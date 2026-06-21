"""Ventana principal Qt: shell visual de ChivaTask y flujos de usuario."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from PySide6.QtCore import QThread, QTimer, Qt, Signal
from PySide6.QtGui import QAction, QCloseEvent, QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from application.consultas_tareas import TaskQueries
from application.puertos import (
    AutostartManager,
    CredentialRepository,
    DesktopNavigator,
    DesktopNotifier,
    TaskRepository,
)
from application.servicio_ajustes import SettingsService
from domain.modelos import SyncResult, Task, TaskBucket
from domain.politica_tareas import classify_task
from domain.tiempo import now_ts, unix_to_local_text
from shared.ajustes import APP_NAME
from shared.errores import CredentialError

from .bandeja import TrayController
from .componentes.botones import PrimaryButton, SecondaryButton
from .componentes.chips import StatusChip
from .componentes.modales import BaseModal, ConfirmModal
from .componentes.perfil import ProfileButton
from .componentes.prototipo import (
    CourseCard,
    EmptyState,
    MetricCard,
    MiniCalendar,
    ProgressRing,
    SettingsRow,
    TaskRowCard,
    ThemeToggleButton,
    ToggleSwitch,
    PillFilter,
    relative_due_text,
)
from .componentes.tarjetas import DetailPanel, StatCard
from .dialogo_login import LoginDialog
from .animaciones import set_animations_enabled
from .estilos import app_stylesheet
from .logo import BrandLockup, logo_icon
from .registro_iconos import IconRegistry
from .trabajador_sincronizacion import SyncWorker


class MainWindow(QMainWindow):
    sync_finished = Signal(object)

    def __init__(
        self,
        repository: TaskRepository,
        credentials: CredentialRepository,
        notifier: DesktopNotifier,
        navigator: DesktopNavigator,
        autostart: AutostartManager,
        run_sync,
        sync_interval_seconds: int,
    ) -> None:
        super().__init__()
        self.setFont(QFont("Segoe UI", 10))
        self.repository = repository
        self.credentials = credentials
        self.notifier = notifier
        self.navigator = navigator
        self.autostart = autostart
        self.run_sync = run_sync
        self.settings = SettingsService(repository, autostart)
        self.settings.cleanup_legacy_settings()
        self.queries = TaskQueries(repository)
        self.icons = IconRegistry()
        self.theme_toggles: list[ThemeToggleButton] = []
        self.tasks: list[Task] = []
        self.filtered_tasks: list[Task] = []
        self.selected_task: Task | None = None
        self.selected_course: dict[str, object] | None = None
        self.worker_thread: QThread | None = None
        self.worker: SyncWorker | None = None
        self.syncing = False
        self.api_status = "pending"
        self.last_error_code: str | None = None
        self.awaiting_onboarding_sync = False
        self.task_search_timer = QTimer(self)
        self.task_search_timer.setSingleShot(True)
        self.task_search_timer.setInterval(250)
        self.task_search_timer.timeout.connect(self.refresh_task_list)
        self.course_search_timer = QTimer(self)
        self.course_search_timer.setSingleShot(True)
        self.course_search_timer.setInterval(250)
        self.course_search_timer.timeout.connect(self.refresh_course_list)

        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(logo_icon())
        self.resize(1240, 760)
        self.setMinimumSize(960, 640)
        self._build_ui()
        self.tray = TrayController(self, self.icons, self.show_normal, self.sync_now)
        self.sync_finished.connect(self._sync_finished)

        self.timer = QTimer(self)
        self.timer.setInterval(sync_interval_seconds * 1000)
        self.timer.timeout.connect(self.sync_now)
        self.timer.start()
        self.command_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        self.command_shortcut.activated.connect(self.open_command_palette)

        self.refresh_from_cache()
        QTimer.singleShot(300, self.ensure_login_and_sync)

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(12, 18, 12, 14)
        sidebar_layout.setSpacing(8)
        sidebar_layout.addWidget(BrandLockup(compact=True))

        self.nav_buttons: dict[str, QPushButton] = {}
        for key, icon, text in (
            ("inicio", "home", "Inicio"),
            ("tareas", "tasks", "Tareas"),
            ("cursos", "courses", "Cursos"),
            ("ajustes", "settings", "Ajustes"),
        ):
            button = QPushButton(self.icons.icon(icon), text)
            button.setObjectName("navItem")
            button.setFlat(True)
            button.clicked.connect(lambda _=False, nav_key=key: self.navigate(nav_key))
            sidebar_layout.addWidget(button)
            self.nav_buttons[key] = button
        self.command_hint = QPushButton(self.icons.icon("tasks"), "Buscar...   Ctrl+K")
        self.command_hint.setObjectName("navHint")
        self.command_hint.clicked.connect(self.open_command_palette)
        sidebar_layout.addWidget(self.command_hint)
        sidebar_layout.addStretch(1)
        self.version_label = QLabel("v1.0.0 - IIP-2026")
        self.version_label.setObjectName("sidebarMuted")
        sidebar_layout.addWidget(self.version_label)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addLayout(self._build_header())
        self.error_banner = self._build_error_banner()
        content_layout.addWidget(self.error_banner)
        self.views = QStackedWidget()
        self.views.addWidget(self._build_inicio_view())
        self.views.addWidget(self._build_tareas_view())
        self.views.addWidget(self._build_cursos_view())
        self.views.addWidget(self._build_ajustes_view())
        content_layout.addWidget(self.views, 1)
        self.footer = self._build_footer()
        content_layout.addWidget(self.footer)

        root_layout.addWidget(self.sidebar)
        root_layout.addWidget(content, 1)
        self.setCentralWidget(root)
        self._apply_visual_preferences()
        self.navigate("inicio")

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        header.setContentsMargins(24, 14, 24, 14)
        header.setSpacing(14)
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.title_label = QLabel("Tu campus bajo control")
        self.title_label.setObjectName("title")
        self.subtitle_label = QLabel("Resumen sincronizado desde Moodle")
        self.subtitle_label.setObjectName("subtitle")
        title_box.addWidget(self.title_label)
        title_box.addWidget(self.subtitle_label)
        self.status_pill = QLabel("Sin sincronizar")
        self.status_pill.setObjectName("statusPending")
        self.status_pill.setMaximumWidth(240)
        self.status_pill.setMinimumHeight(36)
        self.status_pill.setAlignment(Qt.AlignCenter)
        self.header_theme_toggle = self._new_theme_toggle()
        self.profile_button = ProfileButton(self.icons, self.credentials, self.change_profile, self.logout_local)
        header.addLayout(title_box)
        header.addStretch(1)
        header.addWidget(self.header_theme_toggle)
        header.addWidget(self.status_pill)
        header.addWidget(self.profile_button)
        return header

    def _build_error_banner(self) -> QFrame:
        banner = QFrame()
        banner.setObjectName("errorBanner")
        layout = QHBoxLayout(banner)
        layout.setContentsMargins(24, 8, 24, 8)
        self.error_label = QLabel("Sin conexion a Moodle - Mostrando datos en cache")
        retry = QPushButton("Reintentar")
        retry.setObjectName("linkButton")
        retry.clicked.connect(self.sync_now)
        layout.addWidget(self.error_label)
        layout.addStretch(1)
        layout.addWidget(retry)
        banner.hide()
        return banner

    def _build_footer(self) -> QFrame:
        footer = QFrame()
        footer.setObjectName("footer")
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(24, 10, 24, 10)
        self.sync_button = PrimaryButton("Sincronizar", self.icons.icon("refresh"))
        self.sync_button.setMaximumWidth(150)
        self.sync_button.setAccessibleName("Sincronizar tareas")
        self.sync_button.setToolTip("Sincronizar tareas con Moodle")
        self.sync_button.clicked.connect(self.sync_now)
        self.data_state_label = QLabel("Listo")
        self.data_state_label.setObjectName("muted")
        self.data_state_label.setAccessibleName("Estado de datos")
        layout.addWidget(self.data_state_label)
        layout.addStretch(1)
        layout.addWidget(self.sync_button)
        return footer

    def _build_inicio_view(self) -> QWidget:
        view = QWidget()
        layout = QHBoxLayout(view)
        layout.setContentsMargins(24, 20, 24, 18)
        layout.setSpacing(16)
        main = QWidget()
        main.setMinimumWidth(560)
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)
        self.home_side = QWidget()
        self.home_side.setFixedWidth(292)
        side_layout = QVBoxLayout(self.home_side)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(14)
        self.greeting_date = QLabel("")
        self.greeting_date.setObjectName("muted")
        self.greeting_title = QLabel("")
        self.greeting_title.setObjectName("heroTitle")
        stats = QGridLayout()
        stats.setHorizontalSpacing(10)
        self.pending_card = MetricCard(self.icons.icon("bell"), "0", "Pendientes", "warning")
        self.overdue_card = MetricCard(self.icons.icon("calendar_due"), "0", "Vencidas", "danger")
        self.week_card = MetricCard(self.icons.icon("calendar_due"), "0", "Esta semana", "info")
        self.course_card = MetricCard(self.icons.icon("courses"), "0", "Cursos", "ok")
        stats.addWidget(self.pending_card, 0, 0)
        stats.addWidget(self.overdue_card, 0, 1)
        stats.addWidget(self.week_card, 0, 2)
        stats.addWidget(self.course_card, 0, 3)

        self.next_deadline_card = QFrame()
        self.next_deadline_card.setObjectName("nextDeadlineCard")
        next_layout = QHBoxLayout(self.next_deadline_card)
        next_layout.setContentsMargins(18, 16, 18, 16)
        self.next_deadline_text = QLabel("")
        self.next_deadline_text.setObjectName("nextDeadlineText")
        self.next_deadline_text.setWordWrap(True)
        next_button = PrimaryButton("Ver tarea")
        next_button.clicked.connect(self._open_next_deadline)
        next_layout.addWidget(self.next_deadline_text, 1)
        next_layout.addWidget(next_button)

        self.home_sections = QWidget()
        self.home_sections_layout = QVBoxLayout(self.home_sections)
        self.home_sections_layout.setContentsMargins(0, 0, 0, 0)
        self.home_sections_layout.setSpacing(12)
        home_scroll = self._scroll_area(self.home_sections)

        current = date.today()
        self.calendar = MiniCalendar(current.year, current.month, {})
        self.progress_ring = ProgressRing(0, "Progreso global")
        side_layout.addWidget(self.calendar)
        side_layout.addWidget(self.progress_ring)
        self.health_label = QLabel("")
        self.health_label.setWordWrap(True)
        self.health_label.setObjectName("settingsCard")
        side_layout.addWidget(self.health_label)
        side_layout.addStretch(1)

        main_layout.addWidget(self.greeting_date)
        main_layout.addWidget(self.greeting_title)
        main_layout.addLayout(stats)
        main_layout.addWidget(self.next_deadline_card)
        main_layout.addWidget(home_scroll, 1)
        layout.addWidget(main, 1)
        layout.addWidget(self.home_side)
        return view

    def _build_tareas_view(self) -> QWidget:
        view = QWidget()
        layout = QHBoxLayout(view)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(14)

        left = QWidget()
        left.setMinimumWidth(560)
        left.setMinimumWidth(560)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        filters = QHBoxLayout()
        self.task_filter = PillFilter([
            ("Todas", "todas"),
            ("Urgentes", "urgentes"),
            ("Vencidas", TaskBucket.OVERDUE.value),
            ("Sin entrega", TaskBucket.UPCOMING.value),
            ("Sin fecha", TaskBucket.UNDATED.value),
            ("Pospuestas", "pospuestas"),
        ], "todas")
        self.task_filter.changed.connect(lambda _value: self.refresh_task_list())
        self.task_search = QLineEdit()
        self.task_search.setPlaceholderText("Buscar tarea o curso...")
        self.task_search.setAccessibleName("Buscar tareas")
        self.task_search.textChanged.connect(self._schedule_task_search_refresh)
        self.task_sort = QComboBox()
        for text, value in (("Por fecha", "fecha"), ("Por curso", "curso"), ("Por estado", "estado")):
            self.task_sort.addItem(text, value)
        self.task_sort.currentIndexChanged.connect(self.refresh_task_list)
        filters.addWidget(self.task_search, 1)
        filters.addWidget(self.task_sort)
        self.task_list_container = QWidget()
        self.task_list_layout = QVBoxLayout(self.task_list_container)
        self.task_list_layout.setContentsMargins(0, 0, 0, 0)
        self.task_list_layout.setSpacing(12)
        self.task_scroll = self._scroll_area(self.task_list_container)
        self.task_count_label = QLabel("")
        self.task_count_label.setObjectName("muted")
        left_layout.addWidget(self.task_filter)
        left_layout.addLayout(filters)
        left_layout.addWidget(self.task_scroll, 1)
        left_layout.addWidget(self.task_count_label)

        self.task_detail = DetailPanel()
        self.task_detail.setFixedWidth(320)
        self.detail_chip = StatusChip("Sin seleccionar", "pending")
        self.detail_title = QLabel("Selecciona una tarea")
        self.detail_title.setObjectName("detailTitle")
        self.detail_course = QLabel("")
        self.detail_date = QLabel("")
        self.detail_status = QLabel("")
        for label in (self.detail_title, self.detail_course, self.detail_date, self.detail_status):
            label.setWordWrap(True)
        self.open_button = PrimaryButton("Abrir campus", self.icons.icon("external"))
        self.open_button.clicked.connect(self.open_selected)
        self.snooze_button = SecondaryButton("Posponer", self.icons.icon("clock"))
        self.snooze_button.setAccessibleName("Posponer recordatorio")
        self.snooze_button.setToolTip("Elegir cuando recordar esta tarea")
        self.snooze_menu = QMenu(self.snooze_button)
        for label, days in (("Recordar manana", 1), ("Recordar en 3 dias", 3), ("Recordar en 1 semana", 7)):
            action = QAction(label, self.snooze_menu)
            action.triggered.connect(lambda _checked=False, snooze_days=days: self.snooze_selected(snooze_days))
            self.snooze_menu.addAction(action)
        self.snooze_button.setMenu(self.snooze_menu)
        self.task_detail.layout.addWidget(self.detail_chip)
        self.task_detail.layout.addWidget(self.detail_title)
        self.task_detail.layout.addWidget(self.detail_course)
        self.task_detail.layout.addWidget(self.detail_date)
        self.task_detail.layout.addWidget(self.detail_status)
        self.task_detail.layout.addWidget(self.open_button)
        self.task_detail.layout.addWidget(self.snooze_button)
        self.task_detail.layout.addStretch(1)

        layout.addWidget(left, 1)
        layout.addWidget(self.task_detail)
        return view

    def _build_cursos_view(self) -> QWidget:
        view = QWidget()
        layout = QHBoxLayout(view)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(14)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        course_filters = QHBoxLayout()
        self.course_search = QLineEdit()
        self.course_search.setPlaceholderText("Buscar curso...")
        self.course_search.setAccessibleName("Buscar cursos")
        self.course_search.textChanged.connect(self._schedule_course_search_refresh)
        self.course_filter = QComboBox()
        for text, value in (("Todos", "todos"), ("Con pendientes", "con_pendientes"), ("Sin pendientes", "sin_pendientes")):
            self.course_filter.addItem(text, value)
        self.course_filter.currentIndexChanged.connect(self.refresh_course_list)
        sync_courses = PrimaryButton("Sincronizar", self.icons.icon("refresh"))
        sync_courses.setMaximumWidth(150)
        sync_courses.clicked.connect(self.sync_now)
        course_filters.addWidget(self.course_search, 1)
        course_filters.addWidget(self.course_filter)
        course_filters.addWidget(sync_courses)
        self.course_cards_container = QWidget()
        self.course_cards_layout = QGridLayout(self.course_cards_container)
        self.course_cards_layout.setContentsMargins(0, 0, 0, 0)
        self.course_cards_layout.setHorizontalSpacing(14)
        self.course_cards_layout.setVerticalSpacing(14)
        self.course_cards_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.course_scroll = self._scroll_area(self.course_cards_container)
        self.course_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.course_count_label = QLabel("")
        self.course_count_label.setObjectName("muted")
        left_layout.addLayout(course_filters)
        left_layout.addWidget(self.course_scroll, 1)
        left_layout.addWidget(self.course_count_label)

        self.course_detail = DetailPanel()
        self.course_detail.setFixedWidth(320)
        self.course_detail_title = QLabel("Selecciona un curso")
        self.course_detail_title.setObjectName("detailTitle")
        self.course_detail_info = QLabel("")
        self.course_detail_info.setWordWrap(True)
        self.course_tasks_label = QLabel("")
        self.course_tasks_label.setWordWrap(True)
        open_course = PrimaryButton("Abrir Moodle", self.icons.icon("external"))
        open_course.clicked.connect(lambda _checked=False: self.navigator.open_campus_home())
        view_tasks = SecondaryButton("Ver tareas del curso", self.icons.icon("tasks"))
        view_tasks.clicked.connect(self._show_selected_course_tasks)
        self.course_detail.layout.addWidget(self.course_detail_title)
        self.course_detail.layout.addWidget(self.course_detail_info)
        self.course_detail.layout.addWidget(self.course_tasks_label)
        self.course_detail.layout.addWidget(open_course)
        self.course_detail.layout.addWidget(view_tasks)
        self.course_detail.layout.addStretch(1)

        layout.addWidget(left, 1)
        layout.addWidget(self.course_detail)
        return view

    def _build_ajustes_view(self) -> QWidget:
        view = QWidget()
        layout = QHBoxLayout(view)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(20)
        nav = QListWidget()
        nav.setObjectName("settingsNav")
        nav.setFixedWidth(210)
        nav.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.settings_stack = QStackedWidget()
        for title, page in (
            ("Perfil y Campus", self._settings_profile_page()),
            ("Sincronizacion", self._settings_sync_page()),
            ("Notificaciones", self._settings_notifications_page()),
            ("Privacidad y Datos", self._settings_privacy_page()),
            ("Apariencia", self._settings_appearance_page()),
            ("Acerca de", self._settings_about_page()),
        ):
            nav.addItem(title)
            self.settings_stack.addWidget(page)
        nav.currentRowChanged.connect(self.settings_stack.setCurrentIndex)
        nav.setCurrentRow(0)
        layout.addWidget(nav)
        layout.addWidget(self.settings_stack, 1)
        return view

    def _settings_profile_page(self) -> QWidget:
        page = self._settings_page("Perfil y Campus", "Cuenta conectada a Campus Moodle")
        self.profile_summary = QLabel("")
        self.profile_summary.setObjectName("settingsCard")
        change = PrimaryButton("Cambiar perfil", self.icons.icon("user_switch"))
        change.setMaximumWidth(180)
        change.clicked.connect(self.change_profile)
        logout = SecondaryButton("Cerrar sesion local", self.icons.icon("logout"))
        logout.setObjectName("dangerButton")
        logout.setMaximumWidth(210)
        logout.clicked.connect(self.logout_local)
        page.layout().addWidget(self.profile_summary)
        page.layout().addWidget(change)
        page.layout().addWidget(logout)
        return page

    def _settings_sync_page(self) -> QWidget:
        page = self._settings_page("Sincronizacion", "Controla frecuencia y arranque automatico")
        sync_toggle = ToggleSwitch(self.settings.setting_bool("sync_on_start", True))
        sync_toggle.toggled_value.connect(lambda v: self.settings.set_setting_bool("sync_on_start", v))
        self.start_windows_check = ToggleSwitch(self.autostart.enabled())
        self.start_windows_check.toggled_value.connect(self._set_autostart_from_settings)
        self.interval_combo = QComboBox()
        for text, value in (("Cada 1 hora", 3600), ("Cada 6 horas", 21600), ("Una vez al dia", 86400)):
            self.interval_combo.addItem(text, value)
        self._select_combo_value(self.interval_combo, self.settings.sync_interval_seconds())
        self.interval_combo.currentIndexChanged.connect(self._interval_changed)
        page.layout().addWidget(SettingsRow("Sincronizar al iniciar la app", "Consulta Moodle cada vez que abres ChivaTask", sync_toggle))
        page.layout().addWidget(SettingsRow("Iniciar con Windows", "ChivaTask arranca en la bandeja del sistema al encender el equipo", self.start_windows_check))
        page.layout().addWidget(SettingsRow("Intervalo de sincronizacion", "Frecuencia de consulta automatica en segundo plano", self.interval_combo))
        page.layout().addWidget(PrimaryButton("Sincronizar", self.icons.icon("refresh")))
        page.layout().itemAt(page.layout().count() - 1).widget().clicked.connect(self.sync_now)
        self.sync_history = QLabel("")
        self.sync_history.setObjectName("settingsCard")
        page.layout().addWidget(self.sync_history)
        return page

    def _settings_notifications_page(self) -> QWidget:
        page = self._settings_page("Notificaciones", "Alertas de Windows para cambios importantes")
        for key, text, default in (
            ("notify_new_tasks", "Notificar tareas nuevas", True),
            ("notify_overdue_tasks", "Notificar tareas vencidas", True),
            ("notify_due_changes", "Notificar cambios de fecha", True),
        ):
            toggle = ToggleSwitch(self.settings.setting_bool(key, default))
            toggle.toggled_value.connect(lambda checked, setting_key=key: self.settings.set_setting_bool(setting_key, checked))
            page.layout().addWidget(SettingsRow(text, "Controla esta alerta local de Windows", toggle))
        self.notif_mode = QComboBox()
        for text, value in (("Solo cambios nuevos", "solo_nuevos"), ("Resumen diario", "resumen_diario"), ("Silencioso", "silencioso")):
            self.notif_mode.addItem(text, value)
        self._select_combo_value(self.notif_mode, self.settings.notification_mode())
        self.notif_mode.currentIndexChanged.connect(lambda: self.settings.set_notification_mode(self.notif_mode.currentData()))
        page.layout().addWidget(SettingsRow("Modo de notificaciones", "Como y cuando enviar las alertas del sistema", self.notif_mode))
        test = SecondaryButton("Enviar notificacion de prueba", self.icons.icon("bell"))
        test.clicked.connect(lambda: self.notifier.notify_changed(self.tasks[:1]) if self.tasks else self.status_pill.setText("No hay tareas para probar"))
        page.layout().addWidget(test)
        return page

    def _settings_privacy_page(self) -> QWidget:
        page = self._settings_page("Privacidad y Datos Locales", "ChivaTask guarda todo en este equipo")
        data = QLabel(f"Credenciales: Windows Credential Manager\nCache local: SQLite\nRuta: {self.repository.path}\nDatos externos: nada sale de este equipo")
        data.setObjectName("settingsCard")
        data.setWordWrap(True)
        open_folder = SecondaryButton("Abrir carpeta de datos")
        open_folder.clicked.connect(self.open_data_folder)
        clear = SecondaryButton("Limpiar cache local")
        clear.setObjectName("dangerButton")
        clear.clicked.connect(self.clear_cache_local)
        page.layout().addWidget(data)
        page.layout().addWidget(open_folder)
        page.layout().addWidget(clear)
        return page

    def _settings_appearance_page(self) -> QWidget:
        page = self._settings_page("Apariencia", "Personaliza el aspecto visual de ChivaTask")
        self.appearance_theme_toggle = self._new_theme_toggle()
        animations = ToggleSwitch(self.settings.setting_bool("animations_enabled", True))
        animations.toggled_value.connect(self._set_animations_enabled)
        page.layout().addWidget(SettingsRow("Modo oscuro", "Alterna entre tema claro y oscuro", self.appearance_theme_toggle))
        page.layout().addWidget(SettingsRow("Animaciones sutiles", "Transiciones y efectos de entrada y salida", animations))
        return page

    def _settings_about_page(self) -> QWidget:
        page = self._settings_page("Acerca de", "Tu campus academico, sin excusas.")
        about = QLabel(
            "ChivaTask es una aplicacion local para gestionar pendientes academicos.\n\n"
            "Stack real: Python 3.11+, PySide6 / Qt Widgets, Moodle REST API oficial, "
            "SQLite local y Windows Credential Manager.\n\n"
            "Herramienta personal no oficial. No tiene afiliacion ni respaldo institucional de UPH."
        )
        about.setObjectName("settingsCard")
        about.setWordWrap(True)
        page.layout().addWidget(about)
        return page

    def _settings_page(self, title: str, subtitle: str) -> QWidget:
        page = QWidget()
        page.setMaximumWidth(840)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignTop)
        title_label = QLabel(title)
        title_label.setObjectName("detailTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("subtitle")
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        layout.addSpacing(8)
        return page

    def _section_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("sectionTitle")
        return label

    def _scroll_area(self, widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setObjectName("flatScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(widget)
        return scroll

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
            elif child_layout:
                self._clear_layout(child_layout)

    def _configure_table(self, table: QTableWidget) -> None:
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(42)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)

    def ensure_login_and_sync(self) -> None:
        if not self.credentials.has_credentials():
            if self.settings.onboarding_completed():
                accepted = LoginDialog(self.credentials, self).exec() == QDialog.Accepted
            else:
                accepted = OnboardingDialog(self.credentials, self).exec() == QDialog.Accepted
                if accepted:
                    self.awaiting_onboarding_sync = True
            if not accepted:
                self._set_status("Credenciales pendientes", "pending")
                return
            if self.awaiting_onboarding_sync:
                self.sync_now()
                return
        if self.settings.setting_bool("sync_on_start", True):
            self.sync_now()

    def sync_now(self) -> None:
        if self.worker_thread and self.worker_thread.isRunning():
            return
        self.syncing = True
        self._set_data_state("loading")
        self._set_status("Sincronizando", "syncing")
        self.sync_button.setEnabled(False)
        self.worker_thread = QThread(self)
        self.worker = SyncWorker(self.run_sync)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.sync_finished.emit)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(lambda: setattr(self, "worker", None))
        self.worker_thread.start()

    def _sync_finished(self, result: SyncResult) -> None:
        self.syncing = False
        self.sync_button.setEnabled(True)
        self.refresh_from_cache()
        if result.ok:
            self.api_status = "ok"
            self.last_error_code = None
            if self.awaiting_onboarding_sync:
                self.settings.set_onboarding_completed(True)
                self.awaiting_onboarding_sync = False
            self.error_banner.hide()
            self._set_data_state("success")
            self._set_status("Sincronizado", "ok")
            self._notify_changed(result.changed_pending)
        else:
            self.awaiting_onboarding_sync = False
            self.api_status = "error"
            self.last_error_code = result.error_code
            self.error_label.setText(f"Sin conexion a Moodle - Mostrando datos en cache ({result.error_code})")
            self.error_banner.show()
            self._set_data_state("offline-cache" if result.pending_count or result.course_count else "recoverable-error")
            self._set_status("Sin conexion", "error")
            if result.error_code == "invalidlogin":
                LoginDialog(self.credentials, self).exec()

    def _notify_changed(self, tasks: list[Task]) -> None:
        if not tasks:
            return
        mode = self.settings.notification_mode()
        if mode == "silencioso":
            self.repository.mark_notified(tasks)
            return
        if mode == "resumen_diario":
            today = date.today().isoformat()
            if self.repository.get_state("last_daily_notification_date") == today:
                return
            self.repository.set_state("last_daily_notification_date", today)
        filtered = []
        for task in tasks:
            bucket = classify_task(task)
            if bucket == TaskBucket.OVERDUE and not self.settings.setting_bool("notify_overdue_tasks", True):
                continue
            if bucket != TaskBucket.OVERDUE and not self.settings.setting_bool("notify_new_tasks", True):
                continue
            filtered.append(task)
        if filtered:
            self.notifier.notify_changed(filtered)
            self.repository.mark_notified(filtered)

    def refresh_from_cache(self) -> None:
        self.tasks = self.queries.pending_sorted()
        counts = self.queries.task_counts()
        courses = self.queries.course_count()
        self.pending_card.update_value(str(counts["todas"]), "Pendientes")
        self.overdue_card.update_value(str(counts["vencidas"]), "Vencidas")
        self.week_card.update_value(str(len(self.queries.tasks_due_within(7))), "Esta semana")
        self.course_card.update_value(str(courses), "Cursos activos")
        self.nav_buttons["tareas"].setText(f"Tareas   {counts['todas']}")
        self.nav_buttons["cursos"].setText(f"Cursos   {courses}")
        last = self.queries.last_successful_sync()
        if last and self.api_status != "error":
            self._set_status("Sincronizado", "ok")
        self.health_label.setText(
            f"Moodle API: {'sin conexion' if self.api_status == 'error' else 'conectado'}\n"
            f"Cache local: SQLite activo\nCredenciales: Credential Manager"
        )
        self._refresh_profile_summary()
        self.refresh_inicio_sections()
        self.refresh_task_list()
        self.refresh_course_list()
        self._refresh_sync_history()

    def _schedule_task_search_refresh(self, *_args) -> None:
        self.task_search_timer.start()

    def _schedule_course_search_refresh(self, *_args) -> None:
        self.course_search_timer.start()

    def _effective_visual_mode(self) -> str:
        return self.settings.visual_mode()

    def _apply_visual_preferences(self) -> None:
        set_animations_enabled(self.settings.setting_bool("animations_enabled", True))
        mode = self._effective_visual_mode()
        self.setStyleSheet(app_stylesheet(mode))
        for toggle in getattr(self, "theme_toggles", []):
            toggle.set_visual_mode(mode)
        self._apply_responsive_layout()

    def _set_visual_mode(self, mode: str) -> None:
        self.settings.set_visual_mode(mode)
        self._apply_visual_preferences()

    def _set_animations_enabled(self, enabled: bool) -> None:
        self.settings.set_setting_bool("animations_enabled", enabled)
        set_animations_enabled(enabled)

    def _new_theme_toggle(self) -> ThemeToggleButton:
        toggle = ThemeToggleButton(self.icons.icon("moon"), self.icons.icon("sun"), self._effective_visual_mode())
        toggle.changed.connect(self._set_visual_mode)
        self.theme_toggles.append(toggle)
        return toggle

    def _apply_responsive_layout(self) -> None:
        compact = self.width() < 1180
        if hasattr(self, "sidebar"):
            self.sidebar.setFixedWidth(176 if compact else 220)
        for panel_name in ("home_side", "task_detail", "course_detail"):
            panel = getattr(self, panel_name, None)
            if panel is not None:
                panel.setVisible(not compact)

    def refresh_inicio_sections(self) -> None:
        if not hasattr(self, "home_sections_layout"):
            return
        today = date.today()
        dias = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
        meses = [
            "enero",
            "febrero",
            "marzo",
            "abril",
            "mayo",
            "junio",
            "julio",
            "agosto",
            "septiembre",
            "octubre",
            "noviembre",
            "diciembre",
        ]
        self.greeting_date.setText(f"{dias[today.weekday()]}, {today.day} de {meses[today.month - 1]} {today.year}")
        username = (getattr(self.credentials, "get_username", lambda: None)() or "estudiante").split("@")[0]
        self.greeting_title.setText(f"{self._greeting_for_hour(datetime.now().hour)}, {username}")
        next_task = self.queries.next_deadline()
        self._next_deadline_task = next_task
        if next_task:
            self.next_deadline_card.show()
            self.next_deadline_text.setText(
                f"PROXIMA ENTREGA - {relative_due_text(next_task.due_at)}\n"
                f"{next_task.name}\n{next_task.course_shortname} - {unix_to_local_text(next_task.due_at)}"
            )
        else:
            self.next_deadline_card.hide()
        self._clear_layout(self.home_sections_layout)
        sections = [
            ("Vencidas", self.queries.overdue_tasks(), "No hay tareas vencidas."),
            ("Esta semana", self.queries.tasks_due_within(7), "No hay entregas esta semana."),
            ("Sin fecha", self.queries.undated_tasks(), "No hay tareas sin fecha."),
        ]
        for title, tasks, empty in sections:
            self.home_sections_layout.addWidget(self._section_title(f"{title}  {len(tasks)}"))
            if tasks:
                for task in tasks[:4]:
                    card = TaskRowCard(task, compact=True)
                    card.selected.connect(self._open_task_from_card)
                    self.home_sections_layout.addWidget(card)
            else:
                self.home_sections_layout.addWidget(EmptyState(empty, "", self.icons.icon("check")))
        self.home_sections_layout.addStretch(1)
        progress = self.queries.global_progress()
        self.progress_ring.update_value(progress["percent"], f"{progress['submitted']} de {progress['total']} actividades")
        self.calendar.set_month(today.year, today.month, self.queries.calendar_marks(today.year, today.month))

    def refresh_task_list(self) -> None:
        if not hasattr(self, "task_list_layout"):
            return
        value = self.task_filter.currentData()
        bucket = None if value in ("todas", "pospuestas") else value
        if value == "urgentes":
            base = self.queries.urgent_tasks()
            query = self.task_search.text().strip().lower()
            self.filtered_tasks = [
                task for task in base
                if not query or query in task.name.lower() or query in task.course_shortname.lower() or query in task.course_fullname.lower()
            ]
        else:
            self.filtered_tasks = self.queries.pending_filtered(
                bucket=bucket,
                search=self.task_search.text(),
                sort_by=self.task_sort.currentData(),
                snoozed_only=value == "pospuestas",
            )
        self._clear_layout(self.task_list_layout)
        self._task_by_id = {task.assignment_id: task for task in self.filtered_tasks}
        if not self.filtered_tasks:
            if self.tasks:
                self._set_data_state("filtered-empty")
                self.task_list_layout.addWidget(EmptyState("Sin resultados", "No hay tareas para este filtro.", self.icons.icon("tasks")))
            else:
                self._set_data_state("empty")
                self.task_list_layout.addWidget(EmptyState("Sin tareas", "No hay tareas pendientes en cache.", self.icons.icon("tasks")))
        for course, items in self.queries.grouped_by_course(self.filtered_tasks):
            group = QFrame()
            group.setObjectName("taskGroup")
            group_layout = QVBoxLayout(group)
            group_layout.setContentsMargins(0, 0, 0, 0)
            group_layout.setSpacing(0)
            header = QLabel(f"{course}  {len(items)}")
            header.setObjectName("taskGroupHeader")
            group_layout.addWidget(header)
            for task in items:
                card = TaskRowCard(task)
                card.selected.connect(self._select_task)
                group_layout.addWidget(card)
            self.task_list_layout.addWidget(group)
        self.task_list_layout.addStretch(1)
        counts = self.queries.task_counts()
        self.task_count_label.setText(
            f"{len(self.filtered_tasks)} de {counts['todas']} tareas"
            + (f" - {counts['pospuestas']} pospuestas" if counts["pospuestas"] else "")
        )

    def refresh_course_list(self) -> None:
        if not hasattr(self, "course_cards_layout"):
            return
        summaries = self.queries.course_summaries()
        query = self.course_search.text().strip().lower()
        mode = self.course_filter.currentData()
        filtered = []
        for summary in summaries:
            pending = int(summary["pending"])
            haystack = f"{summary['shortname']} {summary['fullname']}".lower()
            if query and query not in haystack:
                continue
            if mode == "con_pendientes" and pending == 0:
                continue
            if mode == "sin_pendientes" and pending > 0:
                continue
            filtered.append(summary)
        self.course_summaries = filtered
        self._clear_layout(self.course_cards_layout)
        available_width = self.course_scroll.viewport().width() if hasattr(self, "course_scroll") else 0
        columns = 2 if available_width >= 980 else 1
        if not filtered:
            self.course_cards_layout.addWidget(EmptyState("Sin cursos", "No hay cursos para este filtro.", self.icons.icon("courses")), 0, 0, 1, columns)
        for index, summary in enumerate(filtered):
            card = CourseCard(summary)
            card.selected.connect(self._select_course_summary)
            card.view_tasks.connect(self._show_course_tasks_from_summary)
            self.course_cards_layout.addWidget(card, index // columns, index % columns)
        self.course_count_label.setText(f"{len(filtered)} de {len(summaries)} cursos")

    def _fill_task_table(self, table: QTableWidget, tasks: list[Task]) -> None:
        table.setRowCount(len(tasks))
        for row, task in enumerate(tasks):
            bucket = classify_task(task)
            values = [task.course_shortname or task.course_fullname, task.name, unix_to_local_text(task.due_at), STATUS_TEXT[bucket]]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, task.assignment_id)
                table.setItem(row, col, item)

    def _open_next_deadline(self) -> None:
        task = getattr(self, "_next_deadline_task", None)
        if task:
            self._open_task_from_card(task)

    def _open_task_from_card(self, task: Task) -> None:
        self.navigate("tareas")
        self._select_task(task)

    def _select_urgent_task(self) -> None:
        rows = self.urgent_table.selectionModel().selectedRows()
        if not rows:
            return
        assignment_id = self.urgent_table.item(rows[0].row(), 0).data(Qt.UserRole)
        task = next((item for item in self.tasks if item.assignment_id == assignment_id), None)
        if task:
            self.navigate("tareas")
            self._select_task(task)

    def _task_tree_selection_changed(self) -> None:
        selected = self.task_tree.selectedItems()
        if not selected:
            self.selected_task = None
            self._render_task_detail(None)
            return
        assignment_id = selected[0].data(0, Qt.UserRole)
        self._select_task(self._task_by_id.get(assignment_id))

    def _select_task(self, task: Task | None) -> None:
        self.selected_task = task
        self._render_task_detail(task)

    def _render_task_detail(self, task: Task | None) -> None:
        if not task:
            self.detail_chip.setText("Sin seleccionar")
            self.detail_title.setText("Selecciona una tarea")
            self.detail_course.setText("")
            self.detail_date.setText("")
            self.detail_status.setText("")
            return
        bucket = classify_task(task)
        self._set_chip(self.detail_chip, STATUS_TEXT[bucket], CHIP_VARIANT[bucket])
        self.detail_title.setText(task.name)
        self.detail_course.setText(task.course_fullname or task.course_shortname)
        self.detail_date.setText(f"Fecha: {unix_to_local_text(task.due_at)}")
        snooze = f"\nPospuesta hasta: {unix_to_local_text(task.snoozed_until)}" if task.snoozed_until else ""
        self.detail_status.setText(f"Estado: {STATUS_TEXT[bucket]}{snooze}")

    def _course_selection_changed(self) -> None:
        rows = self.course_table.selectionModel().selectedRows()
        if not rows:
            self.selected_course = None
            return
        course_id = self.course_table.item(rows[0].row(), 0).data(Qt.UserRole)
        self.selected_course = next((item for item in self.course_summaries if item["course_id"] == course_id), None)
        self._render_course_detail()

    def _select_course_summary(self, summary: dict[str, object]) -> None:
        self.selected_course = summary
        self._render_course_detail()

    def _render_course_detail(self) -> None:
        course = self.selected_course
        if not course:
            self.course_detail_title.setText("Selecciona un curso")
            self.course_detail_info.setText("")
            self.course_tasks_label.setText("")
            return
        total = int(course["total"])
        submitted = int(course["submitted"])
        progress = int((submitted / total) * 100) if total else 0
        self.course_detail_title.setText(str(course["shortname"]))
        self.course_detail_info.setText(
            f"{course['fullname']}\nPendientes: {course['pending']}\nEntregadas: {submitted} de {total}\nProgreso: {progress}%"
        )
        tasks: list[Task] = course["tasks"]  # type: ignore[assignment]
        preview = "\n".join(f"- {task.name} ({STATUS_TEXT[classify_task(task)]})" for task in tasks[:5])
        self.course_tasks_label.setText(preview or "Todo entregado. Sin pendientes.")

    def _show_selected_course_tasks(self) -> None:
        if not self.selected_course:
            return
        self.navigate("tareas")
        self.task_search.setText(str(self.selected_course["shortname"]))

    def _show_course_tasks_from_summary(self, summary: dict[str, object]) -> None:
        self.selected_course = summary
        self._show_selected_course_tasks()

    def navigate(self, key: str) -> None:
        index = {"inicio": 0, "tareas": 1, "cursos": 2, "ajustes": 3}[key]
        self.views.setCurrentIndex(index)
        titles = {
            "inicio": ("Tu campus bajo control", "Resumen sincronizado desde Moodle"),
            "tareas": ("Tareas pendientes", "Actividades sin entrega registrada"),
            "cursos": ("Cursos activos", "Materias sincronizadas desde Moodle"),
            "ajustes": ("Ajustes", "Controla como ChivaTask sincroniza y protege tus datos"),
        }
        self.title_label.setText(titles[key][0])
        self.subtitle_label.setText(titles[key][1])
        for nav_key, button in self.nav_buttons.items():
            button.setObjectName("navItemActive" if nav_key == key else "navItem")
            button.style().unpolish(button)
            button.style().polish(button)
        self.footer.setVisible(key in {"inicio", "tareas"})

    def open_command_palette(self) -> None:
        CommandPalette(self, self.tasks, self.navigate, self._select_task).exec()

    def open_selected(self) -> None:
        if self.selected_task and self.selected_task.url:
            opened = self.navigator.open_url(self.selected_task.url)
            if not opened:
                QMessageBox.warning(self, "URL no permitida", "Solo se pueden abrir enlaces seguros del campus.")
            return
        self.navigator.open_campus_home()

    def snooze_selected(self, days: int = 1) -> None:
        if not self.selected_task:
            return
        until = now_ts() + int(timedelta(days=days).total_seconds())
        self.repository.snooze(self.selected_task.assignment_id, until)
        self.refresh_from_cache()
        self._set_status(f"Recordatorio pospuesto {days} dia(s)", "pending")

    def change_profile(self) -> None:
        try:
            self.credentials.clear_token()
        except CredentialError as exc:
            QMessageBox.critical(self, "Credential Manager", str(exc))
            return
        if LoginDialog(self.credentials, self).exec() == QDialog.Accepted:
            self.sync_now()

    def logout_local(self) -> None:
        modal = ConfirmModal(
            "Cerrar sesion local",
            "Esto elimina credenciales, token y cache academica de este equipo. No borra nada en Moodle.",
            self,
        )
        cancel = SecondaryButton("Cancelar")
        cancel.clicked.connect(modal.reject)
        logout = PrimaryButton("Cerrar sesion")
        logout.setObjectName("dangerPrimaryButton")
        logout.clicked.connect(modal.accept)
        modal.layout.addWidget(cancel)
        modal.layout.addWidget(logout)
        if modal.exec() == QDialog.Accepted:
            try:
                if hasattr(self.credentials, "clear_all"):
                    self.credentials.clear_all()
                else:
                    self.credentials.clear_token()
            except CredentialError as exc:
                QMessageBox.critical(self, "Credential Manager", str(exc))
                return
            self.repository.clear_all_local_cache()
            self.settings.set_onboarding_completed(False)
            self.refresh_from_cache()
            self._set_status("Sesion local cerrada", "pending")
            QTimer.singleShot(100, self.ensure_login_and_sync)

    def clear_cache_local(self) -> None:
        modal = ConfirmModal(
            "Limpiar cache local",
            "Se eliminaran cursos, tareas y estado de notificaciones. Credenciales y ajustes se conservan.",
            self,
        )
        cancel = SecondaryButton("Cancelar")
        cancel.clicked.connect(modal.reject)
        clear = PrimaryButton("Limpiar cache")
        clear.setObjectName("dangerPrimaryButton")
        clear.clicked.connect(modal.accept)
        modal.layout.addWidget(cancel)
        modal.layout.addWidget(clear)
        if modal.exec() == QDialog.Accepted:
            self.repository.clear_academic_cache()
            self.refresh_from_cache()
            self._set_status("Cache local eliminada", "pending")

    def open_data_folder(self) -> None:
        path = self.repository.path
        if path == ":memory:":
            return
        opened = self.navigator.open_folder(path.parent)
        if not opened:
            QMessageBox.warning(self, "Carpeta no disponible", "No se pudo abrir la carpeta de datos local.")

    def _set_status(self, text: str, variant: str) -> None:
        self.status_pill.setText(text)
        self.status_pill.setObjectName(
            {
                "ok": "statusOk",
                "error": "statusError",
                "syncing": "statusSyncing",
                "pending": "statusPending",
            }[variant]
        )
        self.status_pill.style().unpolish(self.status_pill)
        self.status_pill.style().polish(self.status_pill)

    def _set_data_state(self, state: str) -> None:
        labels = {
            "loading": "Cargando datos",
            "success": "Datos actualizados",
            "empty": "Sin tareas pendientes",
            "filtered-empty": "Sin resultados para el filtro",
            "offline-cache": "Sin conexion, usando cache",
            "recoverable-error": "Error recuperable de sincronizacion",
            "blocking-error": "Accion bloqueada",
        }
        if hasattr(self, "data_state_label"):
            self.data_state_label.setText(labels.get(state, state))
            self.data_state_label.setProperty("dataState", state)

    def _set_chip(self, chip: StatusChip, text: str, variant: str) -> None:
        chip.setText(text)
        chip.setObjectName(f"chip-{variant}")
        chip.style().unpolish(chip)
        chip.style().polish(chip)

    def _greeting_for_hour(self, hour: int) -> str:
        if 5 <= hour < 12:
            return "Buenos dias"
        if 12 <= hour < 18:
            return "Buenas tardes"
        return "Buenas noches"

    def _refresh_profile_summary(self) -> None:
        if not hasattr(self, "profile_summary"):
            return
        username = getattr(self.credentials, "get_username", lambda: None)() or "Sin perfil conectado"
        self.profile_summary.setText(f"Usuario: {username}\nEstado: {'Conectado a Campus Moodle' if self.credentials.has_credentials() else 'Pendiente'}")
        if hasattr(self.profile_button, "menu"):
            self.profile_button.menu.refresh_user()

    def _refresh_sync_history(self) -> None:
        if not hasattr(self, "sync_history"):
            return
        last = self.repository.get_state("last_successful_sync_at")
        error = self.repository.get_state("last_error_code")
        self.sync_history.setText(
            "Historial de sincronizacion\n"
            f"Ultima correcta: {unix_to_local_text(int(last)) if last else 'Sin registro'}\n"
            f"Ultimo error: {error or 'Ninguno'}"
        )

    def _interval_changed(self) -> None:
        seconds = int(self.interval_combo.currentData())
        self.settings.set_sync_interval_seconds(seconds)
        self.timer.setInterval(seconds * 1000)

    def _set_autostart_from_settings(self, enabled: bool) -> None:
        self.autostart.set_enabled(enabled)
        if hasattr(self, "start_windows_check"):
            self.start_windows_check.setChecked(enabled)

    def _select_combo_value(self, combo: QComboBox, value) -> None:
        for index in range(combo.count()):
            if combo.itemData(index) == value:
                combo.setCurrentIndex(index)
                return

    def show_normal(self) -> None:
        self.tray.reset_background_message()
        self.show()
        self.raise_()
        self.activateWindow()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_responsive_layout()
        if hasattr(self, "course_cards_layout"):
            QTimer.singleShot(0, self.refresh_course_list)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.tray.is_visible():
            event.ignore()
            self.hide()
            self.tray.show_background_message()
        else:
            super().closeEvent(event)


class OnboardingDialog(BaseModal):
    def __init__(self, credentials: CredentialRepository, parent: QWidget | None = None) -> None:
        super().__init__("Bienvenido a ChivaTask", parent)
        self.credentials = credentials
        self.setMinimumWidth(440)
        self.stack = QStackedWidget()
        self.stack.addWidget(self._welcome_page())
        self.stack.addWidget(self._login_page())
        self.stack.addWidget(self._ready_page())
        self.layout.addWidget(self.stack)

    def _welcome_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(BrandLockup())
        title = QLabel("Tu campus academico, sin excusas.")
        title.setObjectName("detailTitle")
        text = QLabel("ChivaTask detecta tareas sin entrega en Moodle, sincroniza en segundo plano y te avisa cuando hay cambios importantes.")
        text.setWordWrap(True)
        start = PrimaryButton("Comenzar")
        start.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        layout.addWidget(title)
        layout.addWidget(text)
        layout.addWidget(start)
        return page

    def _login_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.username = QLineEdit()
        self.username.setPlaceholderText("usuario@uph.edu.hn")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Contrasena del campus")
        self.password.setEchoMode(QLineEdit.Password)
        info = QLabel("Tus credenciales se guardan en Windows Credential Manager, no en archivos del proyecto.")
        info.setWordWrap(True)
        connect = PrimaryButton("Conectar")
        connect.clicked.connect(self._save_credentials)
        back = SecondaryButton("Volver")
        back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        layout.addWidget(QLabel("Conecta tu campus"))
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(info)
        layout.addWidget(connect)
        layout.addWidget(back)
        return page

    def _ready_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel("Todo listo")
        title.setObjectName("detailTitle")
        text = QLabel("La primera sincronizacion se ejecutara al entrar a ChivaTask.")
        text.setWordWrap(True)
        done = PrimaryButton("Ir a ChivaTask")
        done.clicked.connect(self.accept)
        layout.addWidget(title)
        layout.addWidget(text)
        layout.addWidget(done)
        return page

    def _save_credentials(self) -> None:
        username = self.username.text().strip()
        password = self.password.text()
        if not username or not password:
            QMessageBox.warning(self, "Datos incompletos", "Ingresa usuario y contrasena.")
            return
        try:
            self.credentials.save_credentials(username, password)
            self.credentials.clear_token()
        except CredentialError as exc:
            QMessageBox.critical(self, "Credential Manager", str(exc))
            return
        self.stack.setCurrentIndex(2)


class CommandPalette(BaseModal):
    def __init__(self, parent: MainWindow, tasks: list[Task], navigate, select_task) -> None:
        super().__init__("Buscar en ChivaTask", parent)
        self.tasks = tasks
        self.navigate = navigate
        self.select_task = select_task
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar vista o tarea...")
        self.results = QListWidget()
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(250)
        self.search_timer.timeout.connect(self._refresh)
        self.search.textChanged.connect(lambda _text: self.search_timer.start())
        self.results.itemActivated.connect(self._activate)
        self.layout.addWidget(self.search)
        self.layout.addWidget(self.results)
        self.setMinimumWidth(520)
        self._refresh()

    def _refresh(self) -> None:
        self.results.clear()
        query = self.search.text().strip().lower()
        for key, label in (("inicio", "Ir a Inicio"), ("tareas", "Ir a Tareas"), ("cursos", "Ir a Cursos"), ("ajustes", "Ir a Ajustes")):
            if not query or query in label.lower():
                item = QListWidgetItem(label)
                item.setData(Qt.UserRole, ("nav", key))
                self.results.addItem(item)
        for task in self.tasks:
            label = f"{task.course_shortname} - {task.name}"
            if not query or query in label.lower():
                item = QListWidgetItem(label)
                item.setData(Qt.UserRole, ("task", task.assignment_id))
                self.results.addItem(item)

    def _activate(self, item: QListWidgetItem) -> None:
        kind, value = item.data(Qt.UserRole)
        if kind == "nav":
            self.navigate(value)
        else:
            task = next((candidate for candidate in self.tasks if candidate.assignment_id == value), None)
            self.navigate("tareas")
            self.select_task(task)
        self.accept()


STATUS_TEXT = {
    TaskBucket.OVERDUE: "Vencida",
    TaskBucket.UPCOMING: "Sin entrega",
    TaskBucket.UNDATED: "Sin fecha",
    TaskBucket.SUBMITTED: "Entregada",
}

CHIP_VARIANT = {
    TaskBucket.OVERDUE: "overdue",
    TaskBucket.UPCOMING: "pending",
    TaskBucket.UNDATED: "undated",
    TaskBucket.SUBMITTED: "ok",
}
