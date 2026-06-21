"""Utilidades para redactar secretos en diagnosticos."""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from typing import Any

SENSITIVE_KEYS = {"password", "contrasena", "contraseña", "token", "wstoken", "username", "usuario"}
_PAIR_PATTERN = re.compile(
    r"(?i)\b(password|contrasena|contraseña|token|wstoken|username|usuario)\b\s*([=:])\s*([^&\s,;]+)"
)


def redact_secrets(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: "***"
            if str(key).lower() in SENSITIVE_KEYS
            else redact_secrets(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_secrets(item) for item in value)
    if isinstance(value, str):
        return _PAIR_PATTERN.sub(lambda match: f"{match.group(1)}{match.group(2)}***", value)
    return value


class SecretRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_secrets(record.msg)
        if record.args:
            record.args = redact_secrets(record.args)
        return True
