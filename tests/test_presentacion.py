"""Smoke tests de presentacion Qt y componentes de ChivaTask."""

import tempfile
import unittest
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from uph_pendientes.domain.modelos import Course, StoredCredentials, SyncResult, Task
from uph_pendientes.infrastructure.persistence import SQLiteTaskRepository
from uph_pendientes.infrastructure.security import WindowsCredentialRepository
from uph_pendientes.presentation.qt.componentes.prototipo import (
    CourseCard,
    MiniCalendar,
    PillFilter,
    SettingsRow,
    TaskRowCard,
    ToggleSwitch,
)
from uph_pendientes.presentation.qt.dialogo_login import LoginDialog
from uph_pendientes.presentation.qt.ventana_principal import CommandPalette, MainWindow, OnboardingDialog


class FakeCredentials:
    def __init__(self) -> None:
        self.username = "hugo.lopez@uph.edu.hn"
        self.password = "secret"
        self.token = None
        self.cleared = False

    def has_credentials(self):
        return bool(self.username and self.password)

    def get_username(self):
        return self.username

    def load(self):
        return StoredCredentials(self.username, self.password, self.token)

    def save_credentials(self, username, password):
        self.username = username
        self.password = password

    def save_token(self, token):
        self.token = token

    def clear_token(self):
        self.token = None

    def clear_all(self):
        self.username = None
        self.password = None
        self.token = None
        self.cleared = True


class FakeNotifier:
    def __init__(self) -> None:
        self.notified = []

    def notify_changed(self, tasks):
        self.notified.append(tasks)


class FakeAutostart:
    def __init__(self) -> None:
        self.value = False

    def enabled(self):
        return self.value

    def set_enabled(self, enabled):
        self.value = enabled


class PresentationSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_main_window_builds_with_chivatask_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = SQLiteTaskRepository(Path(tmp) / "cache.db")
            try:
                window = MainWindow(
                    repo,
                    FakeCredentials(),
                    FakeNotifier(),
                    FakeAutostart(),
                    lambda: SyncResult(False, 0, 0, [], "missing_credentials"),
                    21600,
                )
                self.assertEqual(window.windowTitle(), "ChivaTask")
                self.assertEqual(window.title_label.text(), "Tu campus bajo control")
                self.assertEqual(window.views.count(), 4)
                window.navigate("cursos")
                self.assertEqual(window.title_label.text(), "Cursos activos")
                self.assertEqual(window.task_scroll.horizontalScrollBarPolicy(), Qt.ScrollBarAlwaysOff)
                self.assertEqual(window.course_scroll.horizontalScrollBarPolicy(), Qt.ScrollBarAlwaysOff)
                window.close()
            finally:
                repo.close()

    def test_login_dialog_builds(self):
        dialog = LoginDialog(WindowsCredentialRepository("uph_pendientes_test_no_write"))
        self.assertEqual(dialog.windowTitle(), "Conecta tu campus")

    def test_onboarding_dialog_builds(self):
        dialog = OnboardingDialog(FakeCredentials())
        self.assertEqual(dialog.windowTitle(), "Bienvenido a ChivaTask")

    def test_command_palette_lists_navigation_and_cached_tasks(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = SQLiteTaskRepository(Path(tmp) / "cache.db")
            repo.upsert_courses([Course(1, "IS", "Curso", True)])
            repo.upsert_tasks([Task(10, 1, "IS", "Curso", "Tarea", None, None, "new")])
            window = MainWindow(
                repo,
                FakeCredentials(),
                FakeNotifier(),
                FakeAutostart(),
                lambda: SyncResult(False, 0, 0, [], "missing_credentials"),
                21600,
            )
            window.refresh_from_cache()
            palette = CommandPalette(window, window.tasks, window.navigate, window._select_task)
            self.assertGreaterEqual(palette.results.count(), 5)
            palette.close()
            window.close()
            repo.close()

    def test_prototype_components_build(self):
        task = Task(10, 1, "IS", "Curso", "Tarea", None, None, "new")
        summary = {
            "course_id": 1,
            "shortname": "IS",
            "fullname": "Curso",
            "pending": 1,
            "submitted": 2,
            "total": 3,
            "tasks": [task],
        }
        toggle = ToggleSwitch(True)
        row = SettingsRow("Titulo", "Subtitulo", toggle)
        widgets = [
            TaskRowCard(task),
            CourseCard(summary),
            MiniCalendar(2026, 6, {15: "overdue"}),
            PillFilter([("Todas", "todas"), ("Vencidas", "vencidas")], "todas"),
            row,
        ]
        self.assertTrue(toggle.isChecked())
        for widget in widgets:
            self.assertIsNotNone(widget.objectName())

    def test_pill_filter_tracks_selected_value(self):
        pills = PillFilter([("Todas", "todas"), ("Urgentes", "urgentes")], "todas")
        self.assertEqual(pills.currentData(), "todas")
        pills.set_value("urgentes")
        self.assertEqual(pills.currentData(), "urgentes")

    def test_open_data_folder_uses_repository_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = SQLiteTaskRepository(Path(tmp) / "cache.db")
            window = MainWindow(
                repo,
                FakeCredentials(),
                FakeNotifier(),
                FakeAutostart(),
                lambda: SyncResult(False, 0, 0, [], "missing_credentials"),
                21600,
            )
            calls = []
            import os

            original = getattr(os, "startfile", None)
            os.startfile = lambda path: calls.append(path)  # type: ignore[attr-defined]
            try:
                window.open_data_folder()
            finally:
                if original is not None:
                    os.startfile = original  # type: ignore[attr-defined]
            self.assertEqual(calls, [str(Path(tmp))])
            window.close()
            repo.close()


if __name__ == "__main__":
    unittest.main()
