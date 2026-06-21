"""Chips de estado para tareas y conexion."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel


class StatusChip(QLabel):
    def __init__(self, text: str, variant: str = "neutral") -> None:
        super().__init__(text)
        self.setObjectName(f"chip-{variant}")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(26)
        self.setMaximumHeight(28)
        self.setMinimumWidth(86)
