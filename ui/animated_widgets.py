"""
Animated UI components.

WaveHeaderWidget  — full-width animated gradient + flowing wave lines.
                    Uses QTimer + QPainter at ~30 fps.

PulseButton       — QPushButton with an animated glow border overlay.
                    Draws a pulsing ring on top of the QSS-styled base button.
"""
import math

from PyQt6.QtCore import Qt, QTimer, QRect, QPointF
from PyQt6.QtGui import (
    QColor, QLinearGradient, QBrush, QPen,
    QPainter, QPainterPath, QFont
)
from PyQt6.QtWidgets import QPushButton, QWidget


# ─────────────────────────────────────────────────────── WaveHeaderWidget ───

class WaveHeaderWidget(QWidget):
    """
    Full-width animated wave banner — used at the top of every dialog/window.

    Paints three sinusoidal wave lines over an animated gradient background
    that shifts between deep black, navy and dark purple.
    """

    def __init__(self, title: str = "", subtitle: str = "", height: int = 88,
                 parent=None):
        super().__init__(parent)
        self._title = title
        self._subtitle = subtitle
        self._phase = 0.0
        self.setFixedHeight(height)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.setSingleShot(False)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._timer.isActive():
            self._timer.start(33)

    def hideEvent(self, event):
        self._timer.stop()
        super().hideEvent(event)

    def set_title(self, title: str):
        self._title = title
        self.update()

    def set_subtitle(self, sub: str):
        self._subtitle = sub
        self.update()

    def _tick(self):
        self._phase = (self._phase + 0.022) % (2 * math.pi)
        self.update()

    # ---------------------------------------------------------------- paint

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        ph = self._phase

        # ── animated background gradient ──
        t = (math.sin(ph * 0.7) + 1) / 2      # 0.0 → 1.0, slow cycle

        def _lerp(a, b, x): return int(a + (b - a) * x)

        # Stop 0 — oscillates between near-black and dark navy
        r0 = _lerp(8,  18, t);  g0 = _lerp(8, 8, t);   b0 = _lerp(26, 38, t)
        # Stop 0.5 — oscillates between deep purple and mid-blue
        r1 = _lerp(25, 45, t);  g1 = _lerp(10, 15, t); b1 = _lerp(70, 110, t)
        # Stop 1 — oscillates between navy and dark purple
        r2 = _lerp(12, 30, t);  g2 = _lerp(8, 10, t);  b2 = _lerp(40, 80, t)

        grad = QLinearGradient(0, 0, w, h)
        grad.setColorAt(0.0, QColor(r0, g0, b0))
        grad.setColorAt(0.5, QColor(r1, g1, b1))
        grad.setColorAt(1.0, QColor(r2, g2, b2))
        p.fillRect(self.rect(), QBrush(grad))

        # ── three offset wave lines ──
        waves = [
            # (frequency, amplitude, phase_offset, colour)
            (0.011, 11, 0.0,  QColor(107, 47,  217, 90)),   # vivid purple
            (0.017, 6,  1.3,  QColor(37,  99,  235, 65)),   # bright blue
            (0.008, 16, 2.5,  QColor(139, 92,  246, 45)),   # light purple
        ]
        for freq, amp, ph_off, colour in waves:
            pen = QPen(colour)
            pen.setWidth(2)
            p.setPen(pen)
            path = QPainterPath()
            first = True
            for x in range(0, w + 4, 4):
                y = h / 2 + amp * math.sin(freq * x + ph + ph_off)
                pt = QPointF(float(x), float(y))
                if first:
                    path.moveTo(pt); first = False
                else:
                    path.lineTo(pt)
            p.drawPath(path)

        # ── title ──
        if self._title:
            p.setPen(QColor(224, 219, 255))
            f = QFont("Segoe UI", 14, QFont.Weight.Bold)
            p.setFont(f)
            text_h = h if not self._subtitle else h - 24
            p.drawText(
                QRect(18, 0, w - 36, text_h),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                self._title
            )

        # ── subtitle ──
        if self._subtitle:
            p.setPen(QColor(130, 120, 190))
            f2 = QFont("Segoe UI", 9)
            p.setFont(f2)
            p.drawText(
                QRect(18, h - 22, w - 36, 20),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                self._subtitle
            )


# ─────────────────────────────────────────────────────────── PulseButton ───

class PulseButton(QPushButton):
    """
    QPushButton that overlays an animated purple glow ring.
    Uses paintEvent to draw *over* the QSS-styled base button — so all normal
    states (hover, pressed, disabled) still come from the stylesheet.
    """

    def __init__(self, text: str = "", parent=None, glow_color: QColor = None):
        super().__init__(text, parent)
        self._phase = 0.0
        self._glow = glow_color or QColor(107, 47, 217)   # vivid purple default
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.setSingleShot(False)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._timer.isActive():
            self._timer.start(40)

    def hideEvent(self, event):
        self._timer.stop()
        super().hideEvent(event)

    def stop_pulse(self):
        self._timer.stop()

    def start_pulse(self):
        self._timer.start(40)

    def _tick(self):
        self._phase = (self._phase + 0.08) % (2 * math.pi)
        self.update()

    def paintEvent(self, event):
        # 1. Let the stylesheet draw the normal button first
        super().paintEvent(event)

        # 2. Overlay the glow ring (skip when disabled)
        if not self.isEnabled():
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        alpha = int(35 + 45 * (math.sin(self._phase) + 1) / 2)
        c = QColor(self._glow.red(), self._glow.green(), self._glow.blue(), alpha)
        pen = QPen(c)
        pen.setWidth(2)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(2, 2, self.width() - 4, self.height() - 4, 7, 7)
        p.end()