"""Tokens visuales de ChivaTask para mantener consistencia."""

from PySide6.QtWidgets import QApplication

from .estilos import app_stylesheet

APP_DISPLAY_NAME = "ChivaTask"

COLOR_VERDE_PROFUNDO = "#123F35"
COLOR_VERDE_ACCION = "#16775F"
COLOR_VERDE_HOVER = "#0F5F4A"
COLOR_FONDO = "#F5F7FA"
COLOR_SUPERFICIE = "#FFFFFF"
COLOR_BORDE = "#D8E2EA"
COLOR_TEXTO = "#102033"
COLOR_TEXTO_SECUNDARIO = "#64748B"
COLOR_AMBAR = "#D97706"
COLOR_ROJO = "#DC2626"
COLOR_AZUL = "#2563EB"

RADIO_BOTON = 10
RADIO_CARD = 12
RADIO_MODAL = 14


def apply_application_theme(visual_mode: str = "claro") -> None:
    """Aplica el QSS global para ventanas, dialogos y popups."""
    app = QApplication.instance()
    if app is not None:
        app.setStyleSheet(app_stylesheet(visual_mode))
