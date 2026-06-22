"""Carga centralizada de iconos SVG locales."""

from __future__ import annotations

from importlib import resources
import re

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer


class IconRegistry:
    TONES = {
        "dark": "#0F3F35",
        "brand": "#1A8B70",
        "muted": "#64748B",
        "light": "#F8FAFC",
        "warning": "#D97706",
        "danger": "#DC2626",
        "info": "#2563EB",
    }
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
        "search": "search.svg",
        "shield": "shield.svg",
        "database": "database.svg",
        "info": "info-circle.svg",
    }

    def __init__(self) -> None:
        self._cache: dict[tuple[str, str], QIcon] = {}

    def icon(self, name: str, tone: str = "dark") -> QIcon:
        key = (name, tone)
        if key not in self._cache:
            self._cache[key] = self._load_tinted_icon(name, tone)
        return self._cache[key]

    def _load_tinted_icon(self, name: str, tone: str) -> QIcon:
        color = self.TONES.get(tone, self.TONES["dark"])
        filename = self.ICONS[name]
        resource = resources.files("resources.icons.tabler").joinpath(filename)
        svg = resource.read_text(encoding="utf-8")
        svg = re.sub(r'stroke="[^"]+"', f'stroke="{color}"', svg)
        renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return QIcon(pixmap)
