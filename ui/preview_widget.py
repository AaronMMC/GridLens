from PyQt6.QtWidgets import (
    QTableWidget, QHeaderView, QTableWidgetItem, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush


class PreviewWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setStretchLastSection(True)
        self.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked |
            QTableWidget.EditTrigger.SelectedClicked |
            QTableWidget.EditTrigger.EditKeyPressed
        )
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ContiguousSelection)
        self.horizontalHeader().setSectionsMovable(True)

    def load_data(self, data: dict):
        self.clear()
        headers = data.get("headers", [])
        rows = data.get("rows", [])
        if not headers and not rows:
            return
        self.setColumnCount(len(headers))
        self.setRowCount(len(rows))
        self.setHorizontalHeaderLabels(headers)
        orange = QColor(255, 200, 100)
        for ri, row in enumerate(rows):
            for ci, val in enumerate(row):
                text = str(val) if val is not None else ""
                qitem = QTableWidgetItem(text)
                if text == "?":
                    qitem.setBackground(QBrush(orange))
                self.setItem(ri, ci, qitem)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.resizeColumnsToContents()

    def get_data(self) -> dict:
        headers = []
        for ci in range(self.columnCount()):
            hitem = self.horizontalHeaderItem(ci)
            headers.append(hitem.text() if hitem else f"Column{ci + 1}")
        rows = []
        for ri in range(self.rowCount()):
            row = []
            for ci in range(self.columnCount()):
                item = self.item(ri, ci)
                row.append(item.text() if item else "")
            rows.append(row)
        return {"headers": headers, "rows": rows}