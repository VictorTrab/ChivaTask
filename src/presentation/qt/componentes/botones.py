"""Botones reutilizables con estilo consistente."""

from __future__ import annotations

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton


class PrimaryButton(QPushButton):
    def __init__(self, text: str, icon: QIcon | None = None) -> None:
        super().__init__(icon or QIcon(), text)
        self.setObjectName("primaryButton")
        self.setAccessibleName(text)
        self.setMinimumHeight(42)


class SecondaryButton(QPushButton):
    def __init__(self, text: str, icon: QIcon | None = None) -> None:
        super().__init__(icon or QIcon(), text)
        self.setObjectName("secondaryButton")
        self.setAccessibleName(text)
        self.setMinimumHeight(42)


class IconButton(QPushButton):
    def __init__(self, icon: QIcon, tooltip: str) -> None:
        super().__init__(icon, "")
        self.setObjectName("iconButton")
        self.setToolTip(tooltip)
        self.setAccessibleName(tooltip)
        self.setFixedSize(40, 40)
