"""Pruebas del caso de uso de sincronizacion con fakes."""

import unittest

from uph_pendientes.application.caso_uso_sincronizacion import SyncUseCase
from uph_pendientes.domain.modelos import StoredCredentials
from uph_pendientes.infrastructure.persistence import SQLiteTaskRepository
from uph_pendientes.shared.errores import CampusError, MissingCredentialsError


class FakeCredentials:
    def __init__(self, token="valid") -> None:
        self.token = token
        self.saved_token = None
        self.cleared = False

    def has_credentials(self):
        return True

    def load(self):
        if self.token == "missing":
            raise MissingCredentialsError("missing")
        return StoredCredentials("user", "pass", self.token)

    def save_credentials(self, username, password):
        pass

    def save_token(self, token):
        self.saved_token = token
        self.token = token

    def clear_token(self):
        self.cleared = True
        self.token = None


class FakeCampus:
    def __init__(self, invalid_first=False, submitted=False) -> None:
        self.invalid_first = invalid_first
        self.submitted = submitted
        self.site_calls = 0

    def login(self, username, password):
        return "new-token"

    def site_info(self, token):
        self.site_calls += 1
        if self.invalid_first and self.site_calls == 1:
            raise CampusError("invalidtoken", "bad")
        return {"userid": 7}

    def courses(self, token, user_id):
        return [{"id": 1, "shortname": "IS", "fullname": "Curso", "visible": 1}]

    def assignments(self, token):
        return [{"id": 1, "assignments": [{"id": 10, "name": "Tarea", "duedate": 0, "url": None}]}]

    def submission_status(self, token, assignment_id):
        status = "submitted" if self.submitted else "new"
        return {"lastattempt": {"submission": {"status": status}}}


class SyncUseCaseTests(unittest.TestCase):
    def test_sync_with_fakes_persists_pending_task(self):
        repo = SQLiteTaskRepository(":memory:")
        result = SyncUseCase(repo, FakeCredentials(), FakeCampus()).execute()
        self.assertTrue(result.ok)
        self.assertEqual(result.pending_count, 1)
        self.assertEqual(len(repo.pending_tasks()), 1)
        repo.close()

    def test_invalid_token_is_regenerated(self):
        repo = SQLiteTaskRepository(":memory:")
        credentials = FakeCredentials(token="stale")
        result = SyncUseCase(repo, credentials, FakeCampus(invalid_first=True)).execute()
        self.assertTrue(result.ok)
        self.assertTrue(credentials.cleared)
        self.assertEqual(credentials.saved_token, "new-token")
        repo.close()

    def test_missing_credentials_returns_controlled_error(self):
        repo = SQLiteTaskRepository(":memory:")
        result = SyncUseCase(repo, FakeCredentials(token="missing"), FakeCampus()).execute()
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, "missing_credentials")
        repo.close()

    def test_submitted_task_is_not_pending(self):
        repo = SQLiteTaskRepository(":memory:")
        result = SyncUseCase(repo, FakeCredentials(), FakeCampus(submitted=True)).execute()
        self.assertTrue(result.ok)
        self.assertEqual(result.pending_count, 0)
        self.assertEqual(repo.pending_tasks(), [])
        repo.close()


if __name__ == "__main__":
    unittest.main()
