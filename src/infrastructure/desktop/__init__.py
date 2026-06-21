"""Adapters de escritorio Windows."""

from .autoarranque import WindowsAutostartManager
from .navegador import SafeDesktopNavigator
from .notificador import WindowsDesktopNotifier

__all__ = ["SafeDesktopNavigator", "WindowsAutostartManager", "WindowsDesktopNotifier"]
