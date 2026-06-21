"""Funciones de tiempo usadas por dominio y presentacion."""

from __future__ import annotations

from datetime import datetime, timezone


def now_ts() -> int:
    return int(datetime.now(tz=timezone.utc).timestamp())


def unix_to_local_text(value: int | None) -> str:
    if not value:
        return "Sin fecha"
    return datetime.fromtimestamp(value).strftime("%Y-%m-%d %H:%M")
