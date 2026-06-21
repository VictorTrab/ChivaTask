"""Smoke tests de presentacion Qt y componentes de ChivaTask."""

import tempfile
import unittest
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from domain.modelos import Course, StoredCredentials, SyncResult, Task
from infrastructure.persistence import SQLiteTaskRepository
from infrastructure.security import WindowsCredentialRepository
from presentation.qt.componentes.prototipo import (
    CourseCard,
    MiniCalendar,
    PillFilter,
    SettingsRow,
    TaskRowCard,
    ToggleSwitch,
)
from presentation.qt.dialogo_login import LoginDialog
from presentation.qt.ventana_principal import CommandPalette, MainWindow, OnboardingDialog


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


class FakeNavigator:
    def __init__(self) -> None:
        self.urls = []
        self.folders = []

    def open_url(self, url):
        self.urls.append(url)
        return url.startswith("https://campus.uph.edu.hn")

    def open_campus_home(self):
        self.urls.append("home")
        return True

    def open_folder(self, path):
        self.folders.append(path)
        return True


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
                    FakeNavigator(),
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
                FakeNavigator(),
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
            navigator = FakeNavigator()
            window = MainWindow(
                repo,
                FakeCredentials(),
                FakeNotifier(),
                navigator,
                FakeAutostart(),
                lambda: SyncResult(False, 0, 0, [], "missing_credentials"),
                21600,
            )
            window.open_data_folder()
            self.assertEqual(navigator.folders, [Path(tmp)])
            window.close()
            repo.close()

    def test_onboarding_is_marked_complete_after_successful_sync(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = SQLiteTaskRepository(Path(tmp) / "cache.db")
            window = MainWindow(
                repo,
                FakeCredentials(),
                FakeNotifier(),
                FakeNavigator(),
                FakeAutostart(),
                lambda: SyncResult(True, 0, 0, []),
                21600,
            )
            window.awaiting_onboarding_sync = True

            window._sync_finished(SyncResult(True, 0, 0, []))

            self.assertTrue(window.settings.onboarding_completed())
            self.assertFalse(window.awaiting_onboarding_sync)
            window.close()
            repo.close()

    def test_visual_preferences_apply_dark_compact_stylesheet(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = SQLiteTaskRepository(Path(tmp) / "cache.db")
            repo.set_setting("visual_mode", "oscuro")
            repo.set_setting("ui_density", "compacta")
            window = MainWindow(
                repo,
                FakeCredentials(),
                FakeNotifier(),
                FakeNavigator(),
                FakeAutostart(),
                lambda: SyncResult(False, 0, 0, [], "missing_credentials"),
                21600,
            )

            stylesheet = window.styleSheet()

            self.assertIn("#101820", stylesheet)
            self.assertIn("font-size: 12px", stylesheet)
            window.close()
            repo.close()

    def test_responsive_layout_hides_side_panels_on_small_width(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = SQLiteTaskRepository(Path(tmp) / "cache.db")
            window = MainWindow(
                repo,
                FakeCredentials(),
                FakeNotifier(),
                FakeNavigator(),
                FakeAutostart(),
                lambda: SyncResult(False, 0, 0, [], "missing_credentials"),
                21600,
            )

            window.resize(1000, 680)
            window._apply_responsive_layout()

            self.assertFalse(window.task_detail.isVisible())
            self.assertEqual(window.sidebar.width(), 176)
            window.close()
            repo.close()

    def test_ui_state_labels_accessibility_and_greeting(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = SQLiteTaskRepository(Path(tmp) / "cache.db")
            window = MainWindow(
                repo,
                FakeCredentials(),
                FakeNotifier(),
                FakeNavigator(),
                FakeAutostart(),
                lambda: SyncResult(False, 0, 0, [], "missing_credentials"),
                21600,
            )

            window.refresh_task_list()

            self.assertEqual(window.task_search.accessibleName(), "Buscar tareas")
            self.assertEqual(window.course_search.accessibleName(), "Buscar cursos")
            self.assertEqual(window.sync_button.accessibleName(), "Sincronizar tareas")
            self.assertEqual(window.data_state_label.property("dataState"), "empty")
            self.assertEqual(window._greeting_for_hour(9), "Buenos dias")
            self.assertEqual(window._greeting_for_hour(15), "Buenas tardes")
            self.assertEqual(window._greeting_for_hour(22), "Buenas noches")
            window.close()
            repo.close()

    def test_snooze_accepts_explicit_day_options(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = SQLiteTaskRepository(Path(tmp) / "cache.db")
            repo.upsert_courses([Course(1, "IS", "Curso", True)])
            task = Task(10, 1, "IS", "Curso", "Tarea", None, None, "new")
            repo.upsert_tasks([task])
            window = MainWindow(
                repo,
                FakeCredentials(),
                FakeNotifier(),
                FakeNavigator(),
                FakeAutostart(),
                lambda: SyncResult(False, 0, 0, [], "missing_credentials"),
                21600,
            )
            window.selected_task = task

            window.snooze_selected(3)

            snoozed = repo.pending_tasks()[0].snoozed_until
            self.assertIsNotNone(snoozed)
            self.assertGreaterEqual(int(snoozed), 3 * 86400)
            self.assertGreaterEqual(len(window.snooze_menu.actions()), 3)
            window.close()
            repo.close()


if __name__ == "__main__":
    unittest.main()
