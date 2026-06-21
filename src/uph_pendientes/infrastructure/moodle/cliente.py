"""Adapter de Moodle Web Services usado por los casos de uso."""

from __future__ import annotations

from typing import Any

import requests

from uph_pendientes.shared.errores import CampusError
from uph_pendientes.shared.ajustes import BASE_URL, MOODLE_SERVICE


class MoodleCampusGateway:
    def __init__(self, base_url: str = BASE_URL, timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def login(self, username: str, password: str) -> str:
        payload = self._post_json(
            "/login/token.php",
            {
                "username": username,
                "password": password,
                "service": MOODLE_SERVICE,
            },
        )
        token = payload.get("token") if isinstance(payload, dict) else None
        if not token:
            code = str(payload.get("errorcode", "login_failed")) if isinstance(payload, dict) else "login_failed"
            message = str(payload.get("error", "No se pudo iniciar sesion.")) if isinstance(payload, dict) else "No se pudo iniciar sesion."
            raise CampusError(code, message)
        return token

    def site_info(self, token: str) -> dict[str, Any]:
        return self.call(token, "core_webservice_get_site_info")

    def courses(self, token: str, user_id: int) -> list[dict[str, Any]]:
        payload = self.call(token, "core_enrol_get_users_courses", userid=user_id)
        return payload if isinstance(payload, list) else []

    def assignments(self, token: str) -> list[dict[str, Any]]:
        payload = self.call(token, "mod_assign_get_assignments")
        return payload.get("courses", []) if isinstance(payload, dict) else []

    def submission_status(self, token: str, assignment_id: int) -> dict[str, Any]:
        payload = self.call(token, "mod_assign_get_submission_status", assignid=assignment_id)
        return payload if isinstance(payload, dict) else {}

    def call(self, token: str, function: str, **params: Any) -> Any:
        payload = self._post_json(
            "/webservice/rest/server.php",
            {
                "wstoken": token,
                "moodlewsrestformat": "json",
                "wsfunction": function,
                **params,
            },
        )
        if isinstance(payload, dict) and payload.get("exception"):
            raise CampusError(str(payload.get("errorcode", "moodle_error")), str(payload.get("message", "Error de Moodle.")))
        return payload

    def _post_json(self, path: str, data: dict[str, Any]) -> Any:
        try:
            response = self.session.post(f"{self.base_url}{path}", data=data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.Timeout as exc:
            raise CampusError("timeout", "Moodle no respondio a tiempo.") from exc
        except requests.RequestException as exc:
            raise CampusError("network", "No se pudo conectar con Moodle.") from exc
        except ValueError as exc:
            raise CampusError("invalid_json", "Moodle devolvio una respuesta invalida.") from exc
