"""Pruebas de seguridad para navegacion y credenciales."""

import unittest
from pathlib import Path

from infrastructure.moodle.cliente import MoodleCampusGateway
from infrastructure.desktop.navegador import SafeDesktopNavigator
from infrastructure.security.almacen_credenciales import WindowsCredentialRepository
from shared.redaccion import redact_secrets
from shared.errores import CredentialError


class FakeKeyring:
    def __init__(self, error: BaseException | None = None) -> None:
        self.error = error
        self.deleted = []

    def delete_password(self, service, account):
        if self.error:
            raise self.error
        self.deleted.append((service, account))


class SafeDesktopNavigatorTests(unittest.TestCase):
    def test_only_opens_https_campus_urls(self):
        opened = []
        navigator = SafeDesktopNavigator(browser_open=lambda url: opened.append(url) or True)

        self.assertTrue(navigator.open_url("https://campus.uph.edu.hn/mod/assign/view.php?id=1"))
        self.assertFalse(navigator.open_url("http://campus.uph.edu.hn/mod/assign/view.php?id=1"))
        self.assertFalse(navigator.open_url("https://example.com/mod/assign/view.php?id=1"))
        self.assertFalse(navigator.open_url("file:///C:/Users/User/secret.txt"))

        self.assertEqual(opened, ["https://campus.uph.edu.hn/mod/assign/view.php?id=1"])

    def test_open_folder_uses_injected_folder_opener(self):
        folders = []
        navigator = SafeDesktopNavigator(folder_open=folders.append)

        self.assertTrue(navigator.open_folder(Path("C:/Temp")))

        self.assertEqual(folders, ["C:\\Temp"])


class CredentialDeletionTests(unittest.TestCase):
    def test_delete_raises_credential_error_for_unexpected_backend_failure(self):
        repo = WindowsCredentialRepository("test_service")
        fake = FakeKeyring(RuntimeError("backend down"))
        repo._keyring = lambda: fake  # type: ignore[method-assign]

        with self.assertRaises(CredentialError):
            repo.clear_token()

    def test_clear_all_deletes_each_known_secret(self):
        repo = WindowsCredentialRepository("test_service")
        fake = FakeKeyring()
        repo._keyring = lambda: fake  # type: ignore[method-assign]

        repo.clear_all()

        self.assertEqual(
            fake.deleted,
            [
                ("test_service", "moodle_username"),
                ("test_service", "moodle_password"),
                ("test_service", "moodle_token"),
            ],
        )


class SecretRedactionTests(unittest.TestCase):
    def test_redacts_sensitive_keys_in_dicts_and_messages(self):
        payload = {
            "username": "student@uph.edu.hn",
            "password": "secret",
            "nested": {"wstoken": "abc123"},
            "safe": "value",
        }
        message = "wstoken=abc123 password=secret usuario=student"

        self.assertEqual(
            redact_secrets(payload),
            {"username": "***", "password": "***", "nested": {"wstoken": "***"}, "safe": "value"},
        )
        self.assertEqual(redact_secrets(message), "wstoken=*** password=*** usuario=***")


class FakeResponse:
    def __init__(self, content_type="application/json", content=b"{}", content_length=None) -> None:
        self.headers = {"Content-Type": content_type}
        if content_length is not None:
            self.headers["Content-Length"] = str(content_length)
        self.content = content


class MoodleResponseValidationTests(unittest.TestCase):
    def test_rejects_non_json_and_oversized_moodle_responses(self):
        gateway = MoodleCampusGateway(max_response_bytes=4)

        with self.assertRaisesRegex(Exception, "tipo de respuesta"):
            gateway._validate_response(FakeResponse(content_type="text/html"))

        with self.assertRaisesRegex(Exception, "demasiado grande"):
            gateway._validate_response(FakeResponse(content=b"12345"))


if __name__ == "__main__":
    unittest.main()
