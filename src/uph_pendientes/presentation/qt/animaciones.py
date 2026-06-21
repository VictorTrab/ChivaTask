"""Animaciones sutiles para feedback visual sin bloquear la UI."""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation
from PySide6.QtWidgets import QWidget


def fade_in(widget: QWidget, duration_ms: int = 160) -> QPropertyAnimation:
    widget.setWindowOpacity(0.0)
    animation = QPropertyAnimation(widget, b"windowOpacity", widget)
    animation.setDuration(duration_ms)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(QEasingCurve.OutCubic)
    animation.start()
    return animation

