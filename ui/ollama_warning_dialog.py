from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QFrame
)
from PyQt6.QtCore import Qt


class OllamaWarningDialog(QDialog):
    def __init__(self, hw_info: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Local Ollama — hardware check")
        self.setMinimumWidth(560)
        self._proceeded = False
        self._build(hw_info)

    def _build(self, hw: dict):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QLabel("All cloud backends exhausted — switching to local Ollama")
        header.setProperty("role", "heading")
        layout.addWidget(header)

        # Coloured tier badge
        tier = hw.get("tier", "cpu_only")
        tier_labels = {
            "good":     ("✓  Your GPU meets the requirements", "success"),
            "marginal": ("⚠  Marginal GPU — slow but should work", "warning"),
            "cpu_only": ("⚠  CPU-only mode — expect 5–15 min/image", "warning"),
            "none":     ("⚠  Could not detect hardware", "warning"),
        }
        badge_text, badge_role = tier_labels.get(tier, tier_labels["none"])
        badge = QLabel(badge_text)
        badge.setProperty("role", badge_role)
        layout.addWidget(badge)

        # Hardware details box
        hw_box = QTextEdit()
        hw_box.setReadOnly(True)
        hw_box.setPlainText(hw.get("message", "Unable to determine hardware capabilities."))
        hw_box.setMaximumHeight(130)
        layout.addWidget(hw_box)

        # Requirements reference
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        req_title = QLabel("Requirements for Ollama (Qwen2.5-VL 7B):")
        req_title.setStyleSheet("font-weight: 600;")
        layout.addWidget(req_title)

        req_box = QTextEdit()
        req_box.setReadOnly(True)
        req_box.setPlainText(
            "Recommended  →  GPU with 8 GB+ VRAM (RTX 3060 / RTX 4060 or better)\n"
            "Marginal      →  GPU with 4–8 GB VRAM  (2–5 min/image, partial CPU offload)\n"
            "GTX 1030 / <4 GB VRAM  →  GPU ignored, runs on CPU only (5–15 min/image)\n"
            "No GPU  →  CPU-only (5–15 min/image)\n"
            "System RAM  →  16 GB minimum for CPU mode\n"
            "Storage  →  ~5 GB free for the model download\n\n"
            "Ollama must be installed: https://ollama.com\n"
            "Model must be pulled: ollama pull qwen2.5vl:7b"
        )
        req_box.setMaximumHeight(155)
        layout.addWidget(req_box)

        # Buttons
        btn_row = QHBoxLayout()
        proceed_btn = QPushButton("Proceed anyway")
        proceed_btn.setProperty("variant", "primary")
        proceed_btn.clicked.connect(self._on_proceed)

        cancel_btn = QPushButton("Cancel scan")
        cancel_btn.clicked.connect(self.reject)

        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(proceed_btn)
        layout.addLayout(btn_row)

    def _on_proceed(self):
        self._proceeded = True
        self.accept()

    @property
    def proceeded(self) -> bool:
        return self._proceeded