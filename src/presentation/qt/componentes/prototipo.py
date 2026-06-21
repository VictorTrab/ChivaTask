"""Componentes visuales inspirados en el prototipo Figma Make."""

from __future__ import annotations

from calendar import monthrange
from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics, QIcon
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
        return "Manana"
    return f"En {diff_days} dias"


def elided(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 1)].rstrip() + "..."


def set_elided_text(label: QLabel, text: str, max_width: int) -> None:
    label.setToolTip(text)
    label.setText(QFontMetrics(label.font()).elidedText(text, Qt.ElideRight, max_width))


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
        self.setMinimumHeight(64 if compact else 76)
        self.setMaximumHeight(78 if compact else 92)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10 if compact else 13, 16, 10 if compact else 13)
        layout.setSpacing(12)

        dot = QLabel()
        dot.setObjectName(f"taskDot-{CHIP_VARIANT[bucket]}")
        dot.setFixedSize(8, 8)

        title_box = QVBoxLayout()
        title_box.setSpacing(3)
        title = QLabel(elided(task.name, 72 if compact else 90))
        title.setObjectName("taskRowTitle")
        title.setWordWrap(True)
        title.setToolTip(task.name)
        meta_text = task.course_shortname or task.course_fullname
        meta = QLabel(elided(meta_text, 56))
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
        chip.setMaximumWidth(112)
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


class CourseCard(QFrame):
    selected = Signal(object)
    view_tasks = Signal(object)

    def __init__(self, summary: dict[str, object]) -> None:
        super().__init__()
        self.summary = summary
        pending = int(summary["pending"])
        total = int(summary["total"])
        submitted = int(summary["submitted"])
        progress = int((submitted / total) * 100) if total else 0
        self.setObjectName("courseCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumWidth(300)
        self.setMaximumWidth(860)
        self.setMinimumHeight(194)
        self.setMaximumHeight(220)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(10)
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
        name = QLabel(elided(fullname, 58))
        name.setObjectName("courseName")
        name.setWordWrap(True)
        name.setToolTip(fullname)
        titles.addWidget(code)
        titles.addWidget(name)

        status = StatusChip("Al dia" if pending == 0 else "Pendiente", "ok" if pending == 0 else "overdue")
        status.setMaximumWidth(92)
        header.addWidget(initials)
        header.addLayout(titles, 1)
        header.addWidget(status)

        progress_label = QLabel(f"{submitted} de {total} entregadas")
        progress_label.setObjectName("courseMeta")
        bar = QProgressBar()
        bar.setObjectName("courseProgress")
        bar.setRange(0, 100)
        bar.setValue(progress)

        footer = QHBoxLayout()
        footer.setSpacing(8)
        pending_label = QLabel("Sin pendientes" if pending == 0 else f"{pending} pendiente{'s' if pending != 1 else ''}")
        pending_label.setObjectName("courseMeta")
        tasks_button = QPushButton("Ver tareas")
        tasks_button.setObjectName("secondarySmallButton")
        tasks_button.setMaximumWidth(104)
        tasks_button.clicked.connect(lambda: self.view_tasks.emit(self.summary))
        campus_button = QPushButton("Campus")
        campus_button.setObjectName("primarySmallButton")
        campus_button.setMaximumWidth(86)
        footer.addWidget(pending_label, 1)
        if pending:
            footer.addWidget(tasks_button)
        footer.addWidget(campus_button)

        layout.addLayout(header)
        layout.addWidget(progress_label)
        layout.addWidget(bar)
        layout.addLayout(footer)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selected.emit(self.summary)
        super().mousePressEvent(event)


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
        self.setText("ON" if self._checked else "OFF")
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
            button.clicked.connect(lambda _=False, option=value: self.set_value(option))
            layout.addWidget(button)
            self.buttons[value] = button
        self._refresh()

    def set_value(self, value: str) -> None:
        self.selected = value
        self._refresh()
        self.changed.emit(value)

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
        self.setMinimumHeight(156)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        self.value_label = QLabel(f"{value}%")
        self.value_label.setObjectName("progressRingValue")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.label_label = QLabel(label)
        self.label_label.setObjectName("progressRingLabel")
        self.label_label.setAlignment(Qt.AlignCenter)
        self.label_label.setWordWrap(True)
        self.bar = QProgressBar()
        self.bar.setObjectName("ringBar")
        self.bar.setRange(0, 100)
        self.bar.setValue(value)
        layout.addWidget(self.value_label)
        layout.addWidget(self.label_label)
        layout.addWidget(self.bar)

    def update_value(self, value: int, label: str | None = None) -> None:
        self.value_label.setText(f"{value}%")
        self.bar.setValue(value)
        if label:
            self.label_label.setText(label)


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
