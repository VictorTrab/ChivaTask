"""Servicio de preferencias de usuario usadas por la UI."""

from __future__ import annotations

from application.puertos import AutostartManager, TaskRepository
from shared.ajustes import DEFAULT_SYNC_INTERVAL_SECONDS


ALLOWED_SYNC_INTERVALS = {3600, 21600, 86400}
ALLOWED_NOTIFICATION_MODES = {"solo_nuevos", "resumen_diario", "silencioso"}
ALLOWED_DENSITIES = {"comoda", "compacta"}
ALLOWED_VISUAL_MODES = {"claro", "oscuro", "sistema"}


class SettingsService:
    def __init__(self, repository: TaskRepository, autostart: AutostartManager) -> None:
        self.repository = repository
        self.autostart = autostart

    def sync_interval_seconds(self) -> int:
        value = self.repository.get_setting("sync_interval_seconds", str(DEFAULT_SYNC_INTERVAL_SECONDS))
        interval = int(value or DEFAULT_SYNC_INTERVAL_SECONDS)
        return interval if interval in ALLOWED_SYNC_INTERVALS else DEFAULT_SYNC_INTERVAL_SECONDS

    def set_sync_interval_seconds(self, seconds: int) -> None:
        normalized = int(seconds)
        if normalized not in ALLOWED_SYNC_INTERVALS:
            normalized = DEFAULT_SYNC_INTERVAL_SECONDS
        self.repository.set_setting("sync_interval_seconds", normalized)

    def notification_mode(self) -> str:
        value = self.repository.get_setting("notification_mode", "solo_nuevos") or "solo_nuevos"
        return value if value in ALLOWED_NOTIFICATION_MODES else "solo_nuevos"

    def set_notification_mode(self, mode: str) -> None:
        self.repository.set_setting("notification_mode", mode if mode in ALLOWED_NOTIFICATION_MODES else "solo_nuevos")

    def setting_bool(self, key: str, default: bool) -> bool:
        value = self.repository.get_setting(key, "1" if default else "0")
        return value == "1"

    def set_setting_bool(self, key: str, enabled: bool) -> None:
        self.repository.set_setting(key, enabled)

    def ui_density(self) -> str:
        value = self.repository.get_setting("ui_density", "comoda") or "comoda"
        return value if value in ALLOWED_DENSITIES else "comoda"

    def set_ui_density(self, density: str) -> None:
        self.repository.set_setting("ui_density", density if density in ALLOWED_DENSITIES else "comoda")

    def visual_mode(self) -> str:
        value = self.repository.get_setting("visual_mode", "claro") or "claro"
        return value if value in ALLOWED_VISUAL_MODES else "claro"

    def set_visual_mode(self, mode: str) -> None:
        self.repository.set_setting("visual_mode", mode if mode in ALLOWED_VISUAL_MODES else "claro")

    def onboarding_completed(self) -> bool:
        return self.setting_bool("onboarding_completed", False)

    def set_onboarding_completed(self, completed: bool) -> None:
        self.set_setting_bool("onboarding_completed", completed)

    def autostart_enabled(self) -> bool:
        return self.autostart.enabled()

    def set_autostart(self, enabled: bool) -> None:
        self.autostart.set_enabled(enabled)
