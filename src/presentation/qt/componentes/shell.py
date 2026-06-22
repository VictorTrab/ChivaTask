"""Componentes del shell principal."""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRect, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from presentation.qt.animaciones import animations_enabled


class NavItem(QFrame):
    clicked = Signal()

    def __init__(self, icon: QIcon, text: str) -> None:
        super().__init__()
        self.setObjectName("navItem")
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(42)
        self.setAccessibleName(text)
        self._active = False
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 10, 8)
        layout.setSpacing(10)
        icon_label = QLabel()
        icon_label.setObjectName("navIcon")
        icon_label.setPixmap(icon.pixmap(18, 18))
        self.text_label = QLabel(text)
        self.text_label.setObjectName("navItemText")
        self.badge = QLabel("")
        self.badge.setObjectName("navBadge")
        self.badge.setAlignment(Qt.AlignCenter)
        self.badge.setVisible(False)
        layout.addWidget(icon_label)
        layout.addWidget(self.text_label, 1)
        layout.addWidget(self.badge)

    def set_active(self, active: bool) -> None:
        self._active = active
        self.setObjectName("navItemActive" if active else "navItem")
        self.text_label.setObjectName("navItemTextActive" if active else "navItemText")
        self.badge.setObjectName("navBadgeActive" if active else "navBadge")
        self._refresh_style()

    def set_badge(self, value: int | str | None) -> None:
        text = "" if value in (None, "", 0, "0") else str(value)
        self.badge.setText(text)
        self.badge.setVisible(bool(text))
        self._refresh_style()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.clicked.emit()
            return
        super().keyPressEvent(event)

    def _refresh_style(self) -> None:
        self.style().unpolish(self)
        self.style().polish(self)
        for child in (self.text_label, self.badge):
            child.style().unpolish(child)
            child.style().polish(child)


class SearchField(QLineEdit):
    def __init__(self, icon: QIcon, placeholder: str) -> None:
        super().__init__()
        self.setObjectName("searchField")
        self.setPlaceholderText(placeholder)
        self.addAction(icon, QLineEdit.LeadingPosition)
        self.setClearButtonEnabled(True)


class LoadingSpinner(QFrame):
    def __init__(self, size: int = 18) -> None:
        super().__init__()
        self.setObjectName("loadingSpinner")
        self.setFixedSize(size, size)
        self.angle = 0
        self._timer = QTimer(self)
        self._timer.setInterval(80)
        self._timer.timeout.connect(self._tick)
        self.hide()

    def start(self) -> None:
        if not animations_enabled():
            self.angle = 0
            self.show()
            self.update()
            return
        self.show()
        if not self._timer.isActive():
            self._timer.start()

    def stop(self) -> None:
        self._timer.stop()
        self.hide()

    def _tick(self) -> None:
        self.angle = (self.angle + 30) % 360
        self.update()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        side = min(self.width(), self.height()) - 4
        rect = QRect(2, 2, side, side)
        track = QPen(QColor("#B7E4D4"), 2)
        track.setCapStyle(Qt.RoundCap)
        accent = QPen(QColor("#16775F"), 2)
        accent.setCapStyle(Qt.RoundCap)
        painter.setPen(track)
        painter.drawArc(rect, 0, 360 * 16)
        painter.setPen(accent)
        painter.drawArc(rect, int(self.angle * 16), 110 * 16)


class SyncStatusPill(QFrame):
    def __init__(self, icon: QIcon) -> None:
        super().__init__()
        self.icon = icon
        self.setObjectName("statusPending")
        self.setMinimumHeight(36)
        self.setMaximumWidth(300)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 7, 12, 7)
        layout.setSpacing(7)
        self.icon_label = QLabel()
        self.icon_label.setObjectName("statusIcon")
        self.icon_label.setPixmap(icon.pixmap(14, 14))
        self.spinner = LoadingSpinner(16)
        self.text_label = QLabel("Sin sincronizar")
        self.text_label.setObjectName("statusText")
        self.detail_label = QLabel("")
        self.detail_label.setObjectName("statusDetail")
        layout.addWidget(self.icon_label)
        layout.addWidget(self.spinner)
        layout.addWidget(self.text_label)
        layout.addWidget(self.detail_label)

    def set_status(self, text: str, variant: str, detail: str = "") -> None:
        self.text_label.setText(text)
        self.detail_label.setText(detail)
        self.detail_label.setVisible(bool(detail))
        if variant == "syncing":
            self.icon_label.hide()
            self.spinner.start()
        else:
            self.spinner.stop()
            self.icon_label.show()
        self.setObjectName(
            {
                "ok": "statusOk",
                "error": "statusError",
                "syncing": "statusSyncing",
                "pending": "statusPending",
            }[variant]
        )
        self._refresh_style()

    def setText(self, text: str) -> None:  # noqa: N802 - compatibilidad con QLabel usado antes
        self.text_label.setText(text)

    def text(self) -> str:
        return self.text_label.text()

    def _refresh_style(self) -> None:
        self.style().unpolish(self)
        self.style().polish(self)
        for child in (self.text_label, self.detail_label):
            child.style().unpolish(child)
            child.style().polish(child)


class SyncToast(QFrame):
    retry_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("syncToastSuccess")
        self.setWindowFlags(Qt.Widget)
        self.setMinimumWidth(340)
        self.setMaximumWidth(460)
        self.hide()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide_animated)
        self._opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity)
        self._fade = QPropertyAnimation(self._opacity, b"opacity", self)
        self._fade.setEasingCurve(QEasingCurve.OutCubic)
        self._hide_connected = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        header = QHBoxLayout()
        header.setSpacing(8)
        self.icon_label = QLabel("")
        self.icon_label.setObjectName("syncToastIcon")
        self.icon_label.setFixedSize(24, 24)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.title_label = QLabel("")
        self.title_label.setObjectName("syncToastTitle")
        self.close_button = QPushButton("x")
        self.close_button.setObjectName("syncToastClose")
        self.close_button.setAccessibleName("Cerrar aviso de sincronización")
        self.close_button.clicked.connect(self.hide_animated)
        header.addWidget(self.icon_label)
        header.addWidget(self.title_label, 1)
        header.addWidget(self.close_button)
        self.detail_label = QLabel("")
        self.detail_label.setObjectName("syncToastDetail")
        self.detail_label.setWordWrap(True)
        self.retry_button = QPushButton("Reintentar")
        self.retry_button.setObjectName("syncToastRetry")
        self.retry_button.setAccessibleName("Reintentar sincronización")
        self.retry_button.clicked.connect(self.retry_requested.emit)
        layout.addLayout(header)
        layout.addWidget(self.detail_label)
        layout.addWidget(self.retry_button, 0, Qt.AlignRight)

    def show_message(self, title: str, detail: str, variant: str, retry: bool = False) -> None:
        self._timer.stop()
        self._fade.stop()
        self.setObjectName("syncToastError" if variant == "error" else "syncToastSuccess")
        self.icon_label.setText("!" if variant == "error" else "OK")
        self.title_label.setText(title)
        self.detail_label.setText(detail)
        self.retry_button.setVisible(retry)
        self._refresh_style()
        self.adjustSize()
        self.show()
        self.raise_()
        self._animate_opacity(0.0, 1.0)
        self._timer.start(7000 if variant == "error" else 5000)

    def hide_animated(self) -> None:
        self._timer.stop()
        if not self.isVisible():
            return
        if not animations_enabled():
            self.hide()
            return
        self._fade.stop()
        self._disconnect_fade_finished()
        self._fade.setDuration(170)
        self._fade.setStartValue(self._opacity.opacity())
        self._fade.setEndValue(0.0)
        self._fade.finished.connect(self.hide)
        self._hide_connected = True
        self._fade.start()

    def _animate_opacity(self, start: float, end: float) -> None:
        self._disconnect_fade_finished()
        if not animations_enabled():
            self._opacity.setOpacity(end)
            return
        self._opacity.setOpacity(start)
        self._fade.setDuration(180)
        self._fade.setStartValue(start)
        self._fade.setEndValue(end)
        self._fade.start()

    def _disconnect_fade_finished(self) -> None:
        if self._hide_connected:
            self._fade.finished.disconnect(self.hide)
            self._hide_connected = False

    def _refresh_style(self) -> None:
        self.style().unpolish(self)
        self.style().polish(self)
        for child in (self.icon_label, self.title_label, self.detail_label, self.close_button, self.retry_button):
            child.style().unpolish(child)
            child.style().polish(child)
