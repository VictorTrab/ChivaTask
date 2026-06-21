"""Carga centralizada de iconos SVG locales."""

from __future__ import annotations

from importlib import resources
from pathlib import Path

from PySide6.QtGui import QIcon


class IconRegistry:
    ICONS = {
        "home": "home.svg",
        "tasks": "list-check.svg",
        "courses": "book.svg",
        "settings": "settings.svg",
        "refresh": "refresh.svg",
        "external": "external-link.svg",
        "clock": "clock.svg",
        "bell": "bell.svg",
        "calendar_due": "calendar-due.svg",
        "alert": "alert-triangle.svg",
        "check": "check.svg",
        "tray": "school.svg",
        "user": "user-circle.svg",
        "user_switch": "user-switch.svg",
        "logout": "logout.svg",
        "sparkles": "sparkles.svg",
        "moon": "moon.svg",
        "sun": "sun.svg",
    }

    def __init__(self) -> None:
        self._cache: dict[str, QIcon] = {}

    def icon(self, name: str) -> QIcon:
        if name not in self._cache:
            filename = self.ICONS[name]
            package = "resources.icons.tabler"
            resource = resources.files(package).joinpath(filename)
            with resources.as_file(resource) as path:
                self._cache[name] = QIcon(str(Path(path)))
        return self._cache[name]
