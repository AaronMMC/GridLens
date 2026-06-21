from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QComboBox, QHBoxLayout
)
from PyQt6.QtCore import Qt
import webbrowser


class QuotaPromptDialog(QDialog):
    def __init__(self, active_profile: dict, other_profiles: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Claude quota reached")
        self.setMinimumWidth(420)
        self._choice = "cancel"
        self._switch_index = -1
        self._setup_ui(active_profile, other_profiles)

    def _setup_ui(self, active_profile: dict, other_profiles: list[dict]):
        layout = QVBoxLayout(self)

        title = QLabel("⚠ Claude quota reached")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        msg = QLabel(
            f'The API key in "{active_profile.get("name", "Unknown")}" has hit its '
            f"usage limit for this period.\n\nWhat would you like to do?"
        )
        msg.setWordWrap(True)
        layout.addWidget(msg)

        if other_profiles:
            switch_layout = QHBoxLayout()
            self.switch_combo = QComboBox()
            for p in other_profiles:
                self.switch_combo.addItem(f'{p["name"]} ({p.get("model", "")})', p)
            switch_layout.addWidget(self.switch_combo)
            switch_btn = QPushButton("Switch to selected profile")
            switch_btn.clicked.connect(self._on_switch)
            switch_layout.addWidget(switch_btn)
            layout.addLayout(switch_layout)

        upgrade_btn = QPushButton("Add credits / upgrade plan → opens browser")
        upgrade_btn.clicked.connect(lambda: webbrowser.open(
            "https://console.anthropic.com/settings/billing"
        ))
        layout.addWidget(upgrade_btn)

        next_btn = QPushButton("Try next backend (Groq — free)")
        next_btn.clicked.connect(self._on_next)
        layout.addWidget(next_btn)

        cancel_btn = QPushButton("Cancel scan")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

    def _on_switch(self):
        self._choice = f"switch:{self.switch_combo.currentIndex()}"
        self.accept()

    def _on_next(self):
        self._choice = "next"
        self.accept()

    @property
    def choice(self) -> str:
        return self._choice