from PyQt6.QtWidgets import (
    QDialog, QTabWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QLabel, QLineEdit, QComboBox, QRadioButton,
    QButtonGroup, QGroupBox, QWidget, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt
import webbrowser
import json
import os
import requests
from dotenv import load_dotenv, set_key
from pathlib import Path


ENV_PATH = Path(".env")
ENV_EXAMPLE_PATH = Path(".env.example")


def load_config() -> dict:
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH)
    else:
        load_dotenv(ENV_EXAMPLE_PATH)
    profiles_raw = os.getenv("CLAUDE_PROFILES", "[]")
    try:
        profiles = json.loads(profiles_raw)
    except json.JSONDecodeError:
        profiles = []
    active = int(os.getenv("ACTIVE_CLAUDE_PROFILE", "0"))
    all_except_active = [p for i, p in enumerate(profiles) if i != active]
    return {
        "active_profile": profiles[active] if 0 <= active < len(profiles) else None,
        "other_profiles": all_except_active,
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY", ""),
        "OLLAMA_BASE_URL": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "DEFAULT_OUTPUT": os.getenv("DEFAULT_OUTPUT", "csv"),
        "MAX_RESOLUTION": int(os.getenv("MAX_RESOLUTION", "2000")),
        "AUTO_FALLBACK": os.getenv("AUTO_FALLBACK", "true").lower() == "true",
    }


def save_config(config: dict):
    data = json.dumps(config.get("claude_profiles", []))
    set_key(ENV_PATH, "CLAUDE_PROFILES", data)
    set_key(ENV_PATH, "ACTIVE_CLAUDE_PROFILE", str(config.get("active_claude_profile", 0)))
    set_key(ENV_PATH, "GROQ_API_KEY", config.get("GROQ_API_KEY", ""))
    set_key(ENV_PATH, "OLLAMA_BASE_URL", config.get("OLLAMA_BASE_URL", "http://localhost:11434"))
    set_key(ENV_PATH, "DEFAULT_OUTPUT", config.get("DEFAULT_OUTPUT", "csv"))
    set_key(ENV_PATH, "MAX_RESOLUTION", str(config.get("MAX_RESOLUTION", "2000")))
    set_key(ENV_PATH, "AUTO_FALLBACK", str(config.get("AUTO_FALLBACK", "true")).lower())


class ProfileEditDialog(QDialog):
    def __init__(self, parent=None, profile=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Profile" if profile else "Add Profile")
        self.setMinimumWidth(400)
        self._result = None
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)
        layout.addWidget(QLabel("API Key:"))
        key_layout = QHBoxLayout()
        self.key_edit = QLineEdit()
        self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        key_layout.addWidget(self.key_edit)
        show_btn = QPushButton("Show")
        show_btn.setCheckable(True)
        show_btn.toggled.connect(
            lambda checked: self.key_edit.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        key_layout.addWidget(show_btn)
        layout.addLayout(key_layout)
        layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["claude-sonnet-4-6", "claude-opus-4-6"])
        layout.addWidget(self.model_combo)
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._on_save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        if profile:
            self.name_edit.setText(profile.get("name", ""))
            self.key_edit.setText(profile.get("key", ""))
            idx = self.model_combo.findText(profile.get("model", "claude-sonnet-4-6"))
            if idx >= 0:
                self.model_combo.setCurrentIndex(idx)

    def _on_save(self):
        self._result = {
            "name": self.name_edit.text().strip(),
            "key": self.key_edit.text().strip(),
            "model": self.model_combo.currentText(),
        }
        self.accept()

    @property
    def result(self):
        return self._result


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(550, 450)
        self._config = load_config()
        self._claude_profiles_raw = self._load_all_profiles()
        self._active_idx = int(os.getenv("ACTIVE_CLAUDE_PROFILE", "0"))
        self._setup_ui()

    def _load_all_profiles(self):
        profiles_raw = os.getenv("CLAUDE_PROFILES", "[]")
        try:
            return json.loads(profiles_raw)
        except json.JSONDecodeError:
            return []

    def _setup_ui(self):
        tabs = QTabWidget(self)
        claude_tab = self._create_claude_tab()
        backends_tab = self._create_backends_tab()
        prefs_tab = self._create_prefs_tab()
        tabs.addTab(claude_tab, "Claude Profiles")
        tabs.addTab(backends_tab, "Other Backends")
        tabs.addTab(prefs_tab, "Preferences")
        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save & Close")
        save_btn.clicked.connect(self._on_save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _create_claude_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        self.profile_list = QListWidget()
        self._refresh_profile_list()
        layout.addWidget(QLabel("Saved Profiles:"))
        layout.addWidget(self.profile_list)
        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_profile)
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self._edit_profile)
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._delete_profile)
        set_active_btn = QPushButton("Set Active")
        set_active_btn.clicked.connect(self._set_active)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(edit_btn)
        btn_row.addWidget(delete_btn)
        btn_row.addWidget(set_active_btn)
        layout.addLayout(btn_row)
        link_btn = QPushButton("Get or top up an API key → console.anthropic.com")
        link_btn.clicked.connect(lambda: webbrowser.open("https://console.anthropic.com"))
        layout.addWidget(link_btn)
        return w

    def _create_backends_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.addWidget(QLabel("Groq API Key:"))
        key_layout = QHBoxLayout()
        self.groq_key_edit = QLineEdit()
        self.groq_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.groq_key_edit.setText(self._config.get("GROQ_API_KEY", ""))
        key_layout.addWidget(self.groq_key_edit)
        show_btn = QPushButton("Show")
        show_btn.setCheckable(True)
        show_btn.toggled.connect(
            lambda checked: self.groq_key_edit.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        key_layout.addWidget(show_btn)
        layout.addLayout(key_layout)
        groq_link = QPushButton("Get API key → console.groq.com")
        groq_link.clicked.connect(lambda: webbrowser.open("https://console.groq.com"))
        layout.addWidget(groq_link)
        layout.addSpacing(10)
        layout.addWidget(QLabel("Ollama Base URL:"))
        self.ollama_url_edit = QLineEdit()
        self.ollama_url_edit.setText(self._config.get("OLLAMA_BASE_URL", "http://localhost:11434"))
        layout.addWidget(self.ollama_url_edit)
        test_btn = QPushButton("Test Ollama connection")
        test_btn.clicked.connect(self._test_ollama)
        layout.addWidget(test_btn)
        layout.addStretch()
        return w

    def _create_prefs_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        format_group = QGroupBox("Default Output Format")
        format_layout = QVBoxLayout(format_group)
        self.csv_radio = QRadioButton("CSV")
        self.excel_radio = QRadioButton("Excel (.xlsx)")
        if self._config.get("DEFAULT_OUTPUT", "csv") == "excel":
            self.excel_radio.setChecked(True)
        else:
            self.csv_radio.setChecked(True)
        format_layout.addWidget(self.csv_radio)
        format_layout.addWidget(self.excel_radio)
        layout.addWidget(format_group)
        res_group = QGroupBox("Image Max Resolution")
        res_layout = QVBoxLayout(res_group)
        self.res_combo = QComboBox()
        self.res_combo.addItems(["1500", "2000", "2500"])
        current_res = str(self._config.get("MAX_RESOLUTION", "2000"))
        idx = self.res_combo.findText(current_res)
        if idx >= 0:
            self.res_combo.setCurrentIndex(idx)
        res_layout.addWidget(self.res_combo)
        layout.addWidget(res_group)
        self.auto_fallback_cb = QCheckBox("Auto-fallback (skip asking at each step)")
        self.auto_fallback_cb.setChecked(self._config.get("AUTO_FALLBACK", True))
        layout.addWidget(self.auto_fallback_cb)
        layout.addStretch()
        return w

    def _refresh_profile_list(self):
        self.profile_list.clear()
        for i, p in enumerate(self._claude_profiles_raw):
            marker = " [ACTIVE]" if i == self._active_idx else ""
            self.profile_list.addItem(f"{p.get('name', 'Unnamed')} ({p.get('model', '')}){marker}")

    def _add_profile(self):
        dlg = ProfileEditDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.result:
            self._claude_profiles_raw.append(dlg.result)
            self._refresh_profile_list()

    def _edit_profile(self):
        idx = self.profile_list.currentRow()
        if idx < 0:
            return
        dlg = ProfileEditDialog(self, self._claude_profiles_raw[idx])
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.result:
            self._claude_profiles_raw[idx] = dlg.result
            self._refresh_profile_list()

    def _delete_profile(self):
        idx = self.profile_list.currentRow()
        if idx < 0:
            return
        if idx == self._active_idx and len(self._claude_profiles_raw) > 1:
            QMessageBox.warning(self, "Cannot Delete", "Cannot delete the active profile. Set another profile as active first.")
            return
        del self._claude_profiles_raw[idx]
        if self._active_idx >= len(self._claude_profiles_raw):
            self._active_idx = max(0, len(self._claude_profiles_raw) - 1)
        self._refresh_profile_list()

    def _set_active(self):
        idx = self.profile_list.currentRow()
        if idx < 0:
            return
        self._active_idx = idx
        self._refresh_profile_list()

    def _test_ollama(self):
        url = self.ollama_url_edit.text().strip()
        try:
            r = requests.get(f"{url}/api/tags", timeout=3)
            if r.status_code == 200:
                QMessageBox.information(self, "Ollama", "✓ Ollama is running")
            else:
                QMessageBox.warning(self, "Ollama", f"✗ Ollama responded with status {r.status_code}")
        except Exception as e:
            QMessageBox.warning(self, "Ollama", f"✗ Could not reach Ollama: {e}")

    def _on_save(self):
        config_data = {
            "claude_profiles": self._claude_profiles_raw,
            "active_claude_profile": self._active_idx,
            "GROQ_API_KEY": self.groq_key_edit.text().strip(),
            "OLLAMA_BASE_URL": self.ollama_url_edit.text().strip(),
            "DEFAULT_OUTPUT": "excel" if self.excel_radio.isChecked() else "csv",
            "MAX_RESOLUTION": int(self.res_combo.currentText()),
            "AUTO_FALLBACK": self.auto_fallback_cb.isChecked(),
        }
        save_config(config_data)
        self.accept()