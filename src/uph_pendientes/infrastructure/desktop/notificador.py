"""Adapter para notificaciones locales de escritorio."""

from __future__ import annotations

from uph_pendientes.domain.modelos import Task
from uph_pendientes.domain.tiempo import unix_to_local_text


class WindowsDesktopNotifier:
    def notify_changed(self, tasks: list[Task]) -> None:
        if not tasks:
            return
        first = tasks[0]
        extra = "" if len(tasks) == 1 else f" y {len(tasks) - 1} mas"
        self._send("ChivaTask", f"{first.name} ({unix_to_local_text(first.due_at)}){extra}")

    def _send(self, title: str, message: str) -> None:
        try:
            from winotify import Notification

            Notification(app_id="ChivaTask", title=title, msg=message).show()
        except Exception:
            try:
                from plyer import notification

                notification.notify(title=title, message=message, app_name="ChivaTask", timeout=8)
            except Exception:
                pass
