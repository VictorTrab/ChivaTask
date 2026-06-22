"""Componentes del shell principal."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QSizePolicy


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
        self.setMaximumWidth(260)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 7, 12, 7)
        layout.setSpacing(8)
        self.icon_label = QLabel()
        self.icon_label.setObjectName("statusIcon")
        self.icon_label.setPixmap(icon.pixmap(14, 14))
        self.text_label = QLabel("Sin sincronizar")
        self.text_label.setObjectName("statusText")
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)

    def set_status(self, text: str, variant: str) -> None:
        self.text_label.setText(text)
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
        self.text_label.style().unpolish(self.text_label)
        self.text_label.style().polish(self.text_label)
