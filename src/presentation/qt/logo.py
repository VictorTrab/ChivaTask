"""Widgets y helpers de marca para ChivaTask."""

from __future__ import annotations

from importlib import resources
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from .tema import APP_DISPLAY_NAME


def logo_path() -> str:
    resource = resources.files("resources.brand").joinpath("chivatask-isotipo.svg")
    with resources.as_file(resource) as path:
        return str(Path(path))


def lockup_path() -> str:
    resource = resources.files("resources.brand").joinpath("chivatask-lockup.svg")
    with resources.as_file(resource) as path:
        return str(Path(path))


def logo_icon() -> QIcon:
    return QIcon(logo_path())


class BrandLockup(QWidget):
    def __init__(self, compact: bool = False, header: bool = False) -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        icon = QLabel()
        size = 38 if compact else 42
        icon.setPixmap(logo_icon().pixmap(size, size))
        name = QLabel(APP_DISPLAY_NAME)
        name.setObjectName("brandTextHeader" if header else "brandText")
        layout.addWidget(icon)
        layout.addWidget(name)
        if not header:
            layout.addStretch(1)
