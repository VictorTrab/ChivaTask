"""Ventana principal Qt: shell visual de ChivaTask y flujos de usuario."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from PySide6.QtCore import QThread, QTimer, Qt, Signal
from PySide6.QtGui import QAction, QCloseEvent, QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
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
from .componentes.shell import NavItem, SearchField, SyncStatusPill, SyncToast
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
    SegmentedControl,
    relative_due_text,
)
from .componentes.tarjetas import DetailPanel, InfoCard, StatCard
from .dialogo_login import LoginDialog
from .animaciones import set_animations_enabled
from .logo import BrandLockup, logo_icon
from .registro_iconos import IconRegistry
from .tema import apply_application_theme
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
        self.task_search_timer = QTimer(self)
        self.task_search_timer.setSingleShot(True)
        self.task_search_timer.setInterval(250)
        self.task_search_timer.timeout.connect(self.refresh_task_list)
        self.course_search_timer = QTimer(self)
        self.course_search_timer.setSingleShot(True)
        self.course_search_timer.setInterval(250)
        self.course_search_timer.timeout.connect(self.refresh_course_list)
        self.sync_relative_timer = QTimer(self)
        self.sync_relative_timer.setInterval(60_000)
        self.sync_relative_timer.timeout.connect(self._refresh_sync_status_detail)

        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(logo_icon())
        self.resize(1240, 760)
        self.setMinimumSize(960, 640)
        self._build_ui()
        self.tray = TrayController(self, self.icons, self.show_normal, self.sync_now)
        self.sync_toast = SyncToast()
        self.sync_toast.setParent(self.content_root)
        self.sync_toast.retry_requested.connect(self.sync_now)
        self.sync_finished.connect(self._sync_finished)

        self.timer = QTimer(self)
        self.timer.setInterval(sync_interval_seconds * 1000)
        self.timer.timeout.connect(self.sync_now)
        self.timer.start()
        self.sync_relative_timer.start()
        self.startup_timer = QTimer(self)
        self.startup_timer.setSingleShot(True)
        self.startup_timer.timeout.connect(self.ensure_startup_sync)
        self.startup_timer.start(300)
        self.refresh_from_cache()

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("appRoot")
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

        self.nav_buttons: dict[str, NavItem] = {}
        for key, icon, text in (
            ("inicio", "home", "Inicio"),
            ("tareas", "tasks", "Tareas"),
            ("cursos", "courses", "Cursos"),
            ("ajustes", "settings", "Ajustes"),
        ):
            button = NavItem(self.icons.icon(icon, "light"), text)
            button.clicked.connect(lambda nav_key=key: self.navigate(nav_key))
            sidebar_layout.addWidget(button)
            self.nav_buttons[key] = button
        sidebar_layout.addStretch(1)
        self.version_label = QLabel("v1.0.0 - IIP-2026")
        self.version_label.setObjectName("sidebarMuted")
        sidebar_layout.addWidget(self.version_label)

        self.content_root = QWidget()
        self.content_root.setObjectName("contentRoot")
        content_layout = QVBoxLayout(self.content_root)
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
        root_layout.addWidget(self.content_root, 1)
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
        self.status_pill = SyncStatusPill(self.icons.icon("check", "brand"))
        self.profile_button = ProfileButton(self.icons, self.credentials, self.change_profile, self.logout_local)
        header.addLayout(title_box)
        header.addStretch(1)
        header.addWidget(self.status_pill)
        header.addWidget(self.profile_button)
        return header

    def _build_error_banner(self) -> QFrame:
        banner = QFrame()
        banner.setObjectName("errorBanner")
        layout = QHBoxLayout(banner)
        layout.setContentsMargins(24, 8, 24, 8)
        self.error_label = QLabel("Sin conexión a Moodle - Mostrando datos en caché")
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
        self.sync_button = PrimaryButton("Sincronizar", self.icons.icon("refresh", "light"))
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
        view.setObjectName("pageRoot")
        layout = QHBoxLayout(view)
        layout.setContentsMargins(24, 20, 24, 18)
        layout.setSpacing(16)
        main = QWidget()
        main.setObjectName("homeMain")
        main.setMinimumWidth(560)
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)
        self.home_side = QWidget()
        self.home_side.setObjectName("homeSide")
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
        self.pending_card = MetricCard(self.icons.icon("bell", "warning"), "0", "Pendientes", "warning")
        self.overdue_card = MetricCard(self.icons.icon("calendar_due", "danger"), "0", "Vencidas", "danger")
        self.week_card = MetricCard(self.icons.icon("calendar_due", "info"), "0", "Esta semana", "info")
        self.course_card = MetricCard(self.icons.icon("courses", "brand"), "0", "Cursos", "ok")
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
        self.home_sections.setObjectName("homeSections")
        self.home_sections_layout = QVBoxLayout(self.home_sections)
        self.home_sections_layout.setContentsMargins(0, 0, 0, 0)
        self.home_sections_layout.setSpacing(12)
        home_scroll = self._scroll_area(self.home_sections)

        current = date.today()
        self.calendar = MiniCalendar(current.year, current.month, {})
        self.progress_ring = ProgressRing(0, "Progreso global")
        side_layout.addWidget(self.calendar)
        side_layout.addWidget(self.progress_ring)
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
        view.setObjectName("pageRoot")
        layout = QHBoxLayout(view)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(14)

        left = QWidget()
        left.setObjectName("taskListContent")
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
        self.task_search = SearchField(self.icons.icon("search", "muted"), "Buscar tarea o curso...")
        self.task_search.setAccessibleName("Buscar tareas")
        self.task_search.textChanged.connect(self._schedule_task_search_refresh)
        self.task_sort = QComboBox()
        self.task_sort.setAccessibleName("Ordenar tareas")
        self.task_sort.setToolTip("Ordenar la lista de tareas")
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
        self.task_detail.setMinimumWidth(280)
        self.task_detail.setMaximumWidth(340)
        self.detail_chip = StatusChip("Sin seleccionar", "pending")
        self.detail_title = QLabel("Selecciona una tarea")
        self.detail_title.setObjectName("detailTitle")
        self.detail_course = QLabel("")
        self.detail_date = QLabel("")
        self.detail_status = QLabel("")
        for label in (self.detail_title, self.detail_course, self.detail_date, self.detail_status):
            label.setWordWrap(True)
        self.open_button = PrimaryButton("Abrir campus", self.icons.icon("external", "light"))
        self.open_button.clicked.connect(self.open_selected)
        self.snooze_button = SecondaryButton("Posponer", self.icons.icon("clock", "muted"))
        self.snooze_button.setAccessibleName("Posponer recordatorio")
        self.snooze_button.setToolTip("Elegir cuando recordar esta tarea")
        self.snooze_menu = QMenu(self.snooze_button)
        for label, days in (("Recordar mañana", 1), ("Recordar en 3 días", 3), ("Recordar en 1 semana", 7)):
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
        view.setObjectName("pageRoot")
        layout = QHBoxLayout(view)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(14)

        left = QWidget()
        left.setObjectName("courseListContent")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        course_filters = QHBoxLayout()
        self.course_search = SearchField(self.icons.icon("search", "muted"), "Buscar curso...")
        self.course_search.setAccessibleName("Buscar cursos")
        self.course_search.textChanged.connect(self._schedule_course_search_refresh)
        self.course_filter = SegmentedControl([
            ("Todos", "todos"),
            ("Con pendientes", "con_pendientes"),
            ("Sin pendientes", "sin_pendientes"),
        ], "todos")
        self.course_filter.setAccessibleName("Filtrar cursos")
        self.course_filter.setToolTip("Filtrar cursos por estado de pendientes")
        self.course_filter.changed.connect(lambda _value: self.refresh_course_list())
        sync_courses = PrimaryButton("Sincronizar", self.icons.icon("refresh", "light"))
        sync_courses.setMaximumWidth(150)
        sync_courses.clicked.connect(self.sync_now)
        course_filters.addWidget(self.course_search, 1)
        course_filters.addWidget(sync_courses)
        course_metrics = QGridLayout()
        course_metrics.setHorizontalSpacing(10)
        self.course_total_metric = MetricCard(self.icons.icon("courses", "brand"), "0", "Cursos activos", "ok")
        self.course_pending_metric = MetricCard(self.icons.icon("bell", "warning"), "0", "Tareas pendientes", "warning")
        self.course_overdue_metric = MetricCard(self.icons.icon("calendar_due", "danger"), "0", "Cursos con vencidas", "warning")
        course_metrics.addWidget(self.course_total_metric, 0, 0)
        course_metrics.addWidget(self.course_pending_metric, 0, 1)
        course_metrics.addWidget(self.course_overdue_metric, 0, 2)
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
        left_layout.addWidget(self.course_filter)
        left_layout.addLayout(course_metrics)
        left_layout.addWidget(self.course_scroll, 1)
        left_layout.addWidget(self.course_count_label)

        self.course_detail = DetailPanel()
        self.course_detail.setMinimumWidth(280)
        self.course_detail.setMaximumWidth(340)
        self.course_detail_header = QFrame()
        self.course_detail_header.setObjectName("courseDetailHeader")
        detail_header_layout = QHBoxLayout(self.course_detail_header)
        detail_header_layout.setContentsMargins(0, 0, 0, 0)
        detail_header_layout.setSpacing(12)
        self.course_detail_initials = QLabel("--")
        self.course_detail_initials.setObjectName("courseInitials")
        self.course_detail_initials.setAlignment(Qt.AlignCenter)
        self.course_detail_initials.setFixedSize(50, 50)
        detail_title_box = QVBoxLayout()
        detail_title_box.setSpacing(3)
        self.course_detail_code = QLabel("")
        self.course_detail_code.setObjectName("courseCode")
        self.course_detail_title = QLabel("Selecciona un curso")
        self.course_detail_title.setObjectName("detailTitle")
        self.course_fullname_label = QLabel("")
        self.course_fullname_label.setObjectName("muted")
        self.course_fullname_label.setWordWrap(True)
        detail_title_box.addWidget(self.course_detail_code)
        detail_title_box.addWidget(self.course_detail_title)
        detail_title_box.addWidget(self.course_fullname_label)
        detail_header_layout.addWidget(self.course_detail_initials)
        detail_header_layout.addLayout(detail_title_box, 1)
        self.course_detail_status = StatusChip("Sin selección", "neutral")
        self.course_detail_status.setMaximumWidth(120)
        detail_header_layout.addWidget(self.course_detail_status)

        self.course_progress_card = QFrame()
        self.course_progress_card.setObjectName("courseProgressPanel")
        progress_layout = QVBoxLayout(self.course_progress_card)
        progress_layout.setContentsMargins(16, 14, 16, 14)
        progress_layout.setSpacing(8)
        progress_top = QHBoxLayout()
        self.course_progress_label = QLabel("PROGRESO DEL CURSO")
        self.course_progress_label.setObjectName("infoCardLabel")
        self.course_progress_percent = QLabel("0%")
        self.course_progress_percent.setObjectName("courseDetailPercent")
        progress_top.addWidget(self.course_progress_label, 1)
        progress_top.addWidget(self.course_progress_percent)
        self.course_progress_text = QLabel("-")
        self.course_progress_text.setObjectName("courseMeta")
        self.course_progress_bar = QProgressBar()
        self.course_progress_bar.setObjectName("courseProgress-ok")
        self.course_progress_bar.setRange(0, 100)
        self.course_progress_bar.setTextVisible(False)
        self.course_progress_updated = QLabel("")
        self.course_progress_updated.setObjectName("muted")
        progress_layout.addLayout(progress_top)
        progress_layout.addWidget(self.course_progress_text)
        progress_layout.addWidget(self.course_progress_bar)
        progress_layout.addWidget(self.course_progress_updated)

        self.course_pending_card = InfoCard("Pendientes", "-")
        self.course_preview_card = QFrame()
        self.course_preview_card.setObjectName("settingsInfoList")
        preview_layout = QVBoxLayout(self.course_preview_card)
        preview_layout.setContentsMargins(16, 14, 16, 14)
        preview_layout.setSpacing(8)
        self.course_preview_title = QLabel("Próximas tareas")
        self.course_preview_title.setObjectName("infoCardLabel")
        self.course_tasks_label = QLabel("-")
        self.course_tasks_label.setObjectName("coursePreviewText")
        self.course_tasks_label.setWordWrap(True)
        preview_layout.addWidget(self.course_preview_title)
        preview_layout.addWidget(self.course_tasks_label)
        open_course = PrimaryButton("Abrir Moodle", self.icons.icon("external", "light"))
        open_course.clicked.connect(lambda _checked=False: self.navigator.open_campus_home())
        view_tasks = SecondaryButton("Ver tareas del curso", self.icons.icon("tasks", "muted"))
        view_tasks.clicked.connect(self._show_selected_course_tasks)
        self.course_detail.layout.addWidget(self.course_detail_header)
        self.course_detail.layout.addWidget(self.course_progress_card)
        self.course_detail.layout.addWidget(self.course_pending_card)
        self.course_detail.layout.addWidget(self.course_preview_card)
        self.course_detail.layout.addWidget(open_course)
        self.course_detail.layout.addWidget(view_tasks)
        self.course_detail.layout.addStretch(1)

        layout.addWidget(left, 1)
        layout.addWidget(self.course_detail)
        return view

    def _build_ajustes_view(self) -> QWidget:
        view = QWidget()
        view.setObjectName("pageRoot")
        layout = QHBoxLayout(view)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(20)
        nav = QListWidget()
        nav.setObjectName("settingsNav")
        nav.setFixedWidth(210)
        nav.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.settings_stack = QStackedWidget()
        for icon, title, page in (
            ("user", "Perfil y Campus", self._settings_profile_page()),
            ("refresh", "Sincronización", self._settings_sync_page()),
            ("bell", "Notificaciones", self._settings_notifications_page()),
            ("shield", "Privacidad y Datos", self._settings_privacy_page()),
            ("moon", "Apariencia", self._settings_appearance_page()),
            ("info", "Acerca de", self._settings_about_page()),
        ):
            nav.addItem(QListWidgetItem(self.icons.icon(icon, "muted"), title))
            self.settings_stack.addWidget(page)
        nav.currentRowChanged.connect(self.settings_stack.setCurrentIndex)
        nav.setCurrentRow(0)
        layout.addWidget(nav)
        layout.addWidget(self.settings_stack, 1)
        return view

    def _settings_profile_page(self) -> QWidget:
        page = self._settings_page("Perfil y Campus", "Cuenta conectada a Campus Moodle")
        self.profile_summary = self._settings_profile_card()
        change = PrimaryButton("Cambiar perfil", self.icons.icon("user_switch", "light"))
        change.setMaximumWidth(180)
        change.clicked.connect(self.change_profile)
        logout = SecondaryButton("Cerrar sesión local", self.icons.icon("logout", "danger"))
        logout.setObjectName("dangerButton")
        logout.setMaximumWidth(210)
        logout.clicked.connect(self.logout_local)
        page.layout().addWidget(self.profile_summary)
        page.layout().addWidget(change)
        page.layout().addWidget(logout)
        return page

    def _settings_sync_page(self) -> QWidget:
        page = self._settings_page("Sincronización", "Controla frecuencia y arranque automático")
        sync_toggle = ToggleSwitch(self.settings.setting_bool("sync_on_start", True))
        sync_toggle.toggled_value.connect(lambda v: self.settings.set_setting_bool("sync_on_start", v))
        self.start_windows_check = ToggleSwitch(self.autostart.enabled())
        self.start_windows_check.toggled_value.connect(self._set_autostart_from_settings)
        self.interval_combo = QComboBox()
        self.interval_combo.setAccessibleName("Intervalo de sincronización")
        self.interval_combo.setToolTip("Elegir frecuencia de sincronización automática")
        for text, value in (("Cada 1 hora", 3600), ("Cada 6 horas", 21600), ("Una vez al día", 86400)):
            self.interval_combo.addItem(text, value)
        self._select_combo_value(self.interval_combo, self.settings.sync_interval_seconds())
        self.interval_combo.currentIndexChanged.connect(self._interval_changed)
        page.layout().addWidget(SettingsRow("Sincronizar al iniciar la app", "Consulta Moodle cada vez que abres ChivaTask", sync_toggle))
        page.layout().addWidget(SettingsRow("Iniciar con Windows", "ChivaTask arranca en la bandeja del sistema al encender el equipo", self.start_windows_check))
        page.layout().addWidget(SettingsRow("Intervalo de sincronización", "Frecuencia de consulta automática en segundo plano", self.interval_combo))
        page.layout().addWidget(PrimaryButton("Sincronizar", self.icons.icon("refresh", "light")))
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
        self.notif_mode.setAccessibleName("Modo de notificaciones")
        self.notif_mode.setToolTip("Elegir cómo se envían las notificaciones")
        for text, value in (("Solo cambios nuevos", "solo_nuevos"), ("Resumen diario", "resumen_diario"), ("Silencioso", "silencioso")):
            self.notif_mode.addItem(text, value)
        self._select_combo_value(self.notif_mode, self.settings.notification_mode())
        self.notif_mode.currentIndexChanged.connect(lambda: self.settings.set_notification_mode(self.notif_mode.currentData()))
        page.layout().addWidget(SettingsRow("Modo de notificaciones", "Cómo y cuándo enviar las alertas del sistema", self.notif_mode))
        test = SecondaryButton("Enviar notificación de prueba", self.icons.icon("bell", "warning"))
        test.clicked.connect(lambda: self.notifier.notify_changed(self.tasks[:1]) if self.tasks else self.status_pill.setText("No hay tareas para probar"))
        page.layout().addWidget(test)
        return page

    def _settings_privacy_page(self) -> QWidget:
        page = self._settings_page("Privacidad y Datos Locales", "ChivaTask guarda todo en este equipo")
        data = self._settings_info_list(
            (
                ("shield", "Credenciales", "Windows Credential Manager"),
                ("database", "Caché local", "SQLite local"),
                ("shield", "Datos externos", "Nada sale de este equipo"),
                ("database", "Ruta de caché", str(self.repository.path)),
            )
        )
        open_folder = SecondaryButton("Abrir carpeta de datos")
        open_folder.clicked.connect(self.open_data_folder)
        clear = SecondaryButton("Limpiar caché local")
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
        page = self._settings_page("Acerca de", "Tu campus académico, sin excusas.")
        hero = QFrame()
        hero.setObjectName("aboutHero")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(24, 24, 24, 24)
        hero_layout.setSpacing(10)
        hero_layout.setAlignment(Qt.AlignCenter)
        hero_layout.addWidget(BrandLockup(compact=False, header=False), 0, Qt.AlignCenter)
        tagline = QLabel("Tu campus académico, sin excusas.")
        tagline.setObjectName("aboutHeroSubtitle")
        tagline.setAlignment(Qt.AlignCenter)
        badges = QLabel("v1.0.0   ·   IIP-2026")
        badges.setObjectName("aboutHeroBadge")
        badges.setAlignment(Qt.AlignCenter)
        hero_layout.addWidget(tagline)
        hero_layout.addWidget(badges)

        about = QLabel(
            "ChivaTask es una aplicación de escritorio local para gestionar pendientes académicos. "
            "Consulta la plataforma Moodle mediante su API oficial, detecta tareas sin entrega "
            "registrada y notifica cambios importantes sin que el estudiante tenga que abrir el campus manualmente.\n\n"
            "Esta es una herramienta de uso personal, no oficial. No tiene afiliación ni respaldo institucional."
        )
        about.setObjectName("settingsCard")
        about.setWordWrap(True)
        tech = self._settings_info_list(
            (
                ("check", "Python 3.11+ y PySide6", "Interfaz de escritorio con Qt Widgets"),
                ("external", "Moodle REST API oficial", "Fuente de datos académicos"),
                ("database", "SQLite", "Caché local de tareas y cursos"),
                ("shield", "Windows Credential Manager", "Almacenamiento seguro de credenciales"),
            )
        )
        page.layout().addWidget(hero)
        page.layout().addWidget(about)
        page.layout().addWidget(self._section_title("Tecnologías"))
        page.layout().addWidget(tech)
        return page

    def _settings_page(self, title: str, subtitle: str) -> QWidget:
        page = QWidget()
        page.setObjectName("pageRoot")
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

    def _settings_profile_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("profileSettingsCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(16)
        self.profile_settings_avatar = QLabel("HL")
        self.profile_settings_avatar.setObjectName("profileSettingsAvatar")
        self.profile_settings_avatar.setAlignment(Qt.AlignCenter)
        self.profile_settings_avatar.setFixedSize(60, 60)
        text_box = QVBoxLayout()
        text_box.setSpacing(3)
        self.profile_settings_name = QLabel("Sin perfil")
        self.profile_settings_name.setObjectName("profileSettingsName")
        self.profile_settings_username = QLabel("")
        self.profile_settings_username.setObjectName("profileSettingsUsername")
        self.profile_settings_status = QLabel("")
        self.profile_settings_status.setObjectName("profileSettingsStatus")
        text_box.addWidget(self.profile_settings_name)
        text_box.addWidget(self.profile_settings_username)
        text_box.addWidget(self.profile_settings_status)
        layout.addWidget(self.profile_settings_avatar)
        layout.addLayout(text_box, 1)
        return card

    def _settings_info_list(self, rows: tuple[tuple[str, str, str], ...]) -> QFrame:
        card = QFrame()
        card.setObjectName("settingsInfoList")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        for icon_name, label, value in rows:
            row = QFrame()
            row.setObjectName("settingsInfoRow")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(16, 14, 16, 14)
            row_layout.setSpacing(14)
            icon = QLabel()
            icon.setObjectName("settingsInfoIcon")
            icon.setAlignment(Qt.AlignCenter)
            icon.setPixmap(self.icons.icon(icon_name, "muted").pixmap(20, 20))
            icon.setFixedSize(42, 42)
            texts = QVBoxLayout()
            texts.setSpacing(3)
            label_widget = QLabel(label)
            label_widget.setObjectName("settingsInfoLabel")
            value_widget = QLabel(value)
            value_widget.setObjectName("settingsInfoValue")
            value_widget.setWordWrap(True)
            texts.addWidget(label_widget)
            texts.addWidget(value_widget)
            row_layout.addWidget(icon)
            row_layout.addLayout(texts, 1)
            layout.addWidget(row)
        return card

    def _section_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("sectionTitle")
        return label

    def _scroll_area(self, widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setObjectName("flatScroll")
        widget.setObjectName(widget.objectName() or "scrollContent")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.viewport().setObjectName("scrollViewport")
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

    def ensure_startup_sync(self) -> None:
        if not self.credentials.has_credentials():
            self._set_status("Credenciales pendientes", "pending")
            return
        if self.settings.setting_bool("sync_on_start", True):
            self.sync_now()

    def sync_now(self) -> None:
        if self.worker_thread and self.worker_thread.isRunning():
            return
        self.syncing = True
        self._set_data_state("loading")
        self._set_status("Sincronizando...", "syncing")
        self.sync_button.setEnabled(False)
        self.sync_button.setText("Sincronizando...")
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
        self.sync_button.setText("Sincronizar")
        self.refresh_from_cache()
        if result.ok:
            self.api_status = "ok"
            self.last_error_code = None
            self.error_banner.hide()
            self._set_data_state("success")
            self._set_status("Sincronizado", "ok")
            if result.changed_pending:
                self._show_sync_toast(
                    "Sincronización completada",
                    f"{result.pending_count} tareas pendientes - {result.course_count} cursos",
                    "success",
                )
            else:
                self._show_sync_toast("Sincronizado", "No se detectaron cambios nuevos", "success")
            self._notify_changed(result.changed_pending)
        else:
            self.api_status = "error"
            self.last_error_code = result.error_code
            self.error_label.setText(f"Sin conexión a Moodle - Mostrando datos en caché ({result.error_code})")
            self.error_banner.show()
            self._set_data_state("offline-cache" if result.pending_count or result.course_count else "recoverable-error")
            self._set_status("Sin conexión", "error")
            self._show_sync_toast("No se pudo sincronizar", "Se mantienen los datos guardados en caché", "error", retry=True)
            if result.error_code == "invalidlogin":
                if self._exec_login_dialog(hide_shell=True, restore_on_cancel=True):
                    self.sync_now()

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
        self.nav_buttons["tareas"].set_badge(counts["todas"])
        self.nav_buttons["cursos"].set_badge(courses)
        last = self.queries.last_successful_sync()
        if last and self.api_status != "error":
            self._set_status("Sincronizado", "ok")
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
        apply_application_theme(mode)
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
        toggle = ThemeToggleButton(self.icons.icon("moon", "dark"), self.icons.icon("sun", "light"), self._effective_visual_mode())
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
        dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
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
        username = (getattr(self.credentials, "get_username", lambda: None)() or "estudiante").split("@")[0].split(".")[0]
        self.greeting_title.setText(f"{self._greeting_for_hour(datetime.now().hour)}, {username}")
        next_task = self.queries.next_deadline()
        self._next_deadline_task = next_task
        if next_task:
            self.next_deadline_card.show()
            self.next_deadline_text.setText(
                f"PRÓXIMA ENTREGA - {relative_due_text(next_task.due_at)}\n"
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
                self.home_sections_layout.addWidget(EmptyState(empty, "", self.icons.icon("check", "brand")))
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
                self.task_list_layout.addWidget(EmptyState("Sin resultados", "No hay tareas para este filtro.", self.icons.icon("tasks", "muted")))
            else:
                self._set_data_state("empty")
                self.task_list_layout.addWidget(EmptyState("Sin tareas", "No hay tareas pendientes en caché.", self.icons.icon("tasks", "muted")))
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
        pending_tasks_total = sum(int(summary["pending"]) for summary in summaries)
        overdue_courses = sum(
            1
            for summary in summaries
            if any(classify_task(task) == TaskBucket.OVERDUE for task in summary["tasks"])
        )
        self.course_total_metric.update_value(str(len(summaries)), "Cursos activos")
        self.course_pending_metric.update_value(str(pending_tasks_total), "Tareas pendientes")
        self.course_overdue_metric.update_value(str(overdue_courses), "Cursos con vencidas")
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
        columns = 1 if self.width() < 1180 else 2 if available_width >= 700 else 1
        if not filtered:
            self.course_cards_layout.addWidget(EmptyState("Sin cursos", "No hay cursos para este filtro.", self.icons.icon("courses", "muted")), 0, 0, 1, columns)
        for index, summary in enumerate(filtered):
            card = CourseCard(summary)
            card.selected.connect(self._select_course_summary)
            card.view_tasks.connect(self._show_course_tasks_from_summary)
            card.open_campus.connect(self._open_course_campus_from_summary)
            self.course_cards_layout.addWidget(card, index // columns, index % columns)
        self.course_scroll.verticalScrollBar().setValue(0)
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
        if task and self._detail_panel_is_compact(self.task_detail):
            self._show_task_detail_modal(task)

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

    def _detail_panel_is_compact(self, panel: QWidget) -> bool:
        return self.isVisible() and (not panel.isVisible() or self.width() < 1180)

    def _build_task_detail_modal(self, task: Task) -> BaseModal:
        bucket = classify_task(task)
        modal = BaseModal("Detalle de tarea", self)
        modal.setMinimumWidth(380)
        chip = StatusChip(STATUS_TEXT[bucket], CHIP_VARIANT[bucket])
        title = QLabel(task.name)
        title.setObjectName("detailTitle")
        title.setWordWrap(True)
        course = InfoCard("Curso", task.course_fullname or task.course_shortname)
        due = InfoCard("Fecha de entrega", unix_to_local_text(task.due_at))
        state = InfoCard("Estado", STATUS_TEXT[bucket])
        if task.snoozed_until:
            state.update_value("Estado", f"{STATUS_TEXT[bucket]}\nPospuesta hasta {unix_to_local_text(task.snoozed_until)}")
        actions = QHBoxLayout()
        open_button = PrimaryButton("Abrir campus", self.icons.icon("external", "light"))
        open_button.clicked.connect(lambda: (modal.accept(), self.open_selected()))
        snooze_button = SecondaryButton("Recordar mañana", self.icons.icon("clock", "muted"))
        snooze_button.clicked.connect(lambda: (modal.accept(), self.snooze_selected(1)))
        actions.addWidget(open_button)
        actions.addWidget(snooze_button)
        modal.layout.addWidget(chip)
        modal.layout.addWidget(title)
        modal.layout.addWidget(course)
        modal.layout.addWidget(due)
        modal.layout.addWidget(state)
        modal.layout.addLayout(actions)
        return modal

    def _show_task_detail_modal(self, task: Task) -> None:
        self._build_task_detail_modal(task).exec()

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
        if self._detail_panel_is_compact(self.course_detail):
            self._show_course_detail_modal(summary)

    def _render_course_detail(self) -> None:
        course = self.selected_course
        if not course:
            self.course_detail_initials.setText("--")
            self.course_detail_code.setText("")
            self.course_detail_title.setText("Selecciona un curso")
            self.course_fullname_label.setText("")
            self._set_chip(self.course_detail_status, "Sin selección", "neutral")
            self.course_pending_card.update_value("Pendientes", "-")
            self.course_progress_percent.setText("0%")
            self.course_progress_text.setText("-")
            self.course_progress_bar.setValue(0)
            self.course_progress_bar.setObjectName("courseProgress-ok")
            self.course_progress_updated.setText("")
            self.course_tasks_label.setText("-")
            return
        total = int(course["total"])
        submitted = int(course["submitted"])
        pending = int(course["pending"])
        progress = int((submitted / total) * 100) if total else 0
        tasks: list[Task] = course["tasks"]  # type: ignore[assignment]
        has_overdue = any(classify_task(task) == TaskBucket.OVERDUE for task in tasks)
        progress_variant = "warning" if has_overdue else "ok" if pending == 0 else "info"
        status_text = "Con vencidas" if has_overdue else "Al día" if pending == 0 else "Pendiente"
        status_variant = "overdue" if has_overdue else "ok" if pending == 0 else "undated"
        self.course_detail_initials.setText(str(course["shortname"])[:2].upper())
        self.course_detail_code.setText(str(course["shortname"]))
        self.course_detail_title.setText(str(course["shortname"]))
        self.course_fullname_label.setText(str(course["fullname"]))
        self._set_chip(self.course_detail_status, status_text, status_variant)
        self.course_pending_card.update_value(
            "Pendientes",
            "Sin pendientes" if pending == 0 else f"{pending} pendiente{'s' if pending != 1 else ''}",
        )
        self.course_progress_percent.setText(f"{progress}%")
        self.course_progress_text.setText(f"{submitted} de {total} entregadas")
        self.course_progress_bar.setObjectName(f"courseProgress-{progress_variant}")
        self.course_progress_bar.setValue(progress)
        self.course_progress_bar.style().unpolish(self.course_progress_bar)
        self.course_progress_bar.style().polish(self.course_progress_bar)
        self.course_progress_updated.setText(f"Actualizado: {self._sync_status_detail() or 'sin registro'}")
        preview = "\n".join(f"- {task.name} - {STATUS_TEXT[classify_task(task)]}" for task in tasks[:5])
        self.course_tasks_label.setText(preview or "Todo entregado. Sin pendientes.")

    def _build_course_detail_modal(self, course: dict[str, object]) -> BaseModal:
        total = int(course["total"])
        submitted = int(course["submitted"])
        pending = int(course["pending"])
        progress = int((submitted / total) * 100) if total else 0
        tasks: list[Task] = course["tasks"]  # type: ignore[assignment]
        preview = "\n".join(f"- {task.name} ({STATUS_TEXT[classify_task(task)]})" for task in tasks[:5])
        modal = BaseModal("Detalle de curso", self)
        modal.setMinimumWidth(400)
        title = QLabel(str(course["shortname"]))
        title.setObjectName("detailTitle")
        title.setWordWrap(True)
        fullname = QLabel(str(course["fullname"]))
        fullname.setObjectName("subtitle")
        fullname.setWordWrap(True)
        pending_card = InfoCard(
            "Pendientes",
            "Sin pendientes" if pending == 0 else f"{pending} pendiente{'s' if pending != 1 else ''}",
        )
        progress_card = InfoCard("Progreso", f"{submitted} de {total} entregadas - {progress}%")
        preview_card = InfoCard("Próximas tareas", preview or "Todo entregado. Sin pendientes.")
        actions = QHBoxLayout()
        open_course = PrimaryButton("Abrir Moodle", self.icons.icon("external", "light"))
        open_course.clicked.connect(lambda: (modal.accept(), self.navigator.open_campus_home()))
        view_tasks = SecondaryButton("Ver tareas", self.icons.icon("tasks", "muted"))
        view_tasks.clicked.connect(lambda: (modal.accept(), self._show_course_tasks_from_summary(course)))
        actions.addWidget(open_course)
        actions.addWidget(view_tasks)
        modal.layout.addWidget(title)
        modal.layout.addWidget(fullname)
        modal.layout.addWidget(pending_card)
        modal.layout.addWidget(progress_card)
        modal.layout.addWidget(preview_card)
        modal.layout.addLayout(actions)
        return modal

    def _show_course_detail_modal(self, course: dict[str, object]) -> None:
        self._build_course_detail_modal(course).exec()

    def _show_selected_course_tasks(self) -> None:
        if not self.selected_course:
            return
        self.navigate("tareas")
        self.task_search.setText(str(self.selected_course["shortname"]))

    def _show_course_tasks_from_summary(self, summary: dict[str, object]) -> None:
        self.selected_course = summary
        self._show_selected_course_tasks()

    def _open_course_campus_from_summary(self, _summary: dict[str, object]) -> None:
        self.navigator.open_campus_home()

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
            button.set_active(nav_key == key)
        self.footer.setVisible(key in {"inicio", "tareas"})
        self._position_sync_toast()

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
        self._set_status(f"Recordatorio pospuesto {days} día(s)", "pending")

    def change_profile(self) -> None:
        try:
            self.credentials.clear_token()
        except CredentialError as exc:
            QMessageBox.critical(self, "Credential Manager", str(exc))
            return
        if self._exec_login_dialog(hide_shell=True, restore_on_cancel=True):
            self.sync_now()

    def _exec_login_dialog(self, hide_shell: bool = False, restore_on_cancel: bool = True) -> bool:
        was_visible = self.isVisible()
        previous_state = self.windowState()
        previous_geometry = self.geometry()
        if hide_shell:
            self.hide()
        dialog = LoginDialog(self.credentials)
        accepted = dialog.exec_maximized() == QDialog.Accepted
        if accepted:
            self.settings.set_onboarding_completed(True)
            if hide_shell:
                self._restore_window_state(previous_state, previous_geometry)
        elif hide_shell and restore_on_cancel and was_visible:
            self._restore_window_state(previous_state, previous_geometry)
        return accepted

    def _restore_window_state(self, state, geometry) -> None:
        if state & Qt.WindowFullScreen:
            self.showFullScreen()
        elif state & Qt.WindowMaximized:
            self.showMaximized()
        else:
            self.setGeometry(geometry)
            self.show()
        self.raise_()
        self.activateWindow()

    def logout_local(self) -> None:
        modal = ConfirmModal(
            "Cerrar sesión local",
            "Esto elimina credenciales, token y caché académica de este equipo. No borra nada en Moodle.",
            self,
        )
        cancel = SecondaryButton("Cancelar")
        cancel.clicked.connect(modal.reject)
        logout = PrimaryButton("Cerrar sesión")
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
            self._set_status("Sesión local cerrada", "pending")
            if self._exec_login_dialog(hide_shell=True, restore_on_cancel=False):
                self.sync_now()
            else:
                QApplication.quit()

    def clear_cache_local(self) -> None:
        modal = ConfirmModal(
            "Limpiar caché local",
            "Se eliminarán cursos, tareas y estado de notificaciones. Credenciales y ajustes se conservan.",
            self,
        )
        cancel = SecondaryButton("Cancelar")
        cancel.clicked.connect(modal.reject)
        clear = PrimaryButton("Limpiar caché")
        clear.setObjectName("dangerPrimaryButton")
        clear.clicked.connect(modal.accept)
        modal.layout.addWidget(cancel)
        modal.layout.addWidget(clear)
        if modal.exec() == QDialog.Accepted:
            self.repository.clear_academic_cache()
            self.refresh_from_cache()
            self._set_status("Caché local eliminada", "pending")

    def open_data_folder(self) -> None:
        path = self.repository.path
        if path == ":memory:":
            return
        opened = self.navigator.open_folder(path.parent)
        if not opened:
            QMessageBox.warning(self, "Carpeta no disponible", "No se pudo abrir la carpeta de datos local.")

    def _set_status(self, text: str, variant: str) -> None:
        detail = self._sync_status_detail() if variant == "ok" else ""
        self.status_pill.set_status(text, variant, detail)

    def _show_sync_toast(self, title: str, detail: str, variant: str, retry: bool = False) -> None:
        if not hasattr(self, "sync_toast"):
            return
        self.sync_toast.show_message(title, detail, variant, retry)
        self._position_sync_toast()

    def _position_sync_toast(self) -> None:
        if not hasattr(self, "sync_toast"):
            return
        margin = 18
        self.sync_toast.adjustSize()
        root_width = self.content_root.width() if hasattr(self, "content_root") else self.width()
        root_height = self.content_root.height() if hasattr(self, "content_root") else self.height()
        footer_height = self.footer.height() if hasattr(self, "footer") and self.footer.isVisible() else 0
        x = max(margin, root_width - self.sync_toast.width() - margin)
        y = max(margin, root_height - footer_height - self.sync_toast.height() - margin)
        self.sync_toast.move(x, y)

    def _refresh_sync_status_detail(self) -> None:
        if getattr(self.status_pill, "objectName", lambda: "")() == "statusOk":
            self.status_pill.set_status(self.status_pill.text(), "ok", self._sync_status_detail())

    def _sync_status_detail(self) -> str:
        raw = self.repository.get_state("last_successful_sync_at")
        if not raw:
            return ""
        try:
            elapsed = max(0, now_ts() - int(raw))
        except (TypeError, ValueError):
            return ""
        if elapsed < 60:
            return "ahora"
        minutes = elapsed // 60
        if minutes < 60:
            return f"hace {minutes}m"
        hours = minutes // 60
        if hours < 24:
            return f"hace {hours}h"
        return f"hace {hours // 24}d"

    def _set_data_state(self, state: str) -> None:
        labels = {
            "loading": "Cargando datos",
            "success": "Datos actualizados",
            "empty": "Sin tareas pendientes",
            "filtered-empty": "Sin resultados para el filtro",
            "offline-cache": "Sin conexión, usando caché",
            "recoverable-error": "Error recuperable de sincronización",
            "blocking-error": "Acción bloqueada",
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
            return "Buenos días"
        if 12 <= hour < 18:
            return "Buenas tardes"
        return "Buenas noches"

    def _refresh_profile_summary(self) -> None:
        if not hasattr(self, "profile_settings_name"):
            return
        raw_username = getattr(self.credentials, "get_username", lambda: None)()
        username = raw_username or "Sin perfil conectado"
        display = username.split("@", 1)[0].replace(".", " ").strip().title() if raw_username else "Sin perfil"
        initials = "".join(part[0] for part in display.split()[:2]).upper() if raw_username else "?"
        self.profile_settings_avatar.setText(initials)
        self.profile_settings_name.setText(display)
        self.profile_settings_username.setText(username if raw_username else "Conecta una cuenta de Campus Moodle")
        status = "Conectado a Campus Moodle" if self.credentials.has_credentials() else "Pendiente"
        self.profile_settings_status.setText(f"• {status}")
        if hasattr(self.profile_button, "refresh_user"):
            self.profile_button.refresh_user()

    def _refresh_sync_history(self) -> None:
        if not hasattr(self, "sync_history"):
            return
        last = self.repository.get_state("last_successful_sync_at")
        error = self.repository.get_state("last_error_code")
        self.sync_history.setText(
            "Historial de sincronización\n"
            f"Última correcta: {unix_to_local_text(int(last)) if last else 'Sin registro'}\n"
            f"Último error: {error or 'Ninguno'}"
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
        if self.windowState() & Qt.WindowFullScreen:
            self.showFullScreen()
        elif self.windowState() & Qt.WindowMaximized:
            self.showMaximized()
        else:
            self.show()
        self.raise_()
        self.activateWindow()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_responsive_layout()
        self._position_sync_toast()
        if hasattr(self, "course_cards_layout"):
            QTimer.singleShot(0, self.refresh_course_list)

    def closeEvent(self, event: QCloseEvent) -> None:
        app = QApplication.instance()
        if app and app.property("chivatask_testing"):
            self.timer.stop()
            self.startup_timer.stop()
            self.task_search_timer.stop()
            self.course_search_timer.stop()
            self.sync_relative_timer.stop()
            super().closeEvent(event)
            return
        if self.tray.is_visible():
            event.ignore()
            self.hide()
            self.tray.show_background_message()
        else:
            super().closeEvent(event)


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
