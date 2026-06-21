"""Compatibilidad: expone el notificador de escritorio."""

from infrastructure.desktop import WindowsDesktopNotifier

NotificationService = WindowsDesktopNotifier

__all__ = ["NotificationService"]
