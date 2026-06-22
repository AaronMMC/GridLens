import threading
import webbrowser

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QGroupBox
)
from PyQt6.QtCore import Qt

from core.backends.ollama_backend import (
    is_ollama_running, check_model_available,
    pull_model, OLLAMA_MODEL, OLLAMA_BASE_URL
)


class FirstRunWizard(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to SpreadsheetScanner")
        self.setMinimumSize(520, 430)
        self._groq_key = ""
        self._proceed = False
        self._open_settings = False
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Welcome to SpreadsheetScanner")
        title.setProperty("role", "heading")
        layout.addWidget(title)

        sub = QLabel(
            "To extract data from photos or PDFs, the app needs at least one AI backend. "
            "Choose either option below — both are free."
        )
        sub.setWordWrap(True)
        sub.setProperty("role", "muted")
        layout.addWidget(sub)

        # ----- Option 1: Ollama -----
        ollama_running = is_ollama_running()
        model_ok = check_model_available()

        ol_grp = QGroupBox("Option 1 — Ollama  (free, runs on your computer, no internet needed)")
        ol_lay = QVBoxLayout(ol_grp)
        ol_lay.setSpacing(8)

        if ollama_running and model_ok:
            ol_lay.addWidget(QLabel("Ollama is running and the model is ready. ✓"))
        elif ollama_running and not model_ok:
            ol_lay.addWidget(QLabel(
                f"Ollama is running but the model '{OLLAMA_MODEL}' isn't downloaded yet.\n"
                "Click below to download it (~5 GB — may take a few minutes)."
            ))
            pull_btn = QPushButton(f"Download model  ({OLLAMA_MODEL})")
            pull_btn.clicked.connect(self._on_pull)
            ol_lay.addWidget(pull_btn)
            skip_btn = QPushButton("Skip — I'll do it later")
            skip_btn.setProperty("variant", "link")
            skip_btn.clicked.connect(self._on_skip_pull)
            ol_lay.addWidget(skip_btn)
            self._ol_status = QLabel("")
            ol_lay.addWidget(self._ol_status)
        else:
            ol_lay.addWidget(QLabel(
                "Ollama was not detected. Install it to run AI models locally."
            ))
            inst_btn = QPushButton("Download Ollama  →  ollama.com")
            inst_btn.setProperty("variant", "link")
            inst_btn.clicked.connect(lambda: webbrowser.open("https://ollama.com"))
            ol_lay.addWidget(inst_btn)
            self._ol_status = QLabel("")
            ol_lay.addWidget(self._ol_status)

        layout.addWidget(ol_grp)

        # ----- Option 2: Groq -----
        gr_grp = QGroupBox("Option 2 — Groq API key  (free cloud tier, faster than Ollama)")
        gr_lay = QVBoxLayout(gr_grp)
        gr_lay.setSpacing(8)

        gr_lay.addWidget(QLabel(
            "Sign up for a free Groq API key and paste it below. "
            "No credit card required."
        ))
        key_row = QHBoxLayout()
        self._groq_input = QLineEdit()
        self._groq_input.setPlaceholderText("gsk_...")
        key_row.addWidget(self._groq_input)
        get_btn = QPushButton("Get free key")
        get_btn.clicked.connect(lambda: webbrowser.open("https://console.groq.com"))
        key_row.addWidget(get_btn)
        gr_lay.addLayout(key_row)
        layout.addWidget(gr_grp)

        # ----- Bottom buttons -----
        btn_row = QHBoxLayout()
        start_btn = QPushButton("Start Scanning")
        start_btn.setProperty("variant", "primary")
        start_btn.clicked.connect(self._on_start)
        settings_btn = QPushButton("Open Full Settings")
        settings_btn.clicked.connect(self._on_settings)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(settings_btn)
        btn_row.addWidget(start_btn)
        layout.addLayout(btn_row)

    def _on_pull(self):
        self._ol_status.setText("Downloading… (may take several minutes)")
        self._ol_status.setProperty("role", "warning")
        self._ol_status.style().unpolish(self._ol_status)
        self._ol_status.style().polish(self._ol_status)

        def pull():
            try:
                pull_model()
                self._ol_status.setText("Downloaded successfully! ✓")
                self._ol_status.setProperty("role", "success")
            except Exception as e:
                self._ol_status.setText(f"Download failed: {e}")
                self._ol_status.setProperty("role", "danger")
            self._ol_status.style().unpolish(self._ol_status)
            self._ol_status.style().polish(self._ol_status)

        threading.Thread(target=pull, daemon=True).start()

    def _on_skip_pull(self):
        self._ol_status.setText("Skipped — you can pull the model later from Settings.")
        self._ol_status.setProperty("role", "muted")
        self._ol_status.style().unpolish(self._ol_status)
        self._ol_status.style().polish(self._ol_status)

    def _on_start(self):
        self._groq_key = self._groq_input.text().strip()
        self._proceed = True
        self.accept()

    def _on_settings(self):
        self._groq_key = self._groq_input.text().strip()
        self._proceed = True
        self._open_settings = True
        self.accept()

    @property
    def groq_key(self) -> str:
        return self._groq_key

    @property
    def should_proceed(self) -> bool:
        return self._proceed

    @property
    def should_open_settings(self) -> bool:
        return self._open_settings