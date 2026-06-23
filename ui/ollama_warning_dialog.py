from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QFrame
)
from ui.animated_widgets import WaveHeaderWidget


class OllamaWarningDialog(QDialog):
    def __init__(self, hw_info: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Local Ollama — hardware check")
        self.setMinimumWidth(560)
        self._proceeded = False
        self._build(hw_info)

    def _build(self, hw):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(WaveHeaderWidget(
            "Local Ollama",
            "All cloud backends exhausted — switching to local inference"
        ))

        content_lay = QVBoxLayout()
        content_lay.setContentsMargins(16, 14, 16, 14)
        content_lay.setSpacing(12)

        # Tier badge
        tier = hw.get("tier", "cpu_only")
        tier_map = {
            "good":     ("GPU meets requirements", "success"),
            "marginal": ("Marginal GPU — slow but should work", "warning"),
            "cpu_only": ("CPU-only mode — expect 5-15 min/image", "warning"),
            "none":     ("Could not detect hardware", "warning"),
        }
        badge_text, badge_role = tier_map.get(tier, tier_map["none"])
        badge = QLabel(badge_text)
        badge.setProperty("role", badge_role)
        content_lay.addWidget(badge)

        hw_box = QTextEdit()
        hw_box.setReadOnly(True)
        hw_box.setPlainText(hw.get("message", "Unable to determine hardware capabilities."))
        hw_box.setMaximumHeight(120)
        content_lay.addWidget(hw_box)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background:#2A2060; max-height:1px; border:none;")
        content_lay.addWidget(sep)

        req_title = QLabel("Requirements for Ollama (Qwen2.5-VL 7B):")
        req_title.setStyleSheet("font-weight:600;")
        content_lay.addWidget(req_title)

        req_box = QTextEdit()
        req_box.setReadOnly(True)
        req_box.setPlainText(
            "Recommended   GPU with 8 GB+ VRAM (RTX 3060 / RTX 4060 or better)\n"
            "Marginal       GPU with 4-8 GB VRAM  (2-5 min/image)\n"
            "GTX 1030 / <4 GB VRAM  ->  GPU ignored, CPU only (5-15 min/image)\n"
            "No GPU  ->  CPU only (5-15 min/image)\n"
            "System RAM  ->  16 GB minimum for CPU mode\n"
            "Storage     ->  ~5 GB free for the model\n\n"
            "Install:  https://ollama.com\n"
            "Model:    ollama pull qwen2.5vl:7b"
        )
        req_box.setMaximumHeight(150)
        content_lay.addWidget(req_box)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel scan")
        cancel_btn.clicked.connect(self.reject)
        proceed_btn = QPushButton("Proceed anyway")
        proceed_btn.setProperty("variant", "primary")
        proceed_btn.clicked.connect(self._on_proceed)
        btn_row.addStretch(); btn_row.addWidget(cancel_btn); btn_row.addWidget(proceed_btn)
        content_lay.addLayout(btn_row)

        root.addLayout(content_lay)

    def _on_proceed(self):
        self._proceeded = True; self.accept()

    @property
    def proceeded(self) -> bool: return self._proceeded