"""Compatibilidad: reexporta constantes de configuracion compartida."""

from shared.ajustes import (
    APP_ID,
    APP_NAME,
    BASE_URL,
    DEFAULT_SYNC_INTERVAL_SECONDS,
    MOODLE_SERVICE,
    data_dir,
    db_path,
)

__all__ = [
    "APP_ID",
    "APP_NAME",
    "BASE_URL",
    "DEFAULT_SYNC_INTERVAL_SECONDS",
    "MOODLE_SERVICE",
    "data_dir",
    "db_path",
]
