"""Adapter de Moodle Web Services usado por los casos de uso."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import requests

from shared.errores import CampusError
from shared.ajustes import BASE_URL, MOODLE_SERVICE


class MoodleCampusGateway:
    def __init__(
        self,
        base_url: str = BASE_URL,
        timeout: tuple[float, float] | float = (5, 30),
        max_workers: int = 4,
        max_response_bytes: int = 2_000_000,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_workers = max_workers
        self.max_response_bytes = max_response_bytes
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

    def submission_statuses(self, token: str, assignment_ids: list[int]) -> dict[int, dict[str, Any]]:
        if not assignment_ids:
            return {}
        workers = max(1, min(self.max_workers, len(assignment_ids)))
        statuses: dict[int, dict[str, Any]] = {}
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(self._submission_status_with_fresh_session, token, assignment_id): assignment_id
                for assignment_id in assignment_ids
            }
            for future in as_completed(futures):
                assignment_id = futures[future]
                statuses[assignment_id] = future.result()
        return statuses

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
        return self._post_json_with_session(self.session, path, data)

    def _submission_status_with_fresh_session(self, token: str, assignment_id: int) -> dict[str, Any]:
        with requests.Session() as session:
            payload = self._call_with_session(session, token, "mod_assign_get_submission_status", assignid=assignment_id)
        return payload if isinstance(payload, dict) else {}

    def _call_with_session(self, session: requests.Session, token: str, function: str, **params: Any) -> Any:
        payload = self._post_json_with_session(
            session,
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

    def _post_json_with_session(self, session: requests.Session, path: str, data: dict[str, Any]) -> Any:
        last_error: requests.RequestException | None = None
        for _attempt in range(2):
            try:
                response = session.post(f"{self.base_url}{path}", data=data, timeout=self.timeout)
                response.raise_for_status()
                self._validate_response(response)
                return response.json()
            except (requests.Timeout, requests.ConnectionError) as exc:
                last_error = exc
                continue
            except requests.RequestException as exc:
                raise CampusError("network", "No se pudo conectar con Moodle.") from exc
            except ValueError as exc:
                raise CampusError("invalid_json", "Moodle devolvio una respuesta invalida.") from exc
        if isinstance(last_error, requests.Timeout):
            raise CampusError("timeout", "Moodle no respondio a tiempo.") from last_error
        raise CampusError("network", "No se pudo conectar con Moodle.") from last_error

    def _validate_response(self, response: requests.Response) -> None:
        content_type = response.headers.get("Content-Type", "").lower()
        if "json" not in content_type:
            raise CampusError("invalid_content_type", "Moodle devolvio un tipo de respuesta inesperado.")
        content_length = response.headers.get("Content-Length")
        if content_length:
            try:
                if int(content_length) > self.max_response_bytes:
                    raise CampusError("response_too_large", "Moodle devolvio una respuesta demasiado grande.")
            except ValueError as exc:
                raise CampusError("invalid_content_length", "Moodle devolvio una respuesta invalida.") from exc
        if len(response.content) > self.max_response_bytes:
            raise CampusError("response_too_large", "Moodle devolvio una respuesta demasiado grande.")
