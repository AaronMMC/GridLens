"""
Settings — single scrollable page, no tabs.

Layout (top to bottom):
  WaveHeaderWidget
  Section: AI Backends  (Claude · Groq · Ollama)
  Section: Custom Providers
  Section: Preferences
  Save / Cancel bar
"""
import json
import webbrowser

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFrame, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QMessageBox,
    QPushButton, QRadioButton, QScrollArea, QVBoxLayout, QWidget,
)

from core.config import load_config, save_config
from core.backends.claude_backend import test_key as _test_claude
from core.backends.groq_backend import test_key as _test_groq
from core.backends.gemini_backend import test_key as _test_gemini
from ui.animated_widgets import WaveHeaderWidget


# ── helpers ──────────────────────────────────────────────────────────────────

def _sep() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet("background:#2A2060; max-height:1px; border:none;")
    return f

def _lbl_section(text: str) -> QLabel:
    l = QLabel(text)
    l.setProperty("role", "section")
    l.setContentsMargins(0, 6, 0, 2)
    return l

def _status_lbl() -> QLabel:
    l = QLabel("")
    l.setMinimumWidth(110)
    return l

def _apply_status(lbl: QLabel, ok: bool, msg: str):
    lbl.setText(msg)
    lbl.setProperty("role", "success" if ok else "danger")
    lbl.style().unpolish(lbl); lbl.style().polish(lbl)


# ── profile add/edit popup ────────────────────────────────────────────────────

class _ProfileDialog(QDialog):
    def __init__(self, parent=None, profile: dict = None):
        super().__init__(parent)
        self.setWindowTitle("Edit profile" if profile else "Add Claude profile")
        self.setMinimumWidth(420)
        self._result = None
        self._build(profile or {})

    def _build(self, p):
        lay = QVBoxLayout(self)
        lay.setSpacing(10)

        lay.addWidget(QLabel("Profile name:"))
        self.name = QLineEdit(p.get("name", ""))
        self.name.setPlaceholderText("e.g. Personal, Work, Backup")
        lay.addWidget(self.name)

        lay.addWidget(QLabel("Anthropic API key:"))
        row = QHBoxLayout()
        self.key = QLineEdit(p.get("key", ""))
        self.key.setEchoMode(QLineEdit.EchoMode.Password)
        self.key.setPlaceholderText("sk-ant-...")
        row.addWidget(self.key)
        show = QPushButton("Show"); show.setCheckable(True); show.setFixedWidth(52)
        show.toggled.connect(lambda on: self.key.setEchoMode(
            QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password))
        row.addWidget(show)
        lay.addLayout(row)

        tr = QHBoxLayout()
        tb = QPushButton("Test key"); tb.clicked.connect(self._test)
        self._st = _status_lbl()
        tr.addWidget(tb); tr.addWidget(self._st, 1)
        lay.addLayout(tr)

        link = QPushButton("Get / top up key  ->  console.anthropic.com")
        link.setProperty("variant", "link")
        link.clicked.connect(lambda: webbrowser.open("https://console.anthropic.com"))
        lay.addWidget(link)

        lay.addWidget(QLabel("Model:"))
        self.model = QComboBox()
        self.model.addItem("claude-sonnet-4-6  (faster, cheaper)", "claude-sonnet-4-6")
        self.model.addItem("claude-opus-4-6    (best accuracy)", "claude-opus-4-6")
        saved = p.get("model", "claude-sonnet-4-6")
        for i in range(self.model.count()):
            if self.model.itemData(i) == saved:
                self.model.setCurrentIndex(i); break
        lay.addWidget(self.model)

        btns = QHBoxLayout()
        ok = QPushButton("Save profile"); ok.setProperty("variant", "primary"); ok.clicked.connect(self._save)
        ca = QPushButton("Cancel"); ca.clicked.connect(self.reject)
        btns.addStretch(); btns.addWidget(ok); btns.addWidget(ca)
        lay.addLayout(btns)

    def _test(self):
        ok, msg = _test_claude(self.key.text())
        _apply_status(self._st, ok, msg)

    def _save(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, "Missing name", "Please enter a profile name.")
            return
        self._result = {"name": self.name.text().strip(),
                        "key":  self.key.text().strip(),
                        "model": self.model.currentData()}
        self.accept()

    @property
    def result(self): return self._result


# ── custom provider popup ─────────────────────────────────────────────────────

class _CustomDialog(QDialog):
    def __init__(self, parent=None, provider: dict = None):
        super().__init__(parent)
        self.setWindowTitle("Edit provider" if provider else "Add custom provider")
        self.setMinimumWidth(440)
        self._result = None
        self._build(provider or {})

    def _build(self, p):
        lay = QVBoxLayout(self)
        lay.setSpacing(10)

        hint = QLabel("Store API keys for any OpenAI-compatible endpoint.")
        hint.setProperty("role", "muted"); hint.setWordWrap(True)
        lay.addWidget(hint)

        lay.addWidget(QLabel("Provider name:"))
        self.name = QLineEdit(p.get("name", ""))
        self.name.setPlaceholderText("e.g. OpenAI, Mistral, My Local LLM")
        lay.addWidget(self.name)

        lay.addWidget(QLabel("API key:"))
        row = QHBoxLayout()
        self.key = QLineEdit(p.get("key", ""))
        self.key.setEchoMode(QLineEdit.EchoMode.Password)
        self.key.setPlaceholderText("sk-...")
        row.addWidget(self.key)
        show = QPushButton("Show"); show.setCheckable(True); show.setFixedWidth(52)
        show.toggled.connect(lambda on: self.key.setEchoMode(
            QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password))
        row.addWidget(show)
        lay.addLayout(row)

        lay.addWidget(QLabel("Base URL (optional):"))
        self.url = QLineEdit(p.get("base_url", ""))
        self.url.setPlaceholderText("https://api.openai.com/v1")
        lay.addWidget(self.url)

        lay.addWidget(QLabel("Model name (optional):"))
        self.model = QLineEdit(p.get("model", ""))
        self.model.setPlaceholderText("e.g. gpt-4o, mistral-7b-instruct")
        lay.addWidget(self.model)

        btns = QHBoxLayout()
        ok = QPushButton("Save"); ok.setProperty("variant", "primary"); ok.clicked.connect(self._save)
        ca = QPushButton("Cancel"); ca.clicked.connect(self.reject)
        btns.addStretch(); btns.addWidget(ok); btns.addWidget(ca)
        lay.addLayout(btns)

    def _save(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, "Missing name", "Please enter a provider name.")
            return
        self._result = {"name": self.name.text().strip(),
                        "key":  self.key.text().strip(),
                        "base_url": self.url.text().strip(),
                        "model": self.model.text().strip()}
        self.accept()

    @property
    def result(self): return self._result


# ── main dialog ───────────────────────────────────────────────────────────────

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 660)
        self._cfg = load_config()
        self._profiles = list(self._cfg.get("all_profiles", []))
        self._active_idx = self._cfg.get("active_profile_idx", 0)
        self._custom = list(self._cfg.get("custom_providers", []))
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(WaveHeaderWidget("Settings",
                                        "AI backends  ·  custom providers  ·  preferences"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        c = QWidget()
        cl = QVBoxLayout(c)
        cl.setContentsMargins(16, 14, 16, 14)
        cl.setSpacing(14)

        cl.addWidget(_lbl_section("AI Backends"))
        cl.addWidget(self._build_claude())
        cl.addWidget(self._build_gemini())
        cl.addWidget(self._build_groq())
        cl.addWidget(self._build_ollama())

        cl.addWidget(_lbl_section("Custom Providers"))
        cl.addWidget(self._build_custom())

        cl.addWidget(_lbl_section("Preferences"))
        cl.addWidget(self._build_prefs())

        cl.addStretch()
        scroll.setWidget(c)
        root.addWidget(scroll, 1)

        bar = QWidget()
        bar.setStyleSheet("background:#120E38; border-top:1px solid #2A2060;")
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(16, 10, 16, 10)
        save_btn = QPushButton("Save & Close")
        save_btn.setProperty("variant", "primary")
        save_btn.clicked.connect(self._on_save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        bl.addStretch(); bl.addWidget(cancel_btn); bl.addWidget(save_btn)
        root.addWidget(bar)

    # ── Claude ────────────────────────────────────────────────────────────────

    def _build_claude(self) -> QGroupBox:
        grp = QGroupBox("Claude  (Anthropic — paid, best accuracy)")
        lay = QVBoxLayout(grp); lay.setSpacing(8)

        hint = QLabel("Multiple profiles let you switch between API keys without restarting.")
        hint.setWordWrap(True); hint.setProperty("role", "muted")
        lay.addWidget(hint)

        self._profile_list = QListWidget()
        self._profile_list.setMaximumHeight(115)
        self._refresh_profiles()
        lay.addWidget(self._profile_list)

        br = QHBoxLayout()
        add = QPushButton("+ Add profile"); add.clicked.connect(self._add_profile)
        edit = QPushButton("Edit"); edit.clicked.connect(self._edit_profile)
        delete = QPushButton("Delete"); delete.setProperty("variant", "danger")
        delete.clicked.connect(self._delete_profile)
        active_btn = QPushButton("Set active"); active_btn.clicked.connect(self._set_active)
        for b in (add, edit, delete, active_btn): br.addWidget(b)
        lay.addLayout(br)

        link = QPushButton("Get or top up key  ->  console.anthropic.com")
        link.setProperty("variant", "link")
        link.clicked.connect(lambda: webbrowser.open("https://console.anthropic.com"))
        lay.addWidget(link)
        return grp

    def _refresh_profiles(self):
        self._profile_list.clear()
        for i, p in enumerate(self._profiles):
            tick = "  [active]" if i == self._active_idx else ""
            self._profile_list.addItem(
                f"{p.get('name','Unnamed')}   {p.get('model','')} {tick}")

    def _add_profile(self):
        dlg = _ProfileDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.result:
            self._profiles.append(dlg.result)
            if len(self._profiles) == 1: self._active_idx = 0
            self._refresh_profiles()

    def _edit_profile(self):
        i = self._profile_list.currentRow()
        if i < 0: return
        dlg = _ProfileDialog(self, self._profiles[i])
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.result:
            self._profiles[i] = dlg.result; self._refresh_profiles()

    def _delete_profile(self):
        i = self._profile_list.currentRow()
        if i < 0: return
        if i == self._active_idx and len(self._profiles) > 1:
            QMessageBox.warning(self, "Cannot delete",
                "Set another profile as active first."); return
        del self._profiles[i]
        if self._active_idx >= len(self._profiles):
            self._active_idx = max(0, len(self._profiles) - 1)
        self._refresh_profiles()

    def _set_active(self):
        i = self._profile_list.currentRow()
        if i >= 0: self._active_idx = i; self._refresh_profiles()

    # ── Gemini ────────────────────────────────────────────────────────────────

    def _build_gemini(self) -> QGroupBox:
        grp = QGroupBox("Google Gemini  (Recommended, best free tier)")
        lay = QVBoxLayout(grp); lay.setSpacing(8)

        lay.addWidget(QLabel("API key:"))
        row = QHBoxLayout()
        self._gemini_key = QLineEdit(self._cfg.get("GEMINI_API_KEY", ""))
        self._gemini_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._gemini_key.setPlaceholderText("AIzaSy...")
        row.addWidget(self._gemini_key)
        show = QPushButton("Show"); show.setCheckable(True); show.setFixedWidth(52)
        show.toggled.connect(lambda on: self._gemini_key.setEchoMode(
            QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password))
        row.addWidget(show)
        lay.addLayout(row)

        tr = QHBoxLayout()
        tb = QPushButton("Test key"); tb.clicked.connect(self._test_gemini_ui)
        self._gemini_st = _status_lbl()
        tr.addWidget(tb); tr.addWidget(self._gemini_st, 1)
        lay.addLayout(tr)

        link = QPushButton("Get a free key  ->  aistudio.google.com/app/apikey")
        link.setProperty("variant", "link")
        link.clicked.connect(lambda: webbrowser.open("https://aistudio.google.com/app/apikey"))
        lay.addWidget(link)
        return grp

    def _test_gemini_ui(self):
        ok, msg = _test_gemini(self._gemini_key.text())
        _apply_status(self._gemini_st, ok, msg)

    # ── Groq ──────────────────────────────────────────────────────────────────

    def _build_groq(self) -> QGroupBox:
        grp = QGroupBox("Groq  (free cloud tier — fast, rate-limited)")
        lay = QVBoxLayout(grp); lay.setSpacing(8)

        lay.addWidget(QLabel("API key:"))
        row = QHBoxLayout()
        self._groq_key = QLineEdit(self._cfg.get("GROQ_API_KEY", ""))
        self._groq_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._groq_key.setPlaceholderText("gsk_...")
        row.addWidget(self._groq_key)
        show = QPushButton("Show"); show.setCheckable(True); show.setFixedWidth(52)
        show.toggled.connect(lambda on: self._groq_key.setEchoMode(
            QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password))
        row.addWidget(show)
        lay.addLayout(row)

        tr = QHBoxLayout()
        tb = QPushButton("Test key"); tb.clicked.connect(self._test_groq)
        self._groq_st = _status_lbl()
        tr.addWidget(tb); tr.addWidget(self._groq_st, 1)
        lay.addLayout(tr)

        link = QPushButton("Get a free key  ->  console.groq.com")
        link.setProperty("variant", "link")
        link.clicked.connect(lambda: webbrowser.open("https://console.groq.com"))
        lay.addWidget(link)
        return grp

    def _test_groq(self):
        ok, msg = _test_groq(self._groq_key.text())
        _apply_status(self._groq_st, ok, msg)

    # ── Ollama ────────────────────────────────────────────────────────────────

    def _build_ollama(self) -> QGroupBox:
        grp = QGroupBox("Ollama  (free, local, offline fallback)")
        lay = QVBoxLayout(grp); lay.setSpacing(8)

        lay.addWidget(QLabel("Base URL:"))
        self._ollama_url = QLineEdit(self._cfg.get("OLLAMA_BASE_URL", "http://localhost:11434"))
        lay.addWidget(self._ollama_url)

        tr = QHBoxLayout()
        tb = QPushButton("Test connection"); tb.clicked.connect(self._test_ollama)
        self._ollama_st = _status_lbl()
        tr.addWidget(tb); tr.addWidget(self._ollama_st, 1)
        lay.addLayout(tr)

        link = QPushButton("Download Ollama  ->  ollama.com")
        link.setProperty("variant", "link")
        link.clicked.connect(lambda: webbrowser.open("https://ollama.com"))
        lay.addWidget(link)
        return grp

    def _test_ollama(self):
        import requests
        url = self._ollama_url.text().strip() or "http://localhost:11434"
        try:
            r = requests.get(f"{url}/api/tags", timeout=3)
            ok = r.status_code == 200
            _apply_status(self._ollama_st, ok, "Connected" if ok else f"Status {r.status_code}")
        except Exception:
            _apply_status(self._ollama_st, False, "Not reachable")

    # ── Custom providers ──────────────────────────────────────────────────────

    def _build_custom(self) -> QGroupBox:
        grp = QGroupBox("Other providers  (any OpenAI-compatible API)")
        lay = QVBoxLayout(grp); lay.setSpacing(8)

        note = QLabel(
            "Add keys for OpenAI, Mistral, Together AI, local vLLM, etc. "
            "Keys are saved to your .env file. Custom provider routing coming soon.")
        note.setWordWrap(True); note.setProperty("role", "muted")
        lay.addWidget(note)

        self._custom_list = QListWidget()
        self._custom_list.setMaximumHeight(100)
        self._refresh_custom()
        lay.addWidget(self._custom_list)

        br = QHBoxLayout()
        add = QPushButton("+ Add provider"); add.clicked.connect(self._add_custom)
        edit = QPushButton("Edit"); edit.clicked.connect(self._edit_custom)
        delete = QPushButton("Delete"); delete.setProperty("variant", "danger")
        delete.clicked.connect(self._delete_custom)
        for b in (add, edit, delete): br.addWidget(b)
        br.addStretch()
        lay.addLayout(br)
        return grp

    def _refresh_custom(self):
        self._custom_list.clear()
        for p in self._custom:
            model = f"  [{p['model']}]" if p.get("model") else ""
            self._custom_list.addItem(f"{p.get('name','?')}{model}")

    def _add_custom(self):
        dlg = _CustomDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.result:
            self._custom.append(dlg.result); self._refresh_custom()

    def _edit_custom(self):
        i = self._custom_list.currentRow()
        if i < 0: return
        dlg = _CustomDialog(self, self._custom[i])
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.result:
            self._custom[i] = dlg.result; self._refresh_custom()

    def _delete_custom(self):
        i = self._custom_list.currentRow()
        if i >= 0: del self._custom[i]; self._refresh_custom()

    # ── Preferences ───────────────────────────────────────────────────────────

    def _build_prefs(self) -> QGroupBox:
        grp = QGroupBox("Preferences")
        lay = QVBoxLayout(grp); lay.setSpacing(10)

        lay.addWidget(QLabel("Default export format:"))
        fmt = QHBoxLayout()
        self._csv_radio   = QRadioButton("CSV  (opens in Excel, Numbers, Sheets)")
        self._excel_radio = QRadioButton("Excel (.xlsx)")
        if self._cfg.get("DEFAULT_OUTPUT", "csv") == "excel":
            self._excel_radio.setChecked(True)
        else:
            self._csv_radio.setChecked(True)
        fmt.addWidget(self._csv_radio); fmt.addWidget(self._excel_radio); fmt.addStretch()
        lay.addLayout(fmt)

        lay.addWidget(_sep())

        lay.addWidget(QLabel("Image max resolution before upload:"))
        hint = QLabel("Lower = faster / cheaper.  Higher = better accuracy on dense tables.")
        hint.setProperty("role", "muted")
        lay.addWidget(hint)
        self._res_combo = QComboBox()
        self._res_combo.addItems(["1500", "2000", "2500"])
        idx = self._res_combo.findText(str(self._cfg.get("MAX_RESOLUTION", "2000")))
        if idx >= 0: self._res_combo.setCurrentIndex(idx)
        lay.addWidget(self._res_combo)

        lay.addWidget(_sep())

        self._auto_fb = QCheckBox(
            "Auto-fallback — silently switch backends on quota errors (recommended)")
        self._auto_fb.setChecked(self._cfg.get("AUTO_FALLBACK", True))
        lay.addWidget(self._auto_fb)
        return grp

    # ── save ──────────────────────────────────────────────────────────────────

    def _on_save(self):
        try:
            save_config(
                claude_profiles=self._profiles,
                active_claude_profile=self._active_idx,
                groq_api_key=self._groq_key.text(),
                gemini_api_key=self._gemini_key.text(),
                ollama_base_url=self._ollama_url.text(),
                default_output="excel" if self._excel_radio.isChecked() else "csv",
                max_resolution=int(self._res_combo.currentText()),
                auto_fallback=self._auto_fb.isChecked(),
                custom_providers=self._custom,
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Save failed",
                f"Could not save settings:\n{e}\n\nMake sure the app folder is writable.")