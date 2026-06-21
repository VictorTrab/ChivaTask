"""Compatibilidad: expone el gateway Moodle con nombres historicos."""

from infrastructure.moodle import MoodleCampusGateway
from shared.errores import CampusError

MoodleApiError = CampusError
MoodleClient = MoodleCampusGateway

__all__ = ["MoodleApiError", "MoodleClient"]
