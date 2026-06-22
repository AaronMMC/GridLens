import webbrowser

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QFrame
)
from PyQt6.QtCore import Qt


class QuotaPromptDialog(QDialog):
    def __init__(self, active_profile: dict, other_profiles: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Claude quota reached")
        self.setMinimumWidth(440)
        self._choice = "cancel"
        self._build(active_profile, other_profiles)

    def _build(self, active: dict, others: list):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("⚠  Claude quota reached")
        title.setProperty("role", "heading")
        layout.addWidget(title)

        msg = QLabel(
            f"The API key in <b>{active.get('name', 'Unknown')}</b> has hit its "
            f"usage limit for this period.\n\nWhat would you like to do?"
        )
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setWordWrap(True)
        layout.addWidget(msg)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        # Switch to another profile (only shown if alternatives exist)
        if others:
            switch_lbl = QLabel("Switch to a different Claude profile:")
            layout.addWidget(switch_lbl)
            combo_row = QHBoxLayout()
            self._switch_combo = QComboBox()
            for p in others:
                self._switch_combo.addItem(f"{p.get('name', '?')}  [{p.get('model', '')}]")
            combo_row.addWidget(self._switch_combo, 1)
            switch_btn = QPushButton("Use this profile")
            switch_btn.setProperty("variant", "primary")
            switch_btn.clicked.connect(self._on_switch)
            combo_row.addWidget(switch_btn)
            layout.addLayout(combo_row)

        # Add credits
        upgrade_btn = QPushButton("Add credits or upgrade plan  →  console.anthropic.com")
        upgrade_btn.setProperty("variant", "link")
        upgrade_btn.clicked.connect(
            lambda: webbrowser.open("https://console.anthropic.com/settings/billing")
        )
        layout.addWidget(upgrade_btn)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep2)

        # Fallback / cancel
        next_btn = QPushButton("Try next backend (Groq — free)")
        next_btn.clicked.connect(self._on_next)
        cancel_btn = QPushButton("Cancel scan")
        cancel_btn.clicked.connect(self.reject)

        btn_row = QHBoxLayout()
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(next_btn)
        layout.addLayout(btn_row)

    def _on_switch(self):
        self._choice = f"switch:{self._switch_combo.currentIndex()}"
        self.accept()

    def _on_next(self):
        self._choice = "next"
        self.accept()

    @property
    def choice(self) -> str:
        return self._choice