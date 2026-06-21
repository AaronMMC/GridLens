from PyQt6.QtWidgets import (
    QMainWindow, QToolBar, QStatusBar, QVBoxLayout, QHBoxLayout,
    QWidget, QLabel, QPushButton, QComboBox, QFileDialog,
    QSplitter, QScrollArea, QFrame, QMessageBox, QHBoxLayout,
    QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QDragEnterEvent, QDropEvent, QAction, QMouseEvent
from PyQt6.QtWidgets import QDialog
from pathlib import Path
import json
import os
import shutil
import tempfile
import threading

from ui.preview_widget import PreviewWidget
from ui.settings_dialog import SettingsDialog, load_config
from ui.ollama_warning_dialog import OllamaWarningDialog
from ui.quota_prompt_dialog import QuotaPromptDialog
from ui.first_run_wizard import FirstRunWizard
from core.extractor import extract_table, get_available_backend
from core.backends.ollama_backend import is_ollama_running, check_model_available
from core.exporter import export_csv, export_excel
from core.preprocessor import preprocess_image, pdf_to_images
from core.hardware_check import check_ollama_requirements


class ExtractionWorker(QThread):
    status_update = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, image_bytes, media_type, config):
        super().__init__()
        self.image_bytes = image_bytes
        self.media_type = media_type
        self.config = config
        self._quota_choice = None
        self._ollama_proceeded = False
        self._quota_event = threading.Event()
        self._ollama_event = threading.Event()

    def quota_callback(self, profile, other_profiles):
        self._quota_choice = None
        self.status_update.emit("Claude quota reached — awaiting user choice...")
        self._quota_event.clear()
        self._quota_event.wait()
        return self._quota_choice

    def ollama_hw_callback(self, hw_info):
        self._ollama_proceeded = False
        self.status_update.emit("Ollama hardware check required — awaiting confirmation...")
        self._ollama_event.clear()
        self._ollama_event.wait()
        return self._ollama_proceeded

    def resolve_quota(self, choice):
        self._quota_choice = choice
        self._quota_event.set()

    def resolve_ollama_hw(self, proceed):
        self._ollama_proceeded = proceed
        self._ollama_event.set()

    def run(self):
        try:
            result = extract_table(
                self.image_bytes, self.media_type, self.config,
                status_cb=self.status_update.emit,
                quota_cb=None if self.config.get("AUTO_FALLBACK") else self.quota_callback,
                ollama_hw_cb=None if self.config.get("AUTO_FALLBACK") else self.ollama_hw_callback,
            )
            self.finished.emit(result)
        except RuntimeError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(str(e))


class ImagePreviewLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(400, 300)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            "QLabel { border: 2px dashed #aaa; border-radius: 8px; "
            "background-color: #fafafa; color: #888; font-size: 16px; }"
        )
        self.setText(
            "Click to browse or drop a file here\n\n"
            "Supported: PNG, JPG, PDF"
        )
        self.setWordWrap(True)
        self._main = None

    def set_main(self, main):
        self._main = main

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self._main:
            self._main._on_load_file()

    def set_pixmap(self, pixmap):
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(
                self.size(), Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            super().setPixmap(scaled)
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.setStyleSheet(
                "QLabel { border: 2px solid #ccc; border-radius: 4px; "
                "background-color: white; }"
            )
        else:
            self.clear()
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.setStyleSheet(
                "QLabel { border: 2px dashed #aaa; border-radius: 8px; "
                "background-color: #fafafa; color: #888; font-size: 16px; }"
            )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SpreadsheetScanner")
        self.setMinimumSize(900, 650)
        self.setAcceptDrops(True)

        self._config = self._load_config()
        self._current_image_bytes = None
        self._current_media_type = "image/jpeg"
        self._pdf_pages = []
        self._selected_pdf_page = 0
        self._extracted_data = None
        self._worker = None

        self._setup_ui()
        self._refresh_profile_combo()
        self._update_backend_indicator()
        self._check_backends_on_startup()

    def _load_config(self) -> dict:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=True)
        cfg = load_config()
        active = int(os.getenv("ACTIVE_CLAUDE_PROFILE", "0"))
        profiles = json.loads(os.getenv("CLAUDE_PROFILES", "[]"))
        other = [p for i, p in enumerate(profiles) if i != active]
        return {
            "active_profile": profiles[active] if 0 <= active < len(profiles) else None,
            "other_profiles": other,
            "all_profiles": profiles,
            "active_profile_idx": active,
            "GROQ_API_KEY": os.getenv("GROQ_API_KEY", ""),
            "OLLAMA_BASE_URL": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "DEFAULT_OUTPUT": os.getenv("DEFAULT_OUTPUT", "csv"),
            "MAX_RESOLUTION": int(os.getenv("MAX_RESOLUTION", "2000")),
            "AUTO_FALLBACK": os.getenv("AUTO_FALLBACK", "true").lower() == "true",
        }

    def _refresh_config(self):
        self._config = self._load_config()

    def _get_backend_label(self) -> str:
        backend = get_available_backend(self._config)
        if backend == "claude":
            profile = self._config.get("active_profile", {})
            return f"Claude ({profile.get('name', '?')})"
        if backend == "groq":
            return "Groq (free tier)"
        if backend == "ollama":
            model_ok = check_model_available(
                self._config.get("OLLAMA_BASE_URL", "http://localhost:11434")
            )
            status = "ready" if model_ok else "no model"
            return f"Ollama ({status})"
        return "No backend"

    def _update_backend_indicator(self):
        label = self._get_backend_label()
        self.statusBar().showMessage(f"Backend: {label}")

    def _check_backends_on_startup(self):
        if get_available_backend(self._config):
            self._update_backend_indicator()
            return
        if is_ollama_running(self._config.get("OLLAMA_BASE_URL", "http://localhost:11434")):
            self._update_backend_indicator()
            return
        dlg = FirstRunWizard(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.should_proceed:
            if dlg.groq_key:
                from dotenv import set_key
                env_path = Path(__file__).parent.parent / ".env"
                set_key(str(env_path), "GROQ_API_KEY", dlg.groq_key)
            self._refresh_config()
            self._update_backend_indicator()
            if dlg.should_open_settings:
                self._on_settings()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)
        load_action = QAction("Load File", self)
        load_action.triggered.connect(self._on_load_file)
        toolbar.addAction(load_action)
        drive_action = QAction("Import from Google Drive", self)
        drive_action.triggered.connect(self._on_google_drive_import)
        toolbar.addAction(drive_action)
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self._on_settings)
        toolbar.addAction(settings_action)

        profile_layout = QHBoxLayout()
        profile_layout.addWidget(QLabel("Active profile:"))
        self.profile_combo = QComboBox()
        self.profile_combo.currentIndexChanged.connect(self._on_profile_changed)
        profile_layout.addWidget(self.profile_combo, 1)
        profile_layout.addStretch(2)
        main_layout.addLayout(profile_layout)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self.image_label = ImagePreviewLabel()
        self.image_label.set_main(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        image_container = QWidget()
        image_container_layout = QVBoxLayout(image_container)
        image_container_layout.addWidget(self.image_label)

        self.page_strip = QHBoxLayout()
        self.page_strip_widget = QWidget()
        self.page_strip_widget.setLayout(self.page_strip)
        self.page_strip_widget.hide()
        image_container_layout.addWidget(self.page_strip_widget)
        splitter.addWidget(image_container)

        action_layout = QHBoxLayout()
        self.scan_btn = QPushButton("Scan / Extract")
        self.scan_btn.clicked.connect(self._on_scan)
        self.scan_btn.setEnabled(False)
        self.scan_btn.setStyleSheet("QPushButton { min-height: 32px; font-weight: bold; }")
        action_layout.addWidget(self.scan_btn)

        self.status_label = QLabel("Ready")
        action_layout.addWidget(self.status_label, 1)

        output_layout = QHBoxLayout()
        self.csv_radio = QRadioButton("CSV")
        self.excel_radio = QRadioButton("Excel (.xlsx)")
        self.output_group = QButtonGroup()
        self.output_group.addButton(self.csv_radio)
        self.output_group.addButton(self.excel_radio)
        if self._config.get("DEFAULT_OUTPUT", "csv") == "excel":
            self.excel_radio.setChecked(True)
        else:
            self.csv_radio.setChecked(True)
        output_layout.addWidget(self.csv_radio)
        output_layout.addWidget(self.excel_radio)
        output_layout.addStretch()
        save_btn = QPushButton("Save File")
        save_btn.clicked.connect(self._on_save)
        save_btn.setEnabled(False)
        self.save_btn = save_btn
        output_layout.addWidget(save_btn)
        action_layout.addLayout(output_layout)

        action_widget = QWidget()
        action_widget.setLayout(action_layout)
        main_layout.addWidget(action_widget)

        self.preview = PreviewWidget()
        splitter.addWidget(self.preview)
        splitter.setSizes([300, 300])
        main_layout.addWidget(splitter)

    def _refresh_profile_combo(self):
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        profiles = json.loads(os.getenv("CLAUDE_PROFILES", "[]"))
        active_idx = int(os.getenv("ACTIVE_CLAUDE_PROFILE", "0"))
        for i, p in enumerate(profiles):
            marker = " [active]" if i == active_idx else ""
            self.profile_combo.addItem(f"{p.get('name', 'Unnamed')}{marker}", i)
        if not profiles:
            self.profile_combo.addItem("No Claude profiles — add one in Settings", -1)
        self.profile_combo.setCurrentIndex(active_idx if 0 <= active_idx < len(profiles) else 0)
        self.profile_combo.blockSignals(False)

    def _on_profile_changed(self, idx):
        if idx < 0:
            return
        data = self.profile_combo.itemData(idx)
        if data is not None and data >= 0:
            from dotenv import set_key
            set_key(".env", "ACTIVE_CLAUDE_PROFILE", str(data))
            self._refresh_config()
            self._update_backend_indicator()

    def _on_load_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Spreadsheet Photo or Scan", "",
            "Images & PDFs (*.png *.jpg *.jpeg *.pdf);;Images (*.png *.jpg *.jpeg);;PDF (*.pdf)"
        )
        if path:
            self._load_file(path)

    def _on_google_drive_import(self):
        try:
            from integrations.google_drive import get_drive_service, list_recent_files, download_file
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget
        except ImportError:
            QMessageBox.critical(self, "Error", "Google Drive integration requires google-api-python-client.")
            return
        try:
            service = get_drive_service()
            files = list_recent_files(service)
        except Exception as e:
            QMessageBox.critical(self, "Google Drive Error", f"Could not connect to Google Drive:\n{e}")
            return
        if not files:
            QMessageBox.information(self, "No Files", "No recent images or PDFs found in Google Drive.")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Select a file from Google Drive")
        dlg.setMinimumSize(400, 350)
        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel("Recent files:"))
        lst = QListWidget()
        for f in files:
            lst.addItem(f["name"])
        layout.addWidget(lst)
        btn = QPushButton("Download selected")
        btn.clicked.connect(dlg.accept)
        layout.addWidget(btn)
        if dlg.exec() == QDialog.DialogCode.Accepted and lst.currentRow() >= 0:
            file_info = files[lst.currentRow()]
            tmpdir = tempfile.mkdtemp()
            dest = os.path.join(tmpdir, file_info["name"])
            self.statusBar().showMessage(f"Downloading {file_info['name']}...")
            try:
                download_file(service, file_info["id"], dest)
                self._load_file(dest)
                self.statusBar().showMessage("Downloaded from Google Drive.")
            except Exception as e:
                QMessageBox.critical(self, "Download Error", str(e))

    def _load_file(self, path):
        path = Path(path)
        suffix = path.suffix.lower()
        self._pdf_pages = []
        self._selected_pdf_page = 0

        if suffix == ".pdf":
            try:
                with open(path, "rb") as f:
                    pdf_bytes = f.read()
                self._pdf_pages = pdf_to_images(pdf_bytes)
                if not self._pdf_pages:
                    QMessageBox.warning(self, "PDF Error", "Could not extract pages from PDF.")
                    return
                self._select_pdf_page(0)
                self._show_page_strip()
            except ImportError:
                QMessageBox.critical(self, "Error",
                    "PDF support requires pdf2image and Poppler. Install Poppler and pip install pdf2image.")
                return
        elif suffix in (".png", ".jpg", ".jpeg"):
            with open(path, "rb") as f:
                self._current_image_bytes = f.read()
            self._current_media_type = f"image/{'jpeg' if suffix in ('.jpg', '.jpeg') else 'png'}"
            pixmap = QPixmap(str(path))
            self.image_label.set_pixmap(pixmap)
            self._pdf_pages = []
            self._selected_pdf_page = 0
            self.page_strip_widget.hide()
            self.scan_btn.setEnabled(True)
        else:
            QMessageBox.warning(self, "Unsupported Format", f"Unsupported file format: {suffix}")
            return

    def _select_pdf_page(self, idx):
        if 0 <= idx < len(self._pdf_pages):
            self._selected_pdf_page = idx
            self._current_image_bytes = self._pdf_pages[idx]
            self._current_media_type = "image/jpeg"
            pixmap = QPixmap()
            pixmap.loadFromData(self._current_image_bytes)
            self.image_label.set_pixmap(pixmap)
            self.scan_btn.setEnabled(True)

    def _show_page_strip(self):
        while self.page_strip.count():
            item = self.page_strip.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        layout = self.page_strip
        for i in range(len(self._pdf_pages)):
            btn = QPushButton(f"Page {i + 1}")
            btn.setCheckable(True)
            btn.setFixedSize(80, 30)
            if i == self._selected_pdf_page:
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, idx=i: self._select_pdf_page(idx))
            layout.addWidget(btn)
        layout.addStretch()
        self.page_strip_widget.show()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            accepted = {".png", ".jpg", ".jpeg", ".pdf"}
            if any(Path(u.toLocalFile()).suffix.lower() in accepted for u in urls):
                event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path:
                self._load_file(path)
                break

    def _on_scan(self):
        if not self._current_image_bytes:
            return
        self._refresh_config()
        config = self._config
        backend = get_available_backend(config)
        if not backend:
            QMessageBox.warning(self, "No Backends",
                "No backends available. Open Settings to add an API key "
                "or install Ollama from https://ollama.com")
            return
        self.scan_btn.setEnabled(False)
        self.statusBar().showMessage("Pre-processing image...")
        try:
            max_px = int(os.getenv("MAX_RESOLUTION", "2000"))
        except ValueError:
            max_px = 2000
        processed_bytes, media_type = preprocess_image(self._current_image_bytes, max_px)
        self.statusBar().showMessage("Starting extraction...")
        self._worker = ExtractionWorker(processed_bytes, media_type, config)
        self._worker.status_update.connect(self._on_status_update)
        self._worker.finished.connect(self._on_extraction_finished)
        self._worker.error.connect(self._on_extraction_error)
        self._worker.start()

    def _on_status_update(self, msg):
        self.status_label.setText(msg)
        self.statusBar().showMessage(msg)
        if "Claude quota reached" in msg and self._worker:
            self._handle_quota_prompt()
        if "Ollama hardware check required" in msg and self._worker:
            self._handle_ollama_prompt()

    def _handle_quota_prompt(self):
        profile = self._config.get("active_profile", {})
        others = self._config.get("other_profiles", [])
        dlg = QuotaPromptDialog(profile, others, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._worker.resolve_quota(dlg.choice)
        else:
            self._worker.resolve_quota("cancel")

    def _handle_ollama_prompt(self):
        hw = check_ollama_requirements()
        dlg = OllamaWarningDialog(hw, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._worker.resolve_ollama_hw(dlg.proceeded)
        else:
            self._worker.resolve_ollama_hw(False)

    def _on_extraction_finished(self, data):
        self._extracted_data = data
        self.preview.load_data(data)
        headers_count = len(data.get("headers", []))
        rows_count = len(data.get("rows", []))
        self.status_label.setText(f"Done — {rows_count} rows x {headers_count} columns extracted")
        self.statusBar().showMessage(f"Done — {rows_count} rows x {headers_count} columns extracted")
        self.scan_btn.setEnabled(True)
        self.save_btn.setEnabled(True)

    def _on_extraction_error(self, msg):
        self.status_label.setText(f"Error: {msg}")
        self.statusBar().showMessage(f"Error: {msg}")
        self.scan_btn.setEnabled(True)
        QMessageBox.critical(self, "Extraction Error", msg)

    def _on_save(self):
        data = self.preview.get_data()
        if not data.get("headers") and not data.get("rows"):
            return
        is_excel = self.excel_radio.isChecked()
        ext_filter = "Excel Workbook (*.xlsx)" if is_excel else "CSV Files (*.csv)"
        default_suffix = ".xlsx" if is_excel else ".csv"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Extracted Data", default_suffix, ext_filter
        )
        if not path:
            return
        try:
            if is_excel:
                export_excel(data, path)
            else:
                export_csv(data, path)
            self.statusBar().showMessage(f"Saved to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))

    def _on_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_config()
            self._refresh_profile_combo()
            self._update_backend_indicator()