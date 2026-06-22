"""Componentes visuales inspirados en el prototipo Figma Make."""

from __future__ import annotations

from calendar import monthrange
from datetime import datetime

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QIcon, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from domain.modelos import Task, TaskBucket
from domain.politica_tareas import classify_task
from domain.tiempo import now_ts, unix_to_local_text

from .chips import StatusChip


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


def relative_due_text(due_at: int | None) -> str:
    if not due_at:
        return "Sin fecha"
    diff_days = int((due_at - now_ts()) / 86400)
    if diff_days < 0:
        return f"Hace {abs(diff_days)}d"
    if diff_days == 0:
        return "Hoy"
    if diff_days == 1:
        return "Mañana"
    return f"En {diff_days} días"


def set_elided_text(label: QLabel, text: str, max_width: int) -> None:
    label.setToolTip(text)
    label.setText(QFontMetrics(label.font()).elidedText(text, Qt.ElideRight, max_width))


class ElidedLabel(QLabel):
    """Etiqueta que recalcula elision segun el ancho real disponible."""

    def __init__(self, text: str = "", lines: int = 1) -> None:
        super().__init__()
        self.full_text = text
        self.lines = max(1, lines)
        self.setToolTip(text)
        self.setWordWrap(lines > 1)
        self.setText(text)

    def set_full_text(self, text: str) -> None:
        self.full_text = text
        self.setToolTip(text)
        self._refresh_elision()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh_elision()

    def _refresh_elision(self) -> None:
        width = max(32, self.width() - 2)
        metrics = QFontMetrics(self.font())
        if self.lines <= 1:
            self.setText(metrics.elidedText(self.full_text, Qt.ElideRight, width))
            return
        words = self.full_text.split()
        if not words:
            self.setText("")
            return
        first_line: list[str] = []
        remaining = words[:]
        while remaining:
            candidate = " ".join([*first_line, remaining[0]])
            if first_line and metrics.horizontalAdvance(candidate) > width:
                break
            first_line.append(remaining.pop(0))
        if not remaining:
            self.setText(" ".join(first_line))
            return
        second = metrics.elidedText(" ".join(remaining), Qt.ElideRight, width)
        self.setText(f"{' '.join(first_line)}\n{second}")


class MetricCard(QFrame):
    def __init__(self, icon: QIcon, value: str, label: str, variant: str = "default") -> None:
        super().__init__()
        self.setObjectName(f"metricCard-{variant}")
        self.setMinimumHeight(82)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)
        icon_label = QLabel()
        icon_label.setObjectName(f"metricIcon-{variant}")
        icon_label.setPixmap(icon.pixmap(22, 22))
        texts = QVBoxLayout()
        texts.setSpacing(2)
        self.value_label = QLabel(value)
        self.value_label.setObjectName("metricValue")
        self.label_label = QLabel(label)
        self.label_label.setObjectName("metricLabel")
        texts.addWidget(self.value_label)
        texts.addWidget(self.label_label)
        layout.addWidget(icon_label)
        layout.addLayout(texts)
        layout.addStretch(1)

    def update_value(self, value: str, label: str | None = None) -> None:
        self.value_label.setText(value)
        if label is not None:
            self.label_label.setText(label)


class EmptyState(QFrame):
    def __init__(self, title: str, subtitle: str, icon: QIcon | None = None) -> None:
        super().__init__()
        self.setObjectName("emptyState")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 34, 28, 34)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignCenter)
        if icon:
            icon_label = QLabel()
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setPixmap(icon.pixmap(34, 34))
            layout.addWidget(icon_label)
        title_label = QLabel(title)
        title_label.setObjectName("emptyTitle")
        title_label.setAlignment(Qt.AlignCenter)
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("emptySubtitle")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)


class TaskRowCard(QFrame):
    selected = Signal(object)

    def __init__(self, task: Task, compact: bool = False) -> None:
        super().__init__()
        self.task = task
        bucket = classify_task(task)
        self.setObjectName(f"taskRow-{CHIP_VARIANT[bucket]}")
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAccessibleName(f"Tarea: {task.name}")
        self.setMinimumHeight(64 if compact else 76)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10 if compact else 13, 16, 10 if compact else 13)
        layout.setSpacing(12)

        dot = QLabel()
        dot.setObjectName(f"taskDot-{CHIP_VARIANT[bucket]}")
        dot.setFixedSize(8, 8)

        title_box = QVBoxLayout()
        title_box.setSpacing(3)
        title = ElidedLabel(task.name, 2)
        title.setObjectName("taskRowTitle")
        meta_text = task.course_shortname or task.course_fullname
        meta = ElidedLabel(meta_text, 1)
        meta.setObjectName("taskRowMeta")
        meta.setToolTip(task.course_fullname or meta_text)
        title_box.addWidget(title)
        title_box.addWidget(meta)

        date_box = QVBoxLayout()
        date_box.setSpacing(2)
        date_label = QLabel(unix_to_local_text(task.due_at))
        date_label.setObjectName("taskRowDate")
        rel_label = QLabel(relative_due_text(task.due_at))
        rel_label.setObjectName(f"taskRelative-{CHIP_VARIANT[bucket]}")
        date_box.addWidget(date_label)
        date_box.addWidget(rel_label)

        chip = StatusChip(STATUS_TEXT[bucket], CHIP_VARIANT[bucket])
        if task.snoozed_until:
            chip.setText("Pospuesta")
            chip.setObjectName("chip-neutral")

        layout.addWidget(dot)
        layout.addLayout(title_box, 1)
        layout.addLayout(date_box)
        layout.addWidget(chip)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selected.emit(self.task)
        super().mousePressEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.selected.emit(self.task)
            return
        super().keyPressEvent(event)


class CourseCard(QFrame):
    selected = Signal(object)
    view_tasks = Signal(object)
    open_campus = Signal(object)

    def __init__(self, summary: dict[str, object]) -> None:
        super().__init__()
        self.summary = summary
        pending = int(summary["pending"])
        total = int(summary["total"])
        submitted = int(summary["submitted"])
        progress = int((submitted / total) * 100) if total else 0
        tasks = summary.get("tasks", [])
        has_overdue = any(classify_task(task) == TaskBucket.OVERDUE for task in tasks)
        progress_variant = "warning" if has_overdue else "ok" if pending == 0 else "info"
        self.setObjectName("courseCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAccessibleName(f"Curso: {summary['fullname']}")
        self.setMinimumWidth(300)
        self.setMinimumHeight(190)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(8)
        header = QHBoxLayout()
        header.setSpacing(12)

        initials = QLabel(str(summary["shortname"])[:2].upper())
        initials.setObjectName("courseInitials")
        initials.setAlignment(Qt.AlignCenter)
        initials.setFixedSize(44, 44)

        titles = QVBoxLayout()
        titles.setSpacing(3)
        code = QLabel(str(summary["shortname"]))
        code.setObjectName("courseCode")
        fullname = str(summary["fullname"])
        name = ElidedLabel(fullname, 2)
        name.setObjectName("courseName")
        titles.addWidget(code)
        titles.addWidget(name)

        status_text = "Con vencidas" if has_overdue else "Al día" if pending == 0 else "Pendiente"
        status_variant = "overdue" if has_overdue else "ok" if pending == 0 else "undated"
        status = StatusChip(status_text, status_variant)
        header.addWidget(initials)
        header.addLayout(titles, 1)
        header.addWidget(status)

        progress_row = QHBoxLayout()
        progress_row.setSpacing(8)
        progress_label = QLabel(f"{submitted} de {total} entregadas")
        progress_label.setObjectName("courseMeta")
        percent_label = QLabel(f"{progress}%")
        percent_label.setObjectName(f"coursePercent-{progress_variant}")
        progress_row.addWidget(progress_label, 1)
        progress_row.addWidget(percent_label)
        bar = QProgressBar()
        bar.setObjectName(f"courseProgress-{progress_variant}")
        bar.setRange(0, 100)
        bar.setValue(progress)
        bar.setTextVisible(False)

        footer = QHBoxLayout()
        footer.setSpacing(8)
        pending_label = QLabel("Sin pendientes" if pending == 0 else f"{pending} pendiente{'s' if pending != 1 else ''}")
        pending_label.setObjectName("courseMeta")
        tasks_button = QPushButton("Ver tareas")
        tasks_button.setObjectName("secondarySmallButton")
        tasks_button.setMinimumWidth(108)
        tasks_button.setAccessibleName(f"Ver tareas de {summary['shortname']}")
        tasks_button.clicked.connect(lambda: self.view_tasks.emit(self.summary))
        campus_button = QPushButton("Campus")
        campus_button.setObjectName("primarySmallButton")
        campus_button.setMinimumWidth(88)
        campus_button.setAccessibleName(f"Abrir campus de {summary['shortname']}")
        campus_button.clicked.connect(lambda: self.open_campus.emit(self.summary))
        footer.addWidget(pending_label, 1)
        if pending:
            footer.addWidget(tasks_button)
        footer.addWidget(campus_button)

        layout.addLayout(header)
        layout.addLayout(progress_row)
        layout.addWidget(bar)
        layout.addLayout(footer)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selected.emit(self.summary)
        super().mousePressEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.selected.emit(self.summary)
            return
        super().keyPressEvent(event)


class SettingsRow(QFrame):
    def __init__(self, title: str, subtitle: str, control: QWidget) -> None:
        super().__init__()
        self.setObjectName("settingsRow")
        self.setMaximumWidth(760)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(16)
        text_box = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("settingsRowTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("settingsRowSubtitle")
        subtitle_label.setWordWrap(True)
        text_box.addWidget(title_label)
        text_box.addWidget(subtitle_label)
        layout.addLayout(text_box, 1)
        layout.addWidget(control)


class ToggleSwitch(QPushButton):
    toggled_value = Signal(bool)

    def __init__(self, checked: bool = False) -> None:
        super().__init__("")
        self._checked = checked
        self.setCheckable(True)
        self.setFixedSize(48, 28)
        self.setCursor(Qt.PointingHandCursor)
        self.setAccessibleName("Interruptor")
        self.clicked.connect(self._emit)
        self.setChecked(checked)

    def setChecked(self, checked: bool) -> None:  # noqa: N802 - Qt API
        self._checked = checked
        super().setChecked(checked)
        self._refresh()

    def isChecked(self) -> bool:  # noqa: N802 - Qt API
        return self._checked

    def _emit(self) -> None:
        self._checked = super().isChecked()
        self._refresh()
        self.toggled_value.emit(self._checked)

    def _refresh(self) -> None:
        self.setObjectName("toggleOn" if self._checked else "toggleOff")
        self.setText("")
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        enabled = self.isEnabled()
        track = QColor("#16775F" if self._checked else "#CBD5E1")
        if not enabled:
            track = QColor("#E2E8F0")
        if self.underMouse() and enabled:
            track = QColor("#0F5F4A" if self._checked else "#94A3B8")
        painter.setPen(Qt.NoPen)
        painter.setBrush(track)
        rect = QRectF(1, 1, self.width() - 2, self.height() - 2)
        painter.drawRoundedRect(rect, 13, 13)
        knob_size = 22
        knob_x = self.width() - knob_size - 3 if self._checked else 3
        knob = QRectF(knob_x, 3, knob_size, knob_size)
        painter.setBrush(QColor("#FFFFFF" if enabled else "#F8FAFC"))
        painter.drawEllipse(knob)
        if self.hasFocus():
            painter.setPen(QPen(QColor("#6EE7B7"), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 12, 12)


class ThemeToggleButton(QPushButton):
    changed = Signal(str)

    def __init__(self, icon_light: QIcon, icon_dark: QIcon, visual_mode: str = "claro") -> None:
        super().__init__()
        self.icon_light = icon_light
        self.icon_dark = icon_dark
        self.visual_mode = "oscuro" if visual_mode == "oscuro" else "claro"
        self.setCheckable(True)
        self.setFixedSize(44, 36)
        self.setAccessibleName("Cambiar modo claro u oscuro")
        self.clicked.connect(self._toggle)
        self._refresh()

    def set_visual_mode(self, visual_mode: str) -> None:
        self.visual_mode = "oscuro" if visual_mode == "oscuro" else "claro"
        self._refresh()

    def _toggle(self) -> None:
        self.visual_mode = "claro" if self.visual_mode == "oscuro" else "oscuro"
        self._refresh()
        self.changed.emit(self.visual_mode)

    def _refresh(self) -> None:
        dark = self.visual_mode == "oscuro"
        self.setChecked(dark)
        self.setIcon(self.icon_dark if dark else self.icon_light)
        self.setObjectName("themeToggleDark" if dark else "themeToggleLight")
        self.setToolTip("Cambiar a modo claro" if dark else "Cambiar a modo oscuro")
        self.style().unpolish(self)
        self.style().polish(self)


class SegmentedControl(QFrame):
    changed = Signal(str)

    def __init__(self, options: list[tuple[str, str]], selected: str) -> None:
        super().__init__()
        self.setObjectName("segmentedControl")
        self.buttons: dict[str, QPushButton] = {}
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        self.selected = selected
        for label, value in options:
            button = QPushButton(label)
            button.setCheckable(True)
            button.setFocusPolicy(Qt.StrongFocus)
            button.setAccessibleName(label)
            button.clicked.connect(lambda _=False, option=value: self.set_value(option))
            layout.addWidget(button)
            self.buttons[value] = button
        self._refresh()

    def set_value(self, value: str) -> None:
        self.selected = value
        self._refresh()
        self.changed.emit(value)

    def currentData(self) -> str:  # noqa: N802 - compatibilidad con controles de filtro
        return self.selected

    def _refresh(self) -> None:
        for value, button in self.buttons.items():
            button.setChecked(value == self.selected)
            button.setObjectName("segmentActive" if value == self.selected else "segment")
            button.style().unpolish(button)
            button.style().polish(button)


class PillFilter(QFrame):
    changed = Signal(str)

    def __init__(self, options: list[tuple[str, str]], selected: str) -> None:
        super().__init__()
        self.setObjectName("pillFilter")
        self.buttons: dict[str, QPushButton] = {}
        self.selected = selected
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        for label, value in options:
            button = QPushButton(label)
            button.setFocusPolicy(Qt.StrongFocus)
            button.setAccessibleName(label)
            button.clicked.connect(lambda _=False, option=value: self.set_value(option))
            layout.addWidget(button)
            self.buttons[value] = button
        layout.addStretch(1)
        self._refresh()

    def currentData(self) -> str:  # noqa: N802 - compatibilidad con QComboBox
        return self.selected

    def set_value(self, value: str) -> None:
        self.selected = value
        self._refresh()
        self.changed.emit(value)

    def _refresh(self) -> None:
        for value, button in self.buttons.items():
            button.setObjectName("pillActive" if value == self.selected else "pill")
            button.style().unpolish(button)
            button.style().polish(button)


class ProgressRing(QFrame):
    def __init__(self, value: int, label: str) -> None:
        super().__init__()
        self.setObjectName("progressRing")
        self.value = max(0, min(100, value))
        self.label = label
        self.setMinimumHeight(156)
        self.setMinimumWidth(156)

    def update_value(self, value: int, label: str | None = None) -> None:
        self.value = max(0, min(100, value))
        if label:
            self.label = label
        self.update()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        size = min(self.width(), self.height()) - 42
        x = (self.width() - size) / 2
        y = 18
        rect = QRectF(x, y, size, size)
        track_pen = QPen(QColor("#E8EEF4"), 10)
        track_pen.setCapStyle(Qt.RoundCap)
        value_pen = QPen(QColor("#16775F"), 10)
        value_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(track_pen)
        painter.drawArc(rect, 0, 360 * 16)
        painter.setPen(value_pen)
        painter.drawArc(rect, 90 * 16, int(-360 * 16 * self.value / 100))
        text_color = self.palette().color(self.foregroundRole())
        painter.setPen(text_color)
        value_font = QFont("Segoe UI", 18, QFont.Bold)
        painter.setFont(value_font)
        painter.drawText(rect, Qt.AlignCenter, f"{self.value}%")
        muted = QColor("#9FB0C3") if text_color.lightness() > 180 else QColor("#64748B")
        painter.setPen(muted)
        label_font = QFont("Segoe UI", 9, QFont.DemiBold)
        painter.setFont(label_font)
        label_rect = QRectF(12, rect.bottom() + 8, self.width() - 24, 26)
        painter.drawText(label_rect, Qt.AlignCenter | Qt.TextWordWrap, self.label)


class MiniCalendar(QFrame):
    def __init__(self, year: int, month: int, marks: dict[int, str]) -> None:
        super().__init__()
        self.setObjectName("miniCalendar")
        self.setMinimumHeight(260)
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(14, 14, 14, 14)
        self.grid.setHorizontalSpacing(6)
        self.grid.setVerticalSpacing(8)
        self.set_month(year, month, marks)

    def set_month(self, year: int, month: int, marks: dict[int, str]) -> None:
        self._clear()
        title = QLabel(datetime(year, month, 1).strftime("%B %Y"))
        title.setObjectName("calendarTitle")
        self.grid.addWidget(title, 0, 0, 1, 7)
        for col, label in enumerate(["Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do"]):
            day = QLabel(label)
            day.setObjectName("calendarDow")
            day.setAlignment(Qt.AlignCenter)
            self.grid.addWidget(day, 1, col)
        first_weekday = datetime(year, month, 1).weekday()
        days = monthrange(year, month)[1]
        today = datetime.fromtimestamp(now_ts()).date()
        for day_number in range(1, days + 1):
            row = 2 + (first_weekday + day_number - 1) // 7
            col = (first_weekday + day_number - 1) % 7
            label = QLabel(str(day_number))
            label.setFixedSize(26, 24)
            mark = marks.get(day_number)
            if today.year == year and today.month == month and today.day == day_number:
                label.setObjectName("calendarToday")
            elif mark:
                label.setObjectName(f"calendarMark-{mark}")
            else:
                label.setObjectName("calendarDay")
            label.setAlignment(Qt.AlignCenter)
            self.grid.addWidget(label, row, col)

    def _clear(self) -> None:
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
