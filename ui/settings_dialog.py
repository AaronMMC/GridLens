"""
Settings dialog — three tabs: Claude Profiles, Other Backends, Preferences.

Key fix: previously this file saved to Path(".env") (relative to the
process's current working directory). main_window.py read from
Path(__file__).parent.parent / ".env" — a totally different file when
the exe's cwd isn't the exe's own folder. Result: every save was silently
lost. Now all I/O goes through core.config which uses core.paths to find
the canonical location.
"""
import json
import os
import webbrowser

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QMessageBox, QPushButton,
    QRadioButton, QTabWidget, QVBoxLayout, QWidget,
)

from core.config import load_config, save_config
from core.backends.claude_backend import test_key as test_claude_key
from core.backends.groq_backend import test_key as test_groq_key


class _ProfileEditDialog(QDialog):
    def __init__(self, parent=None, profile: dict = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Profile" if profile else "Add Claude Profile")
        self.setMinimumWidth(440)
        self._result = None
        self._build(profile or {})

    def _build(self, profile: dict):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # --- Name ---
        layout.addWidget(QLabel("Profile name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Personal, Work, Backup")
        self.name_edit.setText(profile.get("name", ""))
        layout.addWidget(self.name_edit)

        # --- API Key ---
        layout.addWidget(QLabel("Anthropic API key:"))
        row = QHBoxLayout()
        self.key_edit = QLineEdit()
        self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_edit.setPlaceholderText("sk-ant-...")
        self.key_edit.setText(profile.get("key", ""))
        row.addWidget(self.key_edit)
        show_btn = QPushButton("Show")
        show_btn.setCheckable(True)
        show_btn.setFixedWidth(54)
        show_btn.toggled.connect(
            lambda on: self.key_edit.setEchoMode(
                QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password
            )
        )
        row.addWidget(show_btn)
        layout.addLayout(row)

        # Inline "Test key" feedback
        test_row = QHBoxLayout()
        test_btn = QPushButton("Test key")
        test_btn.clicked.connect(self._test_key)
        self._claude_status = QLabel("")
        test_row.addWidget(test_btn)
        test_row.addWidget(self._claude_status, 1)
        layout.addLayout(test_row)

        get_btn = QPushButton("Get / top up key  →  console.anthropic.com")
        get_btn.setProperty("variant", "link")
        get_btn.clicked.connect(lambda: webbrowser.open("https://console.anthropic.com"))
        layout.addWidget(get_btn)

        # --- Model ---
        layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItem("claude-sonnet-4-6  (faster, cheaper)", "claude-sonnet-4-6")
        self.model_combo.addItem("claude-opus-4-6    (best for messy handwriting)", "claude-opus-4-6")
        saved_model = profile.get("model", "claude-sonnet-4-6")
        for i in range(self.model_combo.count()):
            if self.model_combo.itemData(i) == saved_model:
                self.model_combo.setCurrentIndex(i)
                break
        layout.addWidget(self.model_combo)

        # --- Buttons ---
        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save profile")
        save_btn.setProperty("variant", "primary")
        save_btn.clicked.connect(self._on_save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _test_key(self):
        ok, msg = test_claude_key(self.key_edit.text())
        self._claude_status.setText(msg)
        self._claude_status.setProperty("role", "success" if ok else "danger")
        self._claude_status.style().unpolish(self._claude_status)
        self._claude_status.style().polish(self._claude_status)

    def _on_save(self):
        name = self.name_edit.text().strip()
        key = self.key_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing name", "Please enter a name for this profile.")
            return
        self._result = {
            "name": name,
            "key": key,
            "model": self.model_combo.currentData(),
        }
        self.accept()

    @property
    def result(self):
        return self._result


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(580, 500)
        self._cfg = load_config()
        self._profiles = list(self._cfg.get("all_profiles", []))
        self._active_idx = self._cfg.get("active_profile_idx", 0)
        self._build()

    # ------------------------------------------------------------------ build

    def _build(self):
        tabs = QTabWidget()
        tabs.addTab(self._tab_claude(), "Claude Profiles")
        tabs.addTab(self._tab_backends(), "Other Backends")
        tabs.addTab(self._tab_prefs(), "Preferences")

        bottom = QHBoxLayout()
        save_btn = QPushButton("Save & Close")
        save_btn.setProperty("variant", "primary")
        save_btn.clicked.connect(self._on_save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        bottom.addStretch()
        bottom.addWidget(save_btn)
        bottom.addWidget(cancel_btn)

        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.addWidget(tabs)
        root.addSpacing(8)
        root.addLayout(bottom)
        root.setContentsMargins(12, 12, 12, 12)

    # --------------------------------------------------------------- Tab 1: Claude

    def _tab_claude(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(10)

        hint = QLabel(
            "Each profile stores a separate Anthropic API key. "
            "You can switch between profiles at any time from the main window."
        )
        hint.setWordWrap(True)
        hint.setProperty("role", "muted")
        layout.addWidget(hint)

        self._profile_list = QListWidget()
        self._profile_list.setMinimumHeight(130)
        self._refresh_profile_list()
        layout.addWidget(self._profile_list)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("＋ Add profile")
        add_btn.clicked.connect(self._add_profile)
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self._edit_profile)
        del_btn = QPushButton("Delete")
        del_btn.setProperty("variant", "danger")
        del_btn.clicked.connect(self._delete_profile)
        active_btn = QPushButton("Set as active")
        active_btn.clicked.connect(self._set_active)
        for b in (add_btn, edit_btn, del_btn, active_btn):
            btn_row.addWidget(b)
        layout.addLayout(btn_row)
        layout.addStretch()
        return w

    def _refresh_profile_list(self):
        self._profile_list.clear()
        for i, p in enumerate(self._profiles):
            marker = "  ✓ Active" if i == self._active_idx else ""
            self._profile_list.addItem(
                f"{p.get('name', 'Unnamed')}   [{p.get('model', '')}]{marker}"
            )

    def _add_profile(self):
        dlg = _ProfileEditDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.result:
            self._profiles.append(dlg.result)
            if len(self._profiles) == 1:
                self._active_idx = 0
            self._refresh_profile_list()

    def _edit_profile(self):
        idx = self._profile_list.currentRow()
        if idx < 0:
            return
        dlg = _ProfileEditDialog(self, self._profiles[idx])
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.result:
            self._profiles[idx] = dlg.result
            self._refresh_profile_list()

    def _delete_profile(self):
        idx = self._profile_list.currentRow()
        if idx < 0:
            return
        if idx == self._active_idx and len(self._profiles) > 1:
            QMessageBox.warning(
                self, "Cannot delete",
                "Set a different profile as active before deleting this one."
            )
            return
        del self._profiles[idx]
        if self._active_idx >= len(self._profiles):
            self._active_idx = max(0, len(self._profiles) - 1)
        self._refresh_profile_list()

    def _set_active(self):
        idx = self._profile_list.currentRow()
        if idx < 0:
            return
        self._active_idx = idx
        self._refresh_profile_list()

    # --------------------------------------------------------------- Tab 2: Backends

    def _tab_backends(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(14)

        # Groq group
        groq_grp = QGroupBox("Groq (free cloud tier)")
        groq_lay = QVBoxLayout(groq_grp)
        groq_lay.setSpacing(8)

        groq_lay.addWidget(QLabel("Groq API key:"))
        key_row = QHBoxLayout()
        self._groq_key_edit = QLineEdit()
        self._groq_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._groq_key_edit.setPlaceholderText("gsk_...")
        self._groq_key_edit.setText(self._cfg.get("GROQ_API_KEY", ""))
        key_row.addWidget(self._groq_key_edit)
        show_btn = QPushButton("Show")
        show_btn.setCheckable(True)
        show_btn.setFixedWidth(54)
        show_btn.toggled.connect(
            lambda on: self._groq_key_edit.setEchoMode(
                QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password
            )
        )
        key_row.addWidget(show_btn)
        groq_lay.addLayout(key_row)

        # Inline "Test key" feedback
        test_row = QHBoxLayout()
        test_btn = QPushButton("Test key")
        test_btn.clicked.connect(self._test_groq_key)
        self._groq_status = QLabel("")
        test_row.addWidget(test_btn)
        test_row.addWidget(self._groq_status, 1)
        groq_lay.addLayout(test_row)

        groq_link = QPushButton("Get a free key  →  console.groq.com")
        groq_link.setProperty("variant", "link")
        groq_link.clicked.connect(lambda: webbrowser.open("https://console.groq.com"))
        groq_lay.addWidget(groq_link)

        layout.addWidget(groq_grp)

        # Ollama group
        ollama_grp = QGroupBox("Ollama (free, local, offline)")
        ollama_lay = QVBoxLayout(ollama_grp)
        ollama_lay.setSpacing(8)

        ollama_lay.addWidget(QLabel("Ollama base URL:"))
        self._ollama_url_edit = QLineEdit()
        self._ollama_url_edit.setText(self._cfg.get("OLLAMA_BASE_URL", "http://localhost:11434"))
        ollama_lay.addWidget(self._ollama_url_edit)

        test_ollama_row = QHBoxLayout()
        test_ollama_btn = QPushButton("Test connection")
        test_ollama_btn.clicked.connect(self._test_ollama)
        self._ollama_status = QLabel("")
        test_ollama_row.addWidget(test_ollama_btn)
        test_ollama_row.addWidget(self._ollama_status, 1)
        ollama_lay.addLayout(test_ollama_row)

        ollama_link = QPushButton("Download Ollama  →  ollama.com")
        ollama_link.setProperty("variant", "link")
        ollama_link.clicked.connect(lambda: webbrowser.open("https://ollama.com"))
        ollama_lay.addWidget(ollama_link)

        layout.addWidget(ollama_grp)
        layout.addStretch()
        return w

    def _test_groq_key(self):
        ok, msg = test_groq_key(self._groq_key_edit.text())
        self._groq_status.setText(msg)
        self._groq_status.setProperty("role", "success" if ok else "danger")
        self._groq_status.style().unpolish(self._groq_status)
        self._groq_status.style().polish(self._groq_status)

    def _test_ollama(self):
        import requests
        url = self._ollama_url_edit.text().strip() or "http://localhost:11434"
        try:
            r = requests.get(f"{url}/api/tags", timeout=3)
            if r.status_code == 200:
                self._ollama_status.setText("✓ Connected")
                self._ollama_status.setProperty("role", "success")
            else:
                self._ollama_status.setText(f"✗ Status {r.status_code}")
                self._ollama_status.setProperty("role", "danger")
        except Exception as e:
            self._ollama_status.setText(f"✗ Not reachable")
            self._ollama_status.setProperty("role", "danger")
        self._ollama_status.style().unpolish(self._ollama_status)
        self._ollama_status.style().polish(self._ollama_status)

    # --------------------------------------------------------------- Tab 3: Prefs

    def _tab_prefs(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(14)

        fmt_grp = QGroupBox("Default export format")
        fmt_lay = QVBoxLayout(fmt_grp)
        self._csv_radio = QRadioButton("CSV  (opens in Excel, Numbers, Google Sheets)")
        self._excel_radio = QRadioButton("Excel (.xlsx)  (formatted with bold headers)")
        if self._cfg.get("DEFAULT_OUTPUT", "csv") == "excel":
            self._excel_radio.setChecked(True)
        else:
            self._csv_radio.setChecked(True)
        fmt_lay.addWidget(self._csv_radio)
        fmt_lay.addWidget(self._excel_radio)
        layout.addWidget(fmt_grp)

        res_grp = QGroupBox("Image max resolution before upload")
        res_lay = QVBoxLayout(res_grp)
        hint2 = QLabel(
            "Lower = faster upload and less API cost. Higher = better accuracy "
            "for very dense spreadsheets. 2000 px is a good default."
        )
        hint2.setWordWrap(True)
        hint2.setProperty("role", "muted")
        res_lay.addWidget(hint2)
        self._res_combo = QComboBox()
        self._res_combo.addItems(["1500", "2000", "2500"])
        idx = self._res_combo.findText(str(self._cfg.get("MAX_RESOLUTION", "2000")))
        if idx >= 0:
            self._res_combo.setCurrentIndex(idx)
        res_lay.addWidget(self._res_combo)
        layout.addWidget(res_grp)

        misc_grp = QGroupBox("Scan behaviour")
        misc_lay = QVBoxLayout(misc_grp)
        self._auto_fallback_cb = QCheckBox(
            "Auto-fallback — silently switch backends without asking (recommended)"
        )
        self._auto_fallback_cb.setChecked(self._cfg.get("AUTO_FALLBACK", True))
        misc_lay.addWidget(self._auto_fallback_cb)
        layout.addWidget(misc_grp)

        layout.addStretch()
        return w

    # ------------------------------------------------------------------ save

    def _on_save(self):
        try:
            save_config(
                claude_profiles=self._profiles,
                active_claude_profile=self._active_idx,
                groq_api_key=self._groq_key_edit.text(),
                ollama_base_url=self._ollama_url_edit.text(),
                default_output="excel" if self._excel_radio.isChecked() else "csv",
                max_resolution=int(self._res_combo.currentText()),
                auto_fallback=self._auto_fallback_cb.isChecked(),
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self, "Save failed",
                f"Could not save settings:\n{e}\n\n"
                "Make sure the app folder is writable."
            )