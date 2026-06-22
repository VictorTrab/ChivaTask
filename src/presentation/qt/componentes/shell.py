"""Componentes del shell principal."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSizePolicy, QVBoxLayout


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
        self.text_label = QLabel("Sin sincronizar")
        self.text_label.setObjectName("statusText")
        self.detail_label = QLabel("")
        self.detail_label.setObjectName("statusDetail")
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
        layout.addWidget(self.detail_label)

    def set_status(self, text: str, variant: str, detail: str = "") -> None:
        self.text_label.setText(text)
        self.detail_label.setText(detail)
        self.detail_label.setVisible(bool(detail))
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
        self.setFixedWidth(340)
        self.hide()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        header = QHBoxLayout()
        header.setSpacing(8)
        self.title_label = QLabel("")
        self.title_label.setObjectName("syncToastTitle")
        self.close_button = QPushButton("x")
        self.close_button.setObjectName("syncToastClose")
        self.close_button.setAccessibleName("Cerrar aviso de sincronización")
        self.close_button.clicked.connect(self.hide)
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
        self.setObjectName("syncToastError" if variant == "error" else "syncToastSuccess")
        self.title_label.setText(title)
        self.detail_label.setText(detail)
        self.retry_button.setVisible(retry)
        self._refresh_style()
        self.show()
        self.raise_()
        self._timer.start(7000 if variant == "error" else 4200)

    def _refresh_style(self) -> None:
        self.style().unpolish(self)
        self.style().polish(self)
        for child in (self.title_label, self.detail_label, self.close_button, self.retry_button):
            child.style().unpolish(child)
            child.style().polish(child)
