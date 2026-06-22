"""
App-wide visual theme. Applied once, at the QApplication level, so every
dialog and widget shares the same look without having to restyle each
one individually.

Palette:
  background  #F5F6FA  light neutral
  surface     #FFFFFF  cards / panels
  border      #DCE0E8
  text        #1F2430
  muted text  #6B7280
  primary     #2D6CDF  (accent: scan/save/primary actions)
  primary-dark#2456B3
  success     #1F9D55
  warning     #C77700
  danger      #D64545
"""

COLOR_BG = "#F5F6FA"
COLOR_SURFACE = "#FFFFFF"
COLOR_BORDER = "#DCE0E8"
COLOR_TEXT = "#1F2430"
COLOR_MUTED = "#6B7280"
COLOR_PRIMARY = "#2D6CDF"
COLOR_PRIMARY_DARK = "#2456B3"
COLOR_SUCCESS = "#1F9D55"
COLOR_WARNING = "#C77700"
COLOR_DANGER = "#D64545"

STYLESHEET = f"""
QWidget {{
    background-color: {COLOR_BG};
    color: {COLOR_TEXT};
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}}

QMainWindow, QDialog {{
    background-color: {COLOR_BG};
}}

QGroupBox {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 10px;
    margin-top: 14px;
    padding: 14px 12px 12px 12px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {COLOR_TEXT};
}}

QLabel {{
    background: transparent;
}}
QLabel[role="muted"] {{
    color: {COLOR_MUTED};
}}
QLabel[role="success"] {{
    color: {COLOR_SUCCESS};
    font-weight: 600;
}}
QLabel[role="warning"] {{
    color: {COLOR_WARNING};
    font-weight: 600;
}}
QLabel[role="danger"] {{
    color: {COLOR_DANGER};
    font-weight: 600;
}}
QLabel[role="heading"] {{
    font-size: 16px;
    font-weight: 700;
}}

QPushButton {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 7px;
    padding: 7px 14px;
    color: {COLOR_TEXT};
}}
QPushButton:hover {{
    border-color: {COLOR_PRIMARY};
}}
QPushButton:pressed {{
    background-color: #ECEFF5;
}}
QPushButton:disabled {{
    color: #A8AEBA;
    background-color: #F0F1F5;
    border-color: {COLOR_BORDER};
}}

QPushButton[variant="primary"] {{
    background-color: {COLOR_PRIMARY};
    border: 1px solid {COLOR_PRIMARY};
    color: white;
    font-weight: 600;
}}
QPushButton[variant="primary"]:hover {{
    background-color: {COLOR_PRIMARY_DARK};
}}
QPushButton[variant="primary"]:disabled {{
    background-color: #AFC4ED;
    border-color: #AFC4ED;
    color: #F0F3FB;
}}

QPushButton[variant="link"] {{
    background: transparent;
    border: none;
    color: {COLOR_PRIMARY};
    text-decoration: underline;
    padding: 2px 0;
    text-align: left;
}}
QPushButton[variant="link"]:hover {{
    color: {COLOR_PRIMARY_DARK};
}}

QPushButton[variant="danger"] {{
    color: {COLOR_DANGER};
}}
QPushButton[variant="danger"]:hover {{
    border-color: {COLOR_DANGER};
}}

QLineEdit, QComboBox, QTextEdit {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 6px 8px;
    selection-background-color: {COLOR_PRIMARY};
}}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{
    border: 1px solid {COLOR_PRIMARY};
}}
QComboBox::drop-down {{
    border: none;
    width: 22px;
}}

QListWidget {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
}}
QListWidget::item {{
    padding: 6px 4px;
}}
QListWidget::item:selected {{
    background-color: #E4ECFC;
    color: {COLOR_TEXT};
}}

QTabWidget::pane {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    background: {COLOR_SURFACE};
    top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 7px;
    border-top-right-radius: 7px;
    color: {COLOR_MUTED};
}}
QTabBar::tab:selected {{
    background: {COLOR_SURFACE};
    color: {COLOR_TEXT};
    font-weight: 600;
    border: 1px solid {COLOR_BORDER};
    border-bottom: none;
}}

QToolBar {{
    background-color: {COLOR_SURFACE};
    border-bottom: 1px solid {COLOR_BORDER};
    padding: 4px;
    spacing: 6px;
}}

QStatusBar {{
    background-color: {COLOR_SURFACE};
    border-top: 1px solid {COLOR_BORDER};
    color: {COLOR_MUTED};
}}

QTableWidget {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    gridline-color: {COLOR_BORDER};
}}
QHeaderView::section {{
    background-color: #EEF1F7;
    color: {COLOR_TEXT};
    padding: 6px;
    border: none;
    border-right: 1px solid {COLOR_BORDER};
    border-bottom: 1px solid {COLOR_BORDER};
    font-weight: 600;
}}

QRadioButton, QCheckBox {{
    spacing: 6px;
    background: transparent;
}}

QSplitter::handle {{
    background-color: {COLOR_BG};
}}

QScrollBar:vertical {{
    background: transparent;
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background: #C7CCD6;
    border-radius: 5px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: #ACB3C0;
}}
"""