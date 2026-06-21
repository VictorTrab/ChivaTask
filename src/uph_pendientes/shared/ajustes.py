"""Constantes y rutas base de configuracion de la app."""

from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "ChivaTask"
APP_ID = "uph_pendientes"
DATA_DIR_NAME = "UPH Pendientes"
BASE_URL = "https://campus.uph.edu.hn"
MOODLE_SERVICE = "moodle_mobile_app"
DEFAULT_SYNC_INTERVAL_SECONDS = 6 * 60 * 60


def data_dir() -> Path:
    root = os.environ.get("LOCALAPPDATA")
    path = Path(root) / DATA_DIR_NAME if root else Path.home() / ".uph_pendientes"
    path.mkdir(parents=True, exist_ok=True)
    return path


def db_path() -> Path:
    return data_dir() / "cache.db"
