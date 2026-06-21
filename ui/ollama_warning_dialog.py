from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit
from PyQt6.QtCore import Qt


class OllamaWarningDialog(QDialog):
    def __init__(self, hw_info: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ollama Hardware Warning")
        self.setMinimumWidth(550)
        self._proceeded = False
        self._setup_ui(hw_info)

    def _setup_ui(self, hw_info: dict):
        layout = QVBoxLayout(self)

        header = QLabel("All cloud backends exhausted — switching to local Ollama")
        header.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        msg = QTextEdit()
        msg.setReadOnly(True)
        msg.setPlainText(hw_info.get("message", "Unable to determine hardware capabilities."))
        msg.setMaximumHeight(150)
        layout.addWidget(msg)

        req_label = QLabel("Minimum requirements for Ollama (Qwen2.5-VL 7B):")
        req_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
        layout.addWidget(req_label)

        req_text = QTextEdit()
        req_text.setReadOnly(True)
        req_text.setPlainText(
            "Recommended: GPU with 8 GB+ VRAM (e.g. RTX 3060, RTX 4060, or better)\n"
            "Marginal: GPU with 4-8 GB VRAM (2-5 min/image with partial CPU offload)\n"
            "GTX 1030 / under 4 GB VRAM: GPU is ignored — runs on CPU only, 5-15 min/image\n"
            "System RAM: 16 GB minimum for CPU mode\n"
            "Storage: ~5 GB free for the model\n"
            "Ollama installed: https://ollama.com\n"
            "Model pulled: ollama pull qwen2.5vl:7b"
        )
        req_text.setMaximumHeight(160)
        layout.addWidget(req_text)

        layout.addSpacing(10)

        proceed_btn = QPushButton("Proceed anyway")
        proceed_btn.clicked.connect(self._on_proceed)
        proceed_btn.setStyleSheet("QPushButton { min-height: 30px; }")

        cancel_btn = QPushButton("Cancel scan")
        cancel_btn.clicked.connect(self.reject)

        layout.addWidget(proceed_btn)
        layout.addWidget(cancel_btn)

    def _on_proceed(self):
        self._proceeded = True
        self.accept()

    @property
    def proceeded(self) -> bool:
        return self._proceeded