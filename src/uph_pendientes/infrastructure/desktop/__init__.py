"""Adapters de escritorio Windows."""

from .autoarranque import WindowsAutostartManager
from .notificador import WindowsDesktopNotifier

__all__ = ["WindowsAutostartManager", "WindowsDesktopNotifier"]
