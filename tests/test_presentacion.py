"""Smoke tests de presentacion Qt y componentes de ChivaTask."""

import tempfile
import unittest
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication, QLabel, QProgressBar, QPushButton, QScrollArea

from domain.modelos import Course, StoredCredentials, SyncResult, Task
from infrastructure.persistence import SQLiteTaskRepository
from presentation.qt.bandeja import TrayController
from presentation.qt.componentes.botones import IconButton, PrimaryButton, SecondaryButton
from presentation.qt.componentes.prototipo import (
    CourseCard,
    ElidedLabel,
    MiniCalendar,
    PillFilter,
    SegmentedControl,
    SettingsRow,
    TaskRowCard,
    ToggleSwitch,
    ProgressRing,
)
from presentation.qt.componentes.shell import LoadingSpinner, NavItem, SearchField, SyncStatusPill, SyncToast
from presentation.qt.componentes.perfil import ProfileButton
from presentation.qt.dialogo_login import LoginDialog
from presentation.qt.dialogo_onboarding import OnboardingDialog
from presentation.qt.registro_iconos import IconRegistry
from presentation.qt.ventana_principal import MainWindow


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


class FakeTray:
    def __init__(self) -> None:
        self.messages = 0
        self.resets = 0
        self.visible = True

    def is_visible(self) -> bool:
        return self.visible

    def show_background_message(self) -> None:
        self.messages += 1

    def reset_background_message(self) -> None:
        self.resets += 1


class FakeSystemTray:
    def __init__(self) -> None:
        self.messages = 0

    def showMessage(self, *_args) -> None:  # noqa: N802 - Qt API
        self.messages += 1


class PresentationSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setProperty("chivatask_testing", True)

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
        dialog = LoginDialog(FakeCredentials())
        self.assertEqual(dialog.windowTitle(), "Conecta tu campus")
        self.assertEqual(dialog.objectName(), "accessWindow")
        self.assertEqual(dialog.password.placeholderText(), "Contraseña del campus")
        self.assertEqual(dialog.username.accessibleName(), "Usuario del campus")
        self.assertEqual(dialog.password.accessibleName(), "Contraseña del campus")
        self.assertTrue(hasattr(dialog, "exec_maximized"))
        self.assertGreaterEqual(dialog.username.minimumHeight(), 46)
        self.assertLessEqual(dialog.password_toggle.maximumWidth(), 90)

    def test_login_dialog_shows_inline_validation(self):
        dialog = LoginDialog(FakeCredentials())

        dialog.save()

        self.assertFalse(dialog.error_label.isHidden())
        self.assertIn("usuario y contraseña", dialog.error_label.text())

    def test_onboarding_dialog_builds(self):
        dialog = OnboardingDialog(FakeCredentials())
        self.assertEqual(dialog.windowTitle(), "Bienvenido a ChivaTask")

    def test_sidebar_uses_badges_without_global_search(self):
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
            button_texts = [button.text() for button in window.findChildren(QPushButton)]
            self.assertFalse(any("Ctrl" in text for text in button_texts))
            self.assertEqual(window.nav_buttons["tareas"].text_label.text(), "Tareas")
            self.assertEqual(window.nav_buttons["tareas"].badge.text(), "1")
            self.assertEqual(window.nav_buttons["cursos"].text_label.text(), "Cursos")
            self.assertEqual(window.nav_buttons["cursos"].badge.text(), "1")
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
        opened = []
        widgets[1].open_campus.connect(opened.append)
        widgets[1].open_campus.emit(summary)
        self.assertTrue(toggle.isChecked())
        self.assertEqual(toggle.text(), "")
        self.assertEqual(opened, [summary])
        for widget in widgets:
            self.assertIsNotNone(widget.objectName())

    def test_course_card_allows_long_names_and_full_status_chip(self):
        task = Task(10, 1, "IS", "Curso", "Parcial", 1, None, "new")
        summary = {
            "course_id": 1,
            "shortname": "IS-441 - IIP-2026",
            "fullname": "Traductores e Interpretes II con nombre academico deliberadamente largo",
            "pending": 1,
            "submitted": 4,
            "total": 5,
            "tasks": [task],
        }

        card = CourseCard(summary)
        labels = card.findChildren(QLabel)
        name_labels = [label for label in labels if isinstance(label, ElidedLabel) and label.toolTip() == summary["fullname"]]
        chips = [label for label in labels if label.text() == "Con vencidas"]

        self.assertTrue(name_labels)
        self.assertEqual(name_labels[0].lines, 2)
        self.assertGreaterEqual(card.maximumHeight(), 16_000)
        self.assertTrue(chips)
        self.assertGreaterEqual(chips[0].sizeHint().width(), chips[0].minimumSizeHint().width())

    def test_clickable_cards_are_keyboard_accessible(self):
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
        task_card = TaskRowCard(task)
        course_card = CourseCard(summary)
        selected_tasks = []
        selected_courses = []
        task_card.selected.connect(selected_tasks.append)
        course_card.selected.connect(selected_courses.append)

        task_card.keyPressEvent(QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Return, Qt.NoModifier))
        course_card.keyPressEvent(QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Space, Qt.NoModifier))

        self.assertEqual(task_card.focusPolicy(), Qt.StrongFocus)
        self.assertEqual(course_card.focusPolicy(), Qt.StrongFocus)
        self.assertEqual(task_card.accessibleName(), "Tarea: Tarea")
        self.assertEqual(course_card.accessibleName(), "Curso: Curso")
        self.assertEqual(selected_tasks, [task])
        self.assertEqual(selected_courses, [summary])

    def test_progress_ring_is_not_a_progress_bar_wrapper(self):
        ring = ProgressRing(67, "Progreso global")
        self.assertEqual(ring.value, 67)
        self.assertEqual(ring.findChildren(QProgressBar), [])

    def test_shell_components_expose_clean_state(self):
        icons = IconRegistry()
        nav = NavItem(icons.icon("home", "light"), "Tareas")
        nav.set_badge(12)
        nav.set_active(True)
        search = SearchField(icons.icon("search", "muted"), "Buscar...")
        status = SyncStatusPill(icons.icon("check", "brand"))

        status.set_status("Sincronizado", "ok", "hace 2m")

        self.assertEqual(nav.accessibleName(), "Tareas")
        self.assertEqual(nav.text_label.text(), "Tareas")
        self.assertEqual(nav.badge.text(), "12")
        self.assertEqual(nav.objectName(), "navItemActive")
        self.assertEqual(search.objectName(), "searchField")
        self.assertEqual(status.text(), "Sincronizado")
        self.assertEqual(status.detail_label.text(), "hace 2m")

        status.set_status("Sincronizando...", "syncing")
        self.assertFalse(status.spinner.isHidden())
        status.set_status("Sincronizado", "ok")
        self.assertTrue(status.spinner.isHidden())

    def test_loading_spinner_starts_and_stops_timer(self):
        spinner = LoadingSpinner()

        spinner.start()
        self.assertTrue(spinner.isVisible())
        spinner.stop()

        self.assertFalse(spinner.isVisible())

    def test_sync_toast_exposes_retry_and_deduplicates_widget(self):
        toast = SyncToast()
        retries = []
        toast.retry_requested.connect(lambda: retries.append(True))

        toast.show_message("No se pudo sincronizar", "Usando cache local.", "error", retry=True)
        toast.retry_button.click()
        toast.show_message("Sincronizacion completada", "Datos actualizados.", "success")

        self.assertEqual(toast.title_label.text(), "Sincronizacion completada")
        self.assertFalse(toast.retry_button.isVisible())
        self.assertEqual(toast.icon_label.text(), "OK")
        self.assertEqual(retries, [True])

    def test_base_buttons_expose_accessible_names(self):
        icons = IconRegistry()
        primary = PrimaryButton("Guardar", icons.icon("check", "light"))
        secondary = SecondaryButton("Cancelar")
        icon = IconButton(icons.icon("settings", "muted"), "Configurar")

        self.assertEqual(primary.accessibleName(), "Guardar")
        self.assertEqual(secondary.accessibleName(), "Cancelar")
        self.assertEqual(icon.accessibleName(), "Configurar")
        self.assertEqual(icon.toolTip(), "Configurar")

    def test_profile_button_shows_initials_and_display_name(self):
        button = ProfileButton(IconRegistry(), FakeCredentials(), lambda: None, lambda: None)

        self.assertEqual(button.avatar.text(), "HL")
        self.assertEqual(button.name_label.text(), "Hugo Lopez")
        self.assertEqual(button.accessibleName(), "Perfil local")

    def test_pill_filter_tracks_selected_value(self):
        pills = PillFilter([("Todas", "todas"), ("Urgentes", "urgentes")], "todas")
        self.assertEqual(pills.currentData(), "todas")
        pills.set_value("urgentes")
        self.assertEqual(pills.currentData(), "urgentes")

    def test_filter_controls_are_keyboard_accessible(self):
        pills = PillFilter([("Todas", "todas"), ("Urgentes", "urgentes")], "todas")
        segments = SegmentedControl([("Todos", "todos"), ("Sin pendientes", "sin")], "todos")

        for button in [*pills.buttons.values(), *segments.buttons.values()]:
            self.assertEqual(button.focusPolicy(), Qt.StrongFocus)
            self.assertTrue(button.accessibleName())

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

    def test_background_tray_message_is_shown_once_until_reset(self):
        controller = object.__new__(TrayController)
        controller._background_message_shown = False
        controller.tray = FakeSystemTray()

        controller.show_background_message()
        controller.show_background_message()

        self.assertEqual(controller.tray.messages, 1)

        controller.reset_background_message()
        controller.show_background_message()

        self.assertEqual(controller.tray.messages, 2)

    def test_show_normal_rearms_background_tray_message(self):
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
            tray = FakeTray()
            window.tray = tray  # type: ignore[assignment]

            window.show_normal()

            self.assertEqual(tray.resets, 1)
            tray.visible = False
            window.close()
            repo.close()

    def test_main_window_does_not_prompt_login_on_startup_without_credentials(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = SQLiteTaskRepository(Path(tmp) / "cache.db")
            credentials = FakeCredentials()
            credentials.clear_all()
            window = MainWindow(
                repo,
                credentials,
                FakeNotifier(),
                FakeNavigator(),
                FakeAutostart(),
                lambda: SyncResult(True, 0, 0, []),
                21600,
            )

            window.ensure_startup_sync()

            self.assertEqual(window.status_pill.text(), "Credenciales pendientes")
            self.assertFalse(window.syncing)
            window.close()
            repo.close()

    def test_visual_preferences_apply_dark_stylesheet_and_remove_density(self):
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

            stylesheet = self.app.styleSheet()

            self.assertIn("#101820", stylesheet)
            self.assertNotIn("font-size: 19px", stylesheet)
            self.assertEqual(window.styleSheet(), "")
            self.assertIsNone(repo.get_setting("ui_density"))
            window.close()
            repo.close()

    def test_course_detail_uses_structured_cards(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = SQLiteTaskRepository(Path(tmp) / "cache.db")
            task = Task(10, 1, "IS", "Curso de Ingenieria", "Proyecto", None, None, "new")
            summary = {
                "course_id": 1,
                "shortname": "IS",
                "fullname": "Curso de Ingenieria",
                "pending": 1,
                "submitted": 2,
                "total": 3,
                "tasks": [task],
            }
            window = MainWindow(
                repo,
                FakeCredentials(),
                FakeNotifier(),
                FakeNavigator(),
                FakeAutostart(),
                lambda: SyncResult(False, 0, 0, [], "missing_credentials"),
                21600,
            )

            window._select_course_summary(summary)

            self.assertEqual(window.course_detail_title.text(), "Curso de Ingenieria")
            self.assertEqual(window.course_fullname_label.text(), "")
            self.assertEqual(window.course_pending_card.value_label.text(), "1 pendiente")
            self.assertEqual(window.course_progress_percent.text(), "66%")
            self.assertIn("2 de 3 entregadas", window.course_progress_text.text())
            preview_titles = [label.text() for label in window.course_preview_card.findChildren(QLabel)]
            self.assertIn("Proyecto", " ".join(preview_titles))
            self.assertIsInstance(window.course_detail_scroll, QScrollArea)
            window.close()
            repo.close()

    def test_courses_view_uses_segmented_filter_and_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = SQLiteTaskRepository(Path(tmp) / "cache.db")
            overdue = Task(10, 1, "IS", "Curso IS", "Proyecto", 1, None, "new")
            repo.upsert_courses([Course(1, "IS", "Curso IS", True), Course(2, "MA", "Curso MA", True)])
            repo.upsert_tasks([overdue, Task(20, 2, "MA", "Curso MA", "Tarea", None, None, "new")])
            window = MainWindow(
                repo,
                FakeCredentials(),
                FakeNotifier(),
                FakeNavigator(),
                FakeAutostart(),
                lambda: SyncResult(False, 0, 0, [], "missing_credentials"),
                21600,
            )

            window.refresh_course_list()

            self.assertIsInstance(window.course_filter, SegmentedControl)
            self.assertEqual(window.course_total_metric.value_label.text(), "2")
            self.assertEqual(window.course_pending_metric.value_label.text(), "2")
            self.assertEqual(window.course_overdue_metric.value_label.text(), "1")
            self.assertEqual(window.course_metrics_caption.text(), "Resumen general")
            window.course_filter.set_value("sin_pendientes")
            self.assertIn("Sin pendientes", window.course_filter_caption.text())
            self.assertFalse(any("Ctrl" in button.text() for button in window.findChildren(QPushButton)))
            window.close()
            repo.close()

    def test_course_filter_clears_obsolete_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = SQLiteTaskRepository(Path(tmp) / "cache.db")
            pending = Task(10, 1, "IS", "Curso IS", "Proyecto", 1, None, "new")
            done = Task(20, 2, "MA", "Curso MA", "Tarea", None, None, "submitted")
            repo.upsert_courses([Course(1, "IS", "Curso IS", True), Course(2, "MA", "Curso MA", True)])
            repo.upsert_tasks([pending, done])
            window = MainWindow(
                repo,
                FakeCredentials(),
                FakeNotifier(),
                FakeNavigator(),
                FakeAutostart(),
                lambda: SyncResult(False, 0, 0, [], "missing_credentials"),
                21600,
            )

            window.refresh_course_list()
            window._select_course_summary(window.course_summaries[0])
            window.course_filter.set_value("sin_pendientes")

            self.assertIsNone(window.selected_course)
            self.assertEqual(window.course_detail_title.text(), "Selecciona un curso")
            window.close()
            repo.close()

    def test_task_filter_clears_obsolete_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = SQLiteTaskRepository(Path(tmp) / "cache.db")
            overdue = Task(10, 1, "IS", "Curso IS", "Vencida", 1, None, "new")
            undated = Task(20, 2, "MA", "Curso MA", "Sin fecha", None, None, "new")
            repo.upsert_courses([Course(1, "IS", "Curso IS", True), Course(2, "MA", "Curso MA", True)])
            repo.upsert_tasks([overdue, undated])
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
            window._select_task(overdue)
            window.task_filter.set_value("sin_fecha")

            self.assertIsNone(window.selected_task)
            self.assertEqual(window.detail_title.text(), "Selecciona una tarea")
            window.close()
            repo.close()

    def test_home_renders_priority_plan_and_real_alerts(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = SQLiteTaskRepository(Path(tmp) / "cache.db")
            now = 1
            overdue = Task(10, 1, "IS", "Curso IS", "TAREA PARCIAL II", now, None, "new")
            exam = Task(20, 1, "IS", "Curso IS", "Evaluacion unidad 3", now + 86400, None, "new")
            undated = Task(30, 2, "MA", "Curso MA", "Actividad sin fecha", None, None, "new")
            repo.upsert_courses([Course(1, "IS", "Curso IS", True), Course(2, "MA", "Curso MA", True)])
            repo.upsert_tasks([overdue, exam, undated])
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
            texts = " ".join(label.text() for label in window.plan_card.findChildren(QLabel))
            alerts = " ".join(label.text() for label in window.alerts_card.findChildren(QLabel))

            self.assertIn("TU PLAN DE HOY", texts)
            self.assertLessEqual(len(window.plan_card.findChildren(QPushButton)), 9)
            self.assertIn("Prioridad", texts)
            self.assertIn("Posible evaluacion", alerts)
            window.close()
            repo.close()

    def test_compact_detail_modals_expose_primary_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = SQLiteTaskRepository(Path(tmp) / "cache.db")
            task = Task(10, 1, "IS", "Curso de Ingenieria", "Proyecto final", None, None, "new")
            summary = {
                "course_id": 1,
                "shortname": "IS",
                "fullname": "Curso de Ingenieria",
                "pending": 1,
                "submitted": 2,
                "total": 3,
                "tasks": [task],
            }
            window = MainWindow(
                repo,
                FakeCredentials(),
                FakeNotifier(),
                FakeNavigator(),
                FakeAutostart(),
                lambda: SyncResult(False, 0, 0, [], "missing_credentials"),
                21600,
            )

            task_modal = window._build_task_detail_modal(task)
            course_modal = window._build_course_detail_modal(summary)
            task_buttons = [button.text() for button in task_modal.findChildren(QPushButton)]
            course_buttons = [button.text() for button in course_modal.findChildren(QPushButton)]

            self.assertIn("Abrir campus", task_buttons)
            self.assertIn("Recordar mañana", task_buttons)
            self.assertIn("Abrir Moodle", course_buttons)
            self.assertIn("Ver tareas", course_buttons)
            self.assertGreaterEqual(window.task_detail.minimumWidth(), 280)
            self.assertLessEqual(window.task_detail.maximumWidth(), 340)
            task_modal.close()
            course_modal.close()
            window.close()
            repo.close()

    def test_settings_pages_use_reference_structure(self):
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

            window.navigate("ajustes")
            frame_type = type(window.profile_summary)
            self.assertEqual(window.profile_settings_name.text(), "Hugo Lopez")
            self.assertIsNotNone(window.settings_stack.widget(0).findChild(frame_type, "profileSettingsCard"))
            self.assertIsNotNone(window.settings_stack.widget(3).findChild(frame_type, "settingsInfoList"))
            self.assertIsNotNone(window.settings_stack.widget(5).findChild(frame_type, "aboutHero"))
            window.close()
            repo.close()

    def test_screenshot_smoke_views_render_nonblank(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = SQLiteTaskRepository(Path(tmp) / "cache.db")
            repo.upsert_courses([Course(1, "IS", "Curso de Ingenieria", True)])
            repo.upsert_tasks([Task(10, 1, "IS", "Curso de Ingenieria", "Proyecto", None, None, "new")])
            window = MainWindow(
                repo,
                FakeCredentials(),
                FakeNotifier(),
                FakeNavigator(),
                FakeAutostart(),
                lambda: SyncResult(False, 0, 0, [], "missing_credentials"),
                21600,
            )
            window.resize(1366, 768)
            window.show()
            self.app.processEvents()

            captures = []
            for view in ("inicio", "tareas", "cursos", "ajustes"):
                window.navigate(view)
                window.refresh_from_cache()
                self.app.processEvents()
                pixmap = window.grab()
                path = Path(tmp) / f"{view}.png"
                self.assertTrue(pixmap.save(str(path)))
                self.assertGreater(path.stat().st_size, 8_000)
                captures.append(path)

            login = LoginDialog(FakeCredentials())
            login.resize(480, 420)
            login.setStyleSheet(window.styleSheet())
            login.show()
            self.app.processEvents()
            login_path = Path(tmp) / "login.png"
            self.assertTrue(login.grab().save(str(login_path)))
            self.assertGreater(login_path.stat().st_size, 8_000)

            self.assertEqual(len(captures), 4)
            login.close()
            window.close()
            repo.close()

    def test_theme_toggle_switches_mode_and_syncs_buttons(self):
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

            self.assertEqual(window.settings.visual_mode(), "claro")
            self.assertFalse(hasattr(window, "header_theme_toggle"))
            window.appearance_theme_toggle.click()

            self.assertEqual(window.settings.visual_mode(), "oscuro")
            self.assertEqual(window.appearance_theme_toggle.visual_mode, "oscuro")
            self.assertIn("#101820", self.app.styleSheet())

            window.appearance_theme_toggle.click()

            self.assertEqual(window.settings.visual_mode(), "claro")
            self.assertEqual(window.appearance_theme_toggle.visual_mode, "claro")
            self.assertIn("#F5F7FA", self.app.styleSheet())
            window.close()
            repo.close()

    def test_sync_feedback_restores_button_and_positions_toast_in_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = SQLiteTaskRepository(Path(tmp) / "cache.db")
            window = MainWindow(
                repo,
                FakeCredentials(),
                FakeNotifier(),
                FakeNavigator(),
                FakeAutostart(),
                lambda: SyncResult(True, 3, 2, [Task(1, 1, "IS", "Curso", "Tarea", None, None, "new")]),
                21600,
            )

            window._set_status("Sincronizando...", "syncing")
            window.sync_button.setEnabled(False)
            window.sync_button.setText("Sincronizando...")
            window._sync_finished(SyncResult(True, 3, 2, []))

            self.assertTrue(window.sync_button.isEnabled())
            self.assertEqual(window.sync_button.text(), "Sincronizar")
            self.assertFalse(window.status_pill.spinner.isVisible())
            self.assertEqual(window.sync_toast.parent(), window.content_root)
            self.assertEqual(window.sync_toast.title_label.text(), "Sincronizado")
            self.assertIn("No se detectaron", window.sync_toast.detail_label.text())
            self.assertLessEqual(window.sync_toast.x() + window.sync_toast.width(), window.content_root.width())
            window.close()
            repo.close()

    def test_appearance_settings_no_longer_show_density_row(self):
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

            labels = [label.text() for label in window.findChildren(type(window.title_label))]

            self.assertNotIn("Densidad de informacion", labels)
            self.assertIn("Modo oscuro", labels)
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
            self.assertEqual(window.task_sort.accessibleName(), "Ordenar tareas")
            self.assertEqual(window.course_filter.accessibleName(), "Filtrar cursos")
            self.assertEqual(window.interval_combo.accessibleName(), "Intervalo de sincronización")
            self.assertEqual(window.notif_mode.accessibleName(), "Modo de notificaciones")
            self.assertEqual(window.sync_button.accessibleName(), "Sincronizar tareas")
            self.assertEqual(window.data_state_label.property("dataState"), "empty")
            self.assertEqual(window._greeting_for_hour(9), "Buenos días")
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
