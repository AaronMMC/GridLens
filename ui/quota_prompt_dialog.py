import webbrowser

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QFrame
)
from ui.animated_widgets import WaveHeaderWidget


class QuotaPromptDialog(QDialog):
    def __init__(self, active_profile: dict, other_profiles: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Claude quota reached")
        self.setMinimumWidth(460)
        self._choice = "cancel"
        self._build(active_profile, other_profiles)

    def _build(self, active, others):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(WaveHeaderWidget(
            "Claude quota reached",
            f"Key in \"{active.get('name','?')}\" has hit its usage limit"
        ))

        cl = QVBoxLayout()
        cl.setContentsMargins(16, 14, 16, 14)
        cl.setSpacing(12)

        msg = QLabel("What would you like to do?")
        msg.setProperty("role", "muted")
        cl.addWidget(msg)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background:#2A2060; max-height:1px; border:none;")

        if others:
            cl.addWidget(QLabel("Switch to a different Claude profile:"))
            row = QHBoxLayout()
            self._switch_combo = QComboBox()
            for p in others:
                self._switch_combo.addItem(f"{p.get('name','?')}  [{p.get('model','')}]")
            row.addWidget(self._switch_combo, 1)
            switch_btn = QPushButton("Use this profile")
            switch_btn.setProperty("variant", "primary")
            switch_btn.clicked.connect(self._on_switch)
            row.addWidget(switch_btn)
            cl.addLayout(row)
            cl.addWidget(sep)

        upgrade_btn = QPushButton("Add credits / upgrade plan  ->  console.anthropic.com")
        upgrade_btn.setProperty("variant", "link")
        upgrade_btn.clicked.connect(
            lambda: webbrowser.open("https://console.anthropic.com/settings/billing"))
        cl.addWidget(upgrade_btn)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("background:#2A2060; max-height:1px; border:none;")
        cl.addWidget(sep2)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel scan"); cancel_btn.clicked.connect(self.reject)
        next_btn = QPushButton("Try next backend (Groq — free)"); next_btn.clicked.connect(self._on_next)
        btn_row.addWidget(cancel_btn); btn_row.addStretch(); btn_row.addWidget(next_btn)
        cl.addLayout(btn_row)

        root.addLayout(cl)

    def _on_switch(self):
        self._choice = f"switch:{self._switch_combo.currentIndex()}"; self.accept()

    def _on_next(self):
        self._choice = "next"; self.accept()

    @property
    def choice(self) -> str: return self._choice