"""
Main window — Google Drive integration removed in full.
All config I/O now goes through core.config so reads and writes hit the
same file (fixing the "Groq key doesn't stick" bug).
"""
import threading
import os
from pathlib import Path

from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt6.QtGui import (
    QAction, QColor, QDragEnterEvent, QDropEvent,
    QMouseEvent, QPixmap
)
from PyQt6.QtWidgets import (
    QButtonGroup, QComboBox, QDialog, QFileDialog, QFrame,
    QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton,
    QRadioButton, QScrollArea, QSizePolicy, QSplitter, QStatusBar,
    QToolBar, QVBoxLayout, QWidget
)

from core.config import load_config, save_config, set_active_profile
from core.extractor import extract_table, get_available_backend
from core.backends.ollama_backend import is_ollama_running, check_model_available
from core.exporter import export_csv, export_excel
from core.preprocessor import preprocess_image, pdf_to_images
from core.hardware_check import check_ollama_requirements

from ui.preview_widget import PreviewWidget
from ui.settings_dialog import SettingsDialog
from ui.ollama_warning_dialog import OllamaWarningDialog
from ui.quota_prompt_dialog import QuotaPromptDialog
from ui.first_run_wizard import FirstRunWizard


# ──────────────────────────────── background worker ──────────────────────────

class ExtractionWorker(QThread):
    status_update = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    # signals used to ask the main thread to show dialogs, then wait
    quota_needed = pyqtSignal(dict, list)
    ollama_hw_needed = pyqtSignal(dict)

    def __init__(self, image_bytes: bytes, media_type: str, config: dict):
        super().__init__()
        self.image_bytes = image_bytes
        self.media_type = media_type
        self.config = config
        self._quota_choice = "cancel"
        self._ollama_ok = False
        self._quota_event = threading.Event()
        self._ollama_event = threading.Event()

    # Called from this thread, unblocks when main thread calls resolve_*
    def _quota_cb(self, profile, others):
        self._quota_choice = "cancel"
        self._quota_event.clear()
        self.quota_needed.emit(profile, others)
        self._quota_event.wait()
        return self._quota_choice

    def _ollama_hw_cb(self, hw):
        self._ollama_ok = False
        self._ollama_event.clear()
        self.ollama_hw_needed.emit(hw)
        self._ollama_event.wait()
        return self._ollama_ok

    # Called from main thread
    def resolve_quota(self, choice: str):
        self._quota_choice = choice
        self._quota_event.set()

    def resolve_ollama_hw(self, proceed: bool):
        self._ollama_ok = proceed
        self._ollama_event.set()

    def run(self):
        try:
            result = extract_table(
                self.image_bytes,
                self.media_type,
                self.config,
                status_cb=self.status_update.emit,
                quota_cb=None if self.config.get("AUTO_FALLBACK") else self._quota_cb,
                ollama_hw_cb=self._ollama_hw_cb,
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


# ──────────────────────────── click-to-browse image panel ────────────────────

class _DropPanel(QLabel):
    """Accepts drag-drop AND click-to-browse. Acts as the image preview."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(400, 260)
        self.setWordWrap(True)
        self._main_win = None
        self._reset_style()

    def set_main_win(self, w):
        self._main_win = w

    def _reset_style(self):
        self.setText(
            "Drop an image or PDF here\n\n"
            "or click to browse\n\n"
            "Supported: PNG · JPG · PDF"
        )
        self.setStyleSheet(
            "QLabel { border: 2px dashed #C0C6D4; border-radius: 12px; "
            "background-color: #FAFBFD; color: #8B95A6; font-size: 14px; }"
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def load_pixmap(self, pixmap: QPixmap):
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.setPixmap(scaled)
            self.setStyleSheet(
                "QLabel { border: 1px solid #DCE0E8; border-radius: 8px; "
                "background: white; }"
            )
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def clear_image(self):
        self.clear()
        self._reset_style()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self._main_win:
            self._main_win._on_load_file()


# ─────────────────────────────────── main window ─────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SpreadsheetScanner")
        self.setMinimumSize(920, 660)
        self.setAcceptDrops(True)

        self._config: dict = {}
        self._current_image_bytes: bytes | None = None
        self._current_media_type = "image/jpeg"
        self._pdf_pages: list[bytes] = []
        self._selected_pdf_page = 0
        self._extracted_data: dict | None = None
        self._worker: ExtractionWorker | None = None

        self._build_ui()
        self._refresh_config()
        self._refresh_profile_combo()
        self._update_status_bar()
        self._check_backends_on_startup()

    # ──────────────────────────────── config helpers

    def _refresh_config(self):
        self._config = load_config()

    def _get_backend_label(self) -> str:
        b = get_available_backend(self._config)
        if b == "claude":
            name = (self._config.get("active_profile") or {}).get("name", "?")
            return f"Backend: Claude — {name}"
        if b == "groq":
            return "Backend: Groq (free tier)"
        if b == "ollama":
            url = self._config.get("OLLAMA_BASE_URL", "http://localhost:11434")
            model_ok = check_model_available(url)
            return "Backend: Ollama — ready" if model_ok else "Backend: Ollama — model not pulled"
        return "Backend: None configured"

    def _update_status_bar(self):
        self.statusBar().showMessage(self._get_backend_label())

    def _check_backends_on_startup(self):
        if get_available_backend(self._config):
            return
        url = self._config.get("OLLAMA_BASE_URL", "http://localhost:11434")
        if is_ollama_running(url):
            return
        dlg = FirstRunWizard(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.should_proceed:
            if dlg.groq_key:
                save_config(
                    claude_profiles=self._config.get("all_profiles", []),
                    active_claude_profile=self._config.get("active_profile_idx", 0),
                    groq_api_key=dlg.groq_key,
                    ollama_base_url=self._config.get("OLLAMA_BASE_URL", "http://localhost:11434"),
                    default_output=self._config.get("DEFAULT_OUTPUT", "csv"),
                    max_resolution=self._config.get("MAX_RESOLUTION", 2000),
                    auto_fallback=self._config.get("AUTO_FALLBACK", True),
                )
            self._refresh_config()
            self._update_status_bar()
            if dlg.should_open_settings:
                self._on_settings()

    # ──────────────────────────────── UI construction

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Toolbar
        tb = QToolBar()
        tb.setMovable(False)
        tb.setIconSize(QSize(14, 14))
        self.addToolBar(tb)

        load_act = QAction("📂  Load File", self)
        load_act.triggered.connect(self._on_load_file)
        tb.addAction(load_act)
        tb.addSeparator()
        settings_act = QAction("⚙  Settings", self)
        settings_act.triggered.connect(self._on_settings)
        tb.addAction(settings_act)

        # ── Profile row
        profile_bar = QWidget()
        profile_bar.setStyleSheet(
            "background-color: #FFFFFF; border-bottom: 1px solid #DCE0E8;"
        )
        pb_layout = QHBoxLayout(profile_bar)
        pb_layout.setContentsMargins(12, 6, 12, 6)
        pb_layout.addWidget(QLabel("Active Claude profile:"))
        self._profile_combo = QComboBox()
        self._profile_combo.setMinimumWidth(260)
        self._profile_combo.currentIndexChanged.connect(self._on_profile_changed)
        pb_layout.addWidget(self._profile_combo)
        pb_layout.addStretch()
        root.addWidget(profile_bar)

        # ── Main splitter
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top pane: drop panel + optional PDF strip
        top_pane = QWidget()
        top_layout = QVBoxLayout(top_pane)
        top_layout.setContentsMargins(10, 10, 10, 4)
        top_layout.setSpacing(6)

        self._drop_panel = _DropPanel()
        self._drop_panel.set_main_win(self)
        top_layout.addWidget(self._drop_panel)

        self._page_strip_widget = QWidget()
        self._page_strip_layout = QHBoxLayout(self._page_strip_widget)
        self._page_strip_layout.setContentsMargins(0, 0, 0, 0)
        self._page_strip_widget.hide()
        top_layout.addWidget(self._page_strip_widget)

        splitter.addWidget(top_pane)

        # Bottom pane: preview table
        bottom_pane = QWidget()
        bot_layout = QVBoxLayout(bottom_pane)
        bot_layout.setContentsMargins(10, 4, 10, 10)
        bot_layout.setSpacing(6)

        # Scan / status bar
        scan_row = QHBoxLayout()
        self._scan_btn = QPushButton("Scan / Extract")
        self._scan_btn.setProperty("variant", "primary")
        self._scan_btn.setMinimumHeight(36)
        self._scan_btn.setMinimumWidth(160)
        self._scan_btn.setEnabled(False)
        self._scan_btn.clicked.connect(self._on_scan)
        scan_row.addWidget(self._scan_btn)

        self._status_label = QLabel("Load a file to begin")
        self._status_label.setProperty("role", "muted")
        scan_row.addWidget(self._status_label, 1)
        bot_layout.addLayout(scan_row)

        self._preview = PreviewWidget()
        bot_layout.addWidget(self._preview)

        # Export row
        export_row = QHBoxLayout()
        self._csv_radio = QRadioButton("CSV")
        self._excel_radio = QRadioButton("Excel (.xlsx)")
        self._csv_radio.setChecked(True)
        bg = QButtonGroup(self)
        bg.addButton(self._csv_radio)
        bg.addButton(self._excel_radio)
        export_row.addWidget(QLabel("Save as:"))
        export_row.addWidget(self._csv_radio)
        export_row.addWidget(self._excel_radio)
        export_row.addStretch()
        self._save_btn = QPushButton("💾  Save File")
        self._save_btn.setEnabled(False)
        self._save_btn.clicked.connect(self._on_save)
        export_row.addWidget(self._save_btn)
        bot_layout.addLayout(export_row)

        splitter.addWidget(bottom_pane)
        splitter.setSizes([300, 320])
        root.addWidget(splitter, 1)

        self.setStatusBar(QStatusBar())

    # ──────────────────────────────── profile combo

    def _refresh_profile_combo(self):
        self._profile_combo.blockSignals(True)
        self._profile_combo.clear()
        profiles = self._config.get("all_profiles", [])
        active_idx = self._config.get("active_profile_idx", 0)
        for i, p in enumerate(profiles):
            label = p.get("name", "Unnamed")
            model = p.get("model", "")
            suffix = "  ✓" if i == active_idx else ""
            self._profile_combo.addItem(f"{label}  [{model}]{suffix}", i)
        if not profiles:
            self._profile_combo.addItem("No Claude profiles — add one in Settings", -1)
        self._profile_combo.setCurrentIndex(active_idx if 0 <= active_idx < len(profiles) else 0)
        self._profile_combo.blockSignals(False)

    def _on_profile_changed(self, idx: int):
        data = self._profile_combo.itemData(idx)
        if data is not None and data >= 0:
            set_active_profile(data)
            self._refresh_config()
            self._refresh_profile_combo()
            self._update_status_bar()

    # ──────────────────────────────── file loading

    def _on_load_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Spreadsheet Photo or Scan", "",
            "Images & PDFs (*.png *.jpg *.jpeg *.pdf);;"
            "Images (*.png *.jpg *.jpeg);;"
            "PDF (*.pdf)"
        )
        if path:
            self._load_file(path)

    def _load_file(self, path: str):
        p = Path(path)
        suffix = p.suffix.lower()
        self._pdf_pages = []
        self._selected_pdf_page = 0

        if suffix == ".pdf":
            try:
                raw = p.read_bytes()
                self._pdf_pages = pdf_to_images(raw)
                if not self._pdf_pages:
                    QMessageBox.warning(self, "PDF Error", "No pages could be extracted from this PDF.")
                    return
                self._select_pdf_page(0)
                self._show_page_strip()
            except ImportError:
                QMessageBox.critical(self, "Missing dependency",
                    "PDF support requires pdf2image and Poppler.\n"
                    "Install Poppler and run: pip install pdf2image")
        elif suffix in (".png", ".jpg", ".jpeg"):
            self._current_image_bytes = p.read_bytes()
            self._current_media_type = (
                "image/jpeg" if suffix in (".jpg", ".jpeg") else "image/png"
            )
            pixmap = QPixmap(str(p))
            self._drop_panel.load_pixmap(pixmap)
            self._page_strip_widget.hide()
            self._scan_btn.setEnabled(True)
            self._set_status("Image loaded — click Scan / Extract to begin")
        else:
            QMessageBox.warning(self, "Unsupported format", f"Unsupported file type: {suffix}")

    def _select_pdf_page(self, idx: int):
        if 0 <= idx < len(self._pdf_pages):
            self._selected_pdf_page = idx
            self._current_image_bytes = self._pdf_pages[idx]
            self._current_media_type = "image/jpeg"
            px = QPixmap()
            px.loadFromData(self._current_image_bytes)
            self._drop_panel.load_pixmap(px)
            self._scan_btn.setEnabled(True)

    def _show_page_strip(self):
        while self._page_strip_layout.count():
            item = self._page_strip_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for i in range(len(self._pdf_pages)):
            btn = QPushButton(f"Page {i + 1}")
            btn.setCheckable(True)
            btn.setFixedSize(70, 26)
            if i == self._selected_pdf_page:
                btn.setChecked(True)
            btn.clicked.connect(lambda _checked, idx=i: self._select_pdf_page(idx))
            self._page_strip_layout.addWidget(btn)
        self._page_strip_layout.addStretch()
        self._page_strip_widget.show()

    # ──────────────────────────────── drag and drop

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            accepted = {".png", ".jpg", ".jpeg", ".pdf"}
            if any(
                Path(u.toLocalFile()).suffix.lower() in accepted
                for u in event.mimeData().urls()
            ):
                event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path:
                self._load_file(path)
                break

    # ──────────────────────────────── scan

    def _on_scan(self):
        if not self._current_image_bytes:
            return
        self._refresh_config()
        cfg = self._config

        if not get_available_backend(cfg):
            QMessageBox.warning(
                self, "No backends configured",
                "No AI backends are available.\n\n"
                "Open Settings to add a Groq or Claude API key, or install "
                "Ollama from https://ollama.com"
            )
            return

        # Apply current output format preference
        if cfg.get("DEFAULT_OUTPUT", "csv") == "excel":
            self._excel_radio.setChecked(True)
        else:
            self._csv_radio.setChecked(True)

        self._scan_btn.setEnabled(False)
        self._set_status("Pre-processing image…")

        max_px = cfg.get("MAX_RESOLUTION", 2000)
        processed, media_type = preprocess_image(self._current_image_bytes, max_px)

        self._worker = ExtractionWorker(processed, media_type, cfg)
        self._worker.status_update.connect(self._set_status)
        self._worker.finished.connect(self._on_extraction_done)
        self._worker.error.connect(self._on_extraction_error)
        self._worker.quota_needed.connect(self._handle_quota_prompt)
        self._worker.ollama_hw_needed.connect(self._handle_ollama_prompt)
        self._worker.start()

    def _handle_quota_prompt(self, profile: dict, others: list):
        dlg = QuotaPromptDialog(profile, others, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._worker.resolve_quota(dlg.choice)
        else:
            self._worker.resolve_quota("cancel")

    def _handle_ollama_prompt(self, hw: dict):
        dlg = OllamaWarningDialog(hw, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._worker.resolve_ollama_hw(dlg.proceeded)
        else:
            self._worker.resolve_ollama_hw(False)

    def _on_extraction_done(self, data: dict):
        self._extracted_data = data
        self._preview.load_data(data)
        rows = len(data.get("rows", []))
        cols = len(data.get("headers", []))
        msg = f"Done — {rows} rows × {cols} columns extracted"
        self._set_status(msg)
        self.statusBar().showMessage(self._get_backend_label())
        self._scan_btn.setEnabled(True)
        self._save_btn.setEnabled(True)

    def _on_extraction_error(self, msg: str):
        self._set_status(f"Error — see dialog")
        self._scan_btn.setEnabled(True)
        self.statusBar().showMessage(self._get_backend_label())
        QMessageBox.critical(self, "Extraction failed", msg)

    # ──────────────────────────────── save

    def _on_save(self):
        data = self._preview.get_data()
        if not data.get("headers") and not data.get("rows"):
            return
        is_excel = self._excel_radio.isChecked()
        ext_filter = "Excel Workbook (*.xlsx)" if is_excel else "CSV Files (*.csv)"
        default = "extracted.xlsx" if is_excel else "extracted.csv"
        path, _ = QFileDialog.getSaveFileName(self, "Save Extracted Data", default, ext_filter)
        if not path:
            return
        try:
            if is_excel:
                export_excel(data, path)
            else:
                export_csv(data, path)
            self.statusBar().showMessage(f"Saved → {path}")
        except Exception as e:
            QMessageBox.critical(self, "Save failed", str(e))

    # ──────────────────────────────── settings

    def _on_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_config()
            self._refresh_profile_combo()
            self._update_status_bar()

    # ──────────────────────────────── helpers

    def _set_status(self, msg: str):
        self._status_label.setText(msg)
        self.statusBar().showMessage(msg)