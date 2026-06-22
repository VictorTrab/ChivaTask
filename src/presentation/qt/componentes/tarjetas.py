"""Tarjetas reutilizables para metricas y paneles."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


class StatCard(QFrame):
    def __init__(self, icon: QIcon, value: str, label: str, variant: str = "default") -> None:
        super().__init__()
        self.setObjectName(f"statCard-{variant}")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)
        icon_label = QLabel()
        icon_label.setObjectName("statIcon")
        icon_label.setPixmap(icon.pixmap(26, 26))
        texts = QVBoxLayout()
        self.value_label = QLabel(value)
        self.value_label.setObjectName("statValue")
        self.label_label = QLabel(label)
        self.label_label.setObjectName("statLabel")
        texts.addWidget(self.value_label)
        texts.addWidget(self.label_label)
        layout.addWidget(icon_label)
        layout.addLayout(texts)
        layout.addStretch(1)

    def update_value(self, value: str, label: str | None = None) -> None:
        self.value_label.setText(value)
        if label is not None:
            self.label_label.setText(label)


class DetailPanel(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("detailPanel")
        self.setMinimumWidth(310)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(18, 18, 18, 18)
        self.layout.setSpacing(12)
        self.layout.setAlignment(Qt.AlignTop)


class InfoCard(QFrame):
    def __init__(self, label: str, value: str, variant: str = "default") -> None:
        super().__init__()
        self.setObjectName(f"infoCard-{variant}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)
        self.label_label = QLabel(label)
        self.label_label.setObjectName("infoCardLabel")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("infoCardValue")
        self.value_label.setWordWrap(True)
        layout.addWidget(self.label_label)
        layout.addWidget(self.value_label)

    def update_value(self, label: str, value: str) -> None:
        self.label_label.setText(label)
        self.value_label.setText(value)
