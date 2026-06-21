from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QGroupBox
)
from PyQt6.QtCore import Qt
import webbrowser
import threading

from core.backends.ollama_backend import (
    is_ollama_running, check_model_available,
    pull_model, OLLAMA_MODEL, OLLAMA_BASE_URL
)


class FirstRunWizard(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to SpreadsheetScanner")
        self.setMinimumSize(520, 400)
        self._groq_key = ""
        self._proceed = False
        self._open_settings = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Welcome to SpreadsheetScanner")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)

        subtitle = QLabel(
            "This app scans spreadsheet photos and converts them to CSV or Excel.\n"
            "You need at least one backend to extract data. Choose an option below."
        )
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        layout.addSpacing(10)

        ollama_running = is_ollama_running()
        model_available = check_model_available()

        ollama_group = QGroupBox("Option 1: Ollama (Free, Local, Offline)")
        ollama_layout = QVBoxLayout(ollama_group)

        if ollama_running and model_available:
            ollama_layout.addWidget(QLabel("Ollama is running and the model is ready to use."))
            self._ollama_status = QLabel("Ready")
            self._ollama_status.setStyleSheet("color: green; font-weight: bold;")
            ollama_layout.addWidget(self._ollama_status)
        elif ollama_running and not model_available:
            ollama_layout.addWidget(QLabel(
                f"Ollama is running but the model '{OLLAMA_MODEL}' is not downloaded yet.\n"
                f"Click below to download (~5 GB). This may take several minutes."
            ))
            pull_btn = QPushButton(f"Download model ({OLLAMA_MODEL})")
            pull_btn.clicked.connect(self._on_pull_model)
            ollama_layout.addWidget(pull_btn)
            skip_pull = QPushButton("Skip — I'll do it manually later")
            skip_pull.clicked.connect(lambda: self._mark_ollama_skip())
            ollama_layout.addWidget(skip_pull)
            self._ollama_status = QLabel("")
            ollama_layout.addWidget(self._ollama_status)
        else:
            ollama_layout.addWidget(QLabel(
                "Ollama is not detected on your system.\n"
                "It runs AI models locally on your machine — no internet needed after setup."
            ))
            install_btn = QPushButton("Download Ollama (opens ollama.com)")
            install_btn.clicked.connect(
                lambda: webbrowser.open("https://ollama.com")
            )
            ollama_layout.addWidget(install_btn)

        layout.addWidget(ollama_group)

        groq_group = QGroupBox("Option 2: Groq API Key (Free Cloud Tier)")
        groq_layout = QVBoxLayout(groq_group)
        groq_layout.addWidget(QLabel(
            "Groq offers a free tier with rate limits. Sign up for an API key."
        ))
        key_layout = QHBoxLayout()
        self._groq_input = QLineEdit()
        self._groq_input.setPlaceholderText("Enter your Groq API key (gsk_...)")
        key_layout.addWidget(self._groq_input)
        get_key_btn = QPushButton("Get key")
        get_key_btn.clicked.connect(
            lambda: webbrowser.open("https://console.groq.com")
        )
        key_layout.addWidget(get_key_btn)
        groq_layout.addLayout(key_layout)
        layout.addWidget(groq_group)

        layout.addSpacing(10)

        btn_layout = QHBoxLayout()
        start_btn = QPushButton("Start Scanning")
        start_btn.setStyleSheet("QPushButton { min-height: 36px; font-weight: bold; }")
        start_btn.clicked.connect(self._on_start)
        btn_layout.addWidget(start_btn)

        settings_btn = QPushButton("Open Full Settings")
        settings_btn.clicked.connect(self._on_settings)
        btn_layout.addWidget(settings_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def _on_pull_model(self):
        self._ollama_status.setText("Downloading model (this may take several minutes)...")
        self._ollama_status.setStyleSheet("color: orange; font-weight: bold;")

        def pull():
            try:
                pull_model()
                self._ollama_status.setText("Model downloaded successfully!")
                self._ollama_status.setStyleSheet("color: green; font-weight: bold;")
            except Exception as e:
                self._ollama_status.setText(f"Download failed: {e}")
                self._ollama_status.setStyleSheet("color: red; font-weight: bold;")

        threading.Thread(target=pull, daemon=True).start()

    def _mark_ollama_skip(self):
        self._ollama_status.setText("Skipped — you can pull the model later from Settings.")
        self._ollama_status.setStyleSheet("color: gray;")

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
