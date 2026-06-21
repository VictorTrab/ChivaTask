"""Adapter para activar o desactivar inicio con Windows."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from shared.ajustes import APP_NAME


class WindowsAutostartManager:
    def enabled(self) -> bool:
        return startup_shortcut().exists()

    def set_enabled(self, enabled: bool) -> None:
        shortcut = startup_shortcut()
        if enabled:
            shortcut.parent.mkdir(parents=True, exist_ok=True)
            shortcut.write_text(startup_command(), encoding="utf-8")
        elif shortcut.exists():
            shortcut.unlink()


def startup_dir() -> Path:
    return Path(os.environ.get("APPDATA", str(Path.home()))) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def startup_shortcut() -> Path:
    return startup_dir() / f"{APP_NAME}.cmd"


def startup_command() -> str:
    target = Path(sys.executable)
    if getattr(sys, "frozen", False):
        return f'@echo off\nstart "" "{target}"\n'
    entrypoint = Path(__file__).resolve().parents[2] / "main.py"
    return f'@echo off\nstart "" "{target}" "{entrypoint}"\n'
