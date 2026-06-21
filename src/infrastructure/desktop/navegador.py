"""Navegacion desktop con validacion de URLs externas."""

from __future__ import annotations

import os
import webbrowser
from collections.abc import Callable
from pathlib import Path
from urllib.parse import urlparse

from shared.ajustes import BASE_URL


class SafeDesktopNavigator:
    def __init__(
        self,
        allowed_hosts: tuple[str, ...] = ("campus.uph.edu.hn",),
        browser_open: Callable[[str], bool] | None = None,
        folder_open: Callable[[str], object] | None = None,
    ) -> None:
        self.allowed_hosts = allowed_hosts
        self.browser_open = browser_open or webbrowser.open
        self.folder_open = folder_open

    def open_campus_home(self) -> bool:
        return self.open_url(BASE_URL)

    def open_url(self, url: str) -> bool:
        if not self.is_allowed_moodle_url(url):
            return False
        return bool(self.browser_open(url))

    def open_folder(self, path: Path) -> bool:
        folder = os.fspath(path)
        if self.folder_open:
            self.folder_open(folder)
            return True
        startfile = getattr(os, "startfile", None)
        if startfile:
            startfile(folder)
            return True
        return bool(self.browser_open(folder))

    def is_allowed_moodle_url(self, url: str) -> bool:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        return parsed.scheme == "https" and host in self.allowed_hosts
