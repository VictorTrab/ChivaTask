"""Modales comunes para confirmaciones."""

from __future__ import annotations

from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout, QWidget

from presentation.qt.animaciones import fade_in


class BaseModal(QDialog):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("baseModal")
        self.setModal(True)
        self.setWindowTitle(title)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(14)

    def showEvent(self, event):
        self._fade = fade_in(self)
        super().showEvent(event)


class ConfirmModal(BaseModal):
    def __init__(self, title: str, message: str, parent: QWidget | None = None) -> None:
        super().__init__(title, parent)
        label = QLabel(message)
        label.setWordWrap(True)
        self.layout.addWidget(label)

