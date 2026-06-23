"""
Dark purple / blue / black gradient palette.
Applied once at the QApplication level in main.py.
"""

# ── Raw colour constants (used by animated_widgets.py too) ──────────────────
BLACK      = "#08081A"
NAVY       = "#0C0C26"
DARK_PRP   = "#120E38"
MID_PRP    = "#1E1650"
PURPLE     = "#6B2FD9"
PURPLE_BR  = "#8B5CF6"
PURPLE_LT  = "#A78BFA"
BLUE       = "#1E3A8A"
BLUE_BR    = "#2563EB"
BLUE_LT    = "#3B82F6"
TEXT       = "#E0DBFF"
MUTED      = "#6B6090"
BORDER     = "#2A2060"
BORDER_BR  = "#4A35A0"
SUCCESS    = "#22C55E"
WARNING    = "#F59E0B"
DANGER     = "#EF4444"

STYLESHEET = f"""
/* ── Global ─────────────────────────────────────────────────────────────── */
QWidget {{
    background-color: {BLACK};
    color: {TEXT};
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}}

QMainWindow, QDialog {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {BLACK}, stop:0.5 {NAVY}, stop:1 {BLACK});
}}

/* ── Group boxes (cards) ────────────────────────────────────────────────── */
QGroupBox {{
    background-color: {DARK_PRP};
    border: 1px solid {BORDER};
    border-radius: 10px;
    margin-top: 16px;
    padding: 16px 14px 14px 14px;
    font-weight: 600;
    color: {TEXT};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
    color: {PURPLE_LT};
    font-size: 12px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}}

/* ── Labels ─────────────────────────────────────────────────────────────── */
QLabel {{
    background: transparent;
    color: {TEXT};
}}
QLabel[role="muted"]   {{ color: {MUTED};     }}
QLabel[role="success"] {{ color: {SUCCESS};   font-weight: 600; }}
QLabel[role="warning"] {{ color: {WARNING};   font-weight: 600; }}
QLabel[role="danger"]  {{ color: {DANGER};    font-weight: 600; }}
QLabel[role="heading"] {{ font-size: 16px;    font-weight: 700; color: {TEXT}; }}
QLabel[role="section"] {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.5px;
    color: {PURPLE_LT};
    text-transform: uppercase;
}}

/* ── Buttons ────────────────────────────────────────────────────────────── */
QPushButton {{
    background-color: {MID_PRP};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 7px 16px;
    color: {TEXT};
}}
QPushButton:hover {{
    background-color: #261C60;
    border-color: {BORDER_BR};
}}
QPushButton:pressed {{
    background-color: {DARK_PRP};
}}
QPushButton:disabled {{
    color: #3A3460;
    background-color: {DARK_PRP};
    border-color: {BORDER};
}}

QPushButton[variant="primary"] {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {PURPLE}, stop:1 {BLUE_BR});
    border: 1px solid {PURPLE};
    color: white;
    font-weight: 700;
}}
QPushButton[variant="primary"]:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {PURPLE_BR}, stop:1 {BLUE_LT});
    border-color: {PURPLE_BR};
}}
QPushButton[variant="primary"]:disabled {{
    background: {DARK_PRP};
    border-color: {BORDER};
    color: #3A3460;
}}

QPushButton[variant="link"] {{
    background: transparent;
    border: none;
    color: {PURPLE_LT};
    text-decoration: underline;
    padding: 2px 0;
    text-align: left;
}}
QPushButton[variant="link"]:hover {{ color: {TEXT}; }}

QPushButton[variant="danger"] {{ color: {DANGER}; }}
QPushButton[variant="danger"]:hover {{ border-color: {DANGER}; }}

/* ── Inputs ─────────────────────────────────────────────────────────────── */
QLineEdit, QTextEdit {{
    background-color: {NAVY};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 7px 10px;
    color: {TEXT};
    selection-background-color: {PURPLE};
}}
QLineEdit:focus, QTextEdit:focus {{
    border-color: {PURPLE};
    background-color: #0F0F30;
}}
QLineEdit::placeholder {{ color: {MUTED}; }}

QComboBox {{
    background-color: {NAVY};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 7px 10px;
    color: {TEXT};
}}
QComboBox:focus {{ border-color: {PURPLE}; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{
    background-color: {DARK_PRP};
    border: 1px solid {BORDER_BR};
    color: {TEXT};
    selection-background-color: {PURPLE};
}}

/* ── Lists ──────────────────────────────────────────────────────────────── */
QListWidget {{
    background-color: {NAVY};
    border: 1px solid {BORDER};
    border-radius: 7px;
    color: {TEXT};
}}
QListWidget::item {{ padding: 7px 6px; border-bottom: 1px solid {BORDER}; }}
QListWidget::item:last {{ border-bottom: none; }}
QListWidget::item:selected {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #3D1A80, stop:1 #1E3A8A);
    color: white;
}}

/* ── Tabs ───────────────────────────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    background: {DARK_PRP};
    top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    padding: 8px 18px;
    margin-right: 2px;
    color: {MUTED};
    border-top-left-radius: 7px;
    border-top-right-radius: 7px;
}}
QTabBar::tab:selected {{
    background: {DARK_PRP};
    color: {TEXT};
    font-weight: 600;
    border: 1px solid {BORDER};
    border-bottom: none;
}}

/* ── Toolbar ────────────────────────────────────────────────────────────── */
QToolBar {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {DARK_PRP}, stop:1 {NAVY});
    border-bottom: 1px solid {BORDER};
    padding: 4px 8px;
    spacing: 4px;
}}
QToolBar QToolButton {{
    background: transparent;
    color: {TEXT};
    border: none;
    border-radius: 6px;
    padding: 5px 10px;
}}
QToolBar QToolButton:hover {{
    background-color: {MID_PRP};
    border: 1px solid {BORDER};
}}

/* ── Status bar ─────────────────────────────────────────────────────────── */
QStatusBar {{
    background: {DARK_PRP};
    border-top: 1px solid {BORDER};
    color: {MUTED};
}}

/* ── Table ──────────────────────────────────────────────────────────────── */
QTableWidget {{
    background-color: {NAVY};
    border: 1px solid {BORDER};
    border-radius: 7px;
    gridline-color: {BORDER};
    color: {TEXT};
    alternate-background-color: #0E0E2A;
}}
QHeaderView::section {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {MID_PRP}, stop:1 {DARK_PRP});
    color: {PURPLE_LT};
    padding: 7px 6px;
    border: none;
    border-right: 1px solid {BORDER};
    border-bottom: 1px solid {BORDER};
    font-weight: 600;
    font-size: 12px;
}}

/* ── Radio / Check ──────────────────────────────────────────────────────── */
QRadioButton, QCheckBox {{
    spacing: 8px;
    background: transparent;
    color: {TEXT};
}}
QRadioButton::indicator, QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 2px solid {BORDER_BR};
    border-radius: 8px;
    background: {NAVY};
}}
QRadioButton::indicator:checked, QCheckBox::indicator:checked {{
    background: {PURPLE};
    border-color: {PURPLE};
}}

/* ── Splitter ───────────────────────────────────────────────────────────── */
QSplitter::handle {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 transparent, stop:0.5 {BORDER}, stop:1 transparent);
    height: 1px;
}}

/* ── Scrollbar ──────────────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BORDER_BR};
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{ background: {PURPLE_BR}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER_BR};
    border-radius: 4px;
    min-width: 24px;
}}

/* ── Scroll area ────────────────────────────────────────────────────────── */
QScrollArea, QScrollArea > QWidget > QWidget {{
    background: transparent;
    border: none;
}}
"""