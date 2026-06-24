import threading
import webbrowser

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QGroupBox, QFrame
)
from PyQt6.QtCore import Qt, QTimer

from core.backends.ollama_backend import (
    is_ollama_running, check_model_available,
    pull_model, OLLAMA_MODEL
)
from ui.animated_widgets import WaveHeaderWidget


class FirstRunWizard(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to SpreadsheetScanner")
        self.setMinimumSize(520, 460)
        self._groq_key   = ""
        self._proceed    = False
        self._open_settings = False
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(WaveHeaderWidget(
            "Welcome to SpreadsheetScanner",
            "Set up an AI backend to get started"
        ))

        content = QFrame()
        content.setStyleSheet("background: transparent;")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(14)

        sub = QLabel(
            "The app needs at least one AI backend to extract data from images. "
            "Both options below are free."
        )
        sub.setWordWrap(True)
        sub.setProperty("role", "muted")
        cl.addWidget(sub)

        # Option 1: Ollama
        ol_running = is_ollama_running()
        model_ok   = check_model_available()

        ol_grp = QGroupBox("Option 1 — Ollama  (free, runs locally, no internet needed)")
        ol_lay = QVBoxLayout(ol_grp); ol_lay.setSpacing(8)

        if ol_running and model_ok:
            ol_lay.addWidget(QLabel("Ollama is running and the model is ready."))
        elif ol_running and not model_ok:
            ol_lay.addWidget(QLabel(
                f"Ollama is running but '{OLLAMA_MODEL}' is not downloaded yet (~5 GB)."))
            pull_btn = QPushButton(f"Download model  ({OLLAMA_MODEL})")
            pull_btn.clicked.connect(self._on_pull)
            ol_lay.addWidget(pull_btn)
            skip_btn = QPushButton("Skip — download later from Settings")
            skip_btn.setProperty("variant", "link")
            skip_btn.clicked.connect(self._on_skip_pull)
            ol_lay.addWidget(skip_btn)
            self._ol_status = QLabel("")
            ol_lay.addWidget(self._ol_status)
        else:
            ol_lay.addWidget(QLabel("Ollama was not detected on this machine."))
            inst_btn = QPushButton("Download Ollama  ->  ollama.com")
            inst_btn.setProperty("variant", "link")
            inst_btn.clicked.connect(lambda: webbrowser.open("https://ollama.com"))
            ol_lay.addWidget(inst_btn)
            self._ol_status = QLabel("")
            ol_lay.addWidget(self._ol_status)

        cl.addWidget(ol_grp)

        # Option 2: Groq
        gr_grp = QGroupBox("Option 2 — Groq API key  (free cloud tier, faster)")
        gr_lay = QVBoxLayout(gr_grp); gr_lay.setSpacing(8)
        gr_lay.addWidget(QLabel("Sign up for a free Groq key — no credit card required."))

        key_row = QHBoxLayout()
        self._groq_input = QLineEdit()
        self._groq_input.setPlaceholderText("gsk_...")
        key_row.addWidget(self._groq_input)
        get_btn = QPushButton("Get free key")
        get_btn.clicked.connect(lambda: webbrowser.open("https://console.groq.com"))
        key_row.addWidget(get_btn)
        gr_lay.addLayout(key_row)
        cl.addWidget(gr_grp)

        # Buttons
        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel"); cancel_btn.clicked.connect(self.reject)
        settings_btn = QPushButton("Open Full Settings"); settings_btn.clicked.connect(self._on_settings)
        start_btn = QPushButton("Start Scanning")
        start_btn.setProperty("variant", "primary"); start_btn.clicked.connect(self._on_start)
        btn_row.addWidget(cancel_btn); btn_row.addStretch()
        btn_row.addWidget(settings_btn); btn_row.addWidget(start_btn)
        cl.addStretch(); cl.addLayout(btn_row)

        root.addWidget(content)

    def _on_pull(self):
        self._ol_status.setText("Downloading... (may take several minutes)")
        self._ol_status.setProperty("role", "warning")
        self._ol_status.style().unpolish(self._ol_status); self._ol_status.style().polish(self._ol_status)
        def pull():
            try:
                pull_model()
                QTimer.singleShot(0, lambda: self._set_dl_status("Downloaded successfully!", "success"))
            except Exception as e:
                QTimer.singleShot(0, lambda e=e: self._set_dl_status(f"Download failed: {e}", "danger"))
        threading.Thread(target=pull, daemon=True).start()

    def _set_dl_status(self, text, role):
        self._ol_status.setText(text)
        self._ol_status.setProperty("role", role)
        self._ol_status.style().unpolish(self._ol_status); self._ol_status.style().polish(self._ol_status)

    def _on_skip_pull(self):
        self._ol_status.setText("Skipped — pull the model later from Settings.")
        self._ol_status.setProperty("role", "muted")
        self._ol_status.style().unpolish(self._ol_status); self._ol_status.style().polish(self._ol_status)

    def _on_start(self):
        self._groq_key = self._groq_input.text().strip()
        self._proceed  = True; self.accept()

    def _on_settings(self):
        self._groq_key      = self._groq_input.text().strip()
        self._proceed       = True
        self._open_settings = True; self.accept()

    @property
    def groq_key(self)          -> str:  return self._groq_key
    @property
    def should_proceed(self)    -> bool: return self._proceed
    @property
    def should_open_settings(self) -> bool: return self._open_settings