import webbrowser
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from ui.animated_widgets import WaveHeaderWidget
from ui.theme import PURPLE_LT, TEXT, NAVY
from core.version import __version__, APP_NAME, APP_AUTHOR

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        self.setMinimumSize(480, 420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        header = WaveHeaderWidget(APP_NAME, f"Version {__version__}")
        lay.addWidget(header)

        # Content area
        content = QFrame()
        content.setStyleSheet(f"background-color: {NAVY};")
        c_lay = QVBoxLayout(content)
        c_lay.setContentsMargins(24, 24, 24, 24)
        c_lay.setSpacing(16)

        desc = QLabel(
            f"<b>{APP_NAME}</b> is an open-source, AI-powered desktop application "
            "designed to seamlessly convert photographs and scanned documents into "
            "structured digital spreadsheets (CSV or Excel).<br><br>"
            "<i>Why was it made?</i><br>"
            "Manual data encoding is incredibly time-consuming and error-prone. "
            "GridLens automates this process using state-of-the-art vision models "
            "(Google Gemini, Anthropic Claude, Groq, and local Ollama) "
            "to save you hours of tedious work.<br><br>"
            "<i>Development Methodology:</i><br>"
            "This application was rapidly prototyped and developed using AI-assisted "
            "engineering methodologies (often referred to as 'vibe coding')."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 13px; line-height: 1.5;")
        c_lay.addWidget(desc)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #2A2060; border: none; max-height: 1px;")
        c_lay.addWidget(sep)

        author_lbl = QLabel(f"Originally created by <b>{APP_AUTHOR}</b>")
        author_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        author_lbl.setStyleSheet(f"color: {PURPLE_LT}; font-size: 14px;")
        c_lay.addWidget(author_lbl)

        # Links
        links_lay = QVBoxLayout()
        links_lay.setSpacing(8)

        def make_link(text, url):
            btn = QPushButton(text)
            btn.setProperty("variant", "link")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda: webbrowser.open(url))
            return btn

        repo_btn = make_link("🔗 GridLens GitHub Repository", "https://github.com/AaronMMC/GridLens.git")
        github_btn = make_link("👤 GitHub: AaronMMC", "https://github.com/AaronMMC")
        linkedin_btn = make_link("💼 LinkedIn: Aaron Miguel Cardenas", "https://www.linkedin.com/in/aaron-miguel-cardenas-193855376")
        upwork_btn = make_link("🟢 Upwork Profile", "https://www.upwork.com/freelancers/~016c40d29425f7c63c?mp_source=share")

        links_lay.addWidget(repo_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        links_lay.addWidget(github_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        links_lay.addWidget(linkedin_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        links_lay.addWidget(upwork_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        c_lay.addLayout(links_lay)
        c_lay.addStretch()

        lay.addWidget(content, 1)

        # Bottom bar
        bot = QFrame()
        bot.setStyleSheet("background-color: #120E38; border-top: 1px solid #2A2060;")
        b_lay = QHBoxLayout(bot)
        b_lay.setContentsMargins(16, 12, 16, 12)
        
        close_btn = QPushButton("Close")
        close_btn.setMinimumWidth(100)
        close_btn.clicked.connect(self.accept)
        
        b_lay.addStretch()
        b_lay.addWidget(close_btn)
        lay.addWidget(bot)
