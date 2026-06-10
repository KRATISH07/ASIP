"""
Import all models here so Alembic can discover them via metadata.
"""
from app.db.base import Base  # noqa: F401
from app.db.models.tower import Tower, InfrastructureType  # noqa: F401
from app.db.models.resident import Apartment, Resident, ResidentRole  # noqa: F401
from app.db.models.user import User, UserRole  # noqa: F401
from app.db.models.incident import (  # noqa: F401
    Incident, IncidentType, IncidentSeverity, IncidentStatus
)
from app.db.models.contractor import Contractor, ContractorAssignment  # noqa: F401
from app.db.models.contractor_history import ContractorHistory  # noqa: F401
from app.db.models.notification import Notification, NotificationChannel, NotificationStatus  # noqa: F401
from app.db.models.agent_log import AgentLog  # noqa: F401
from app.db.models.maintenance_record import MaintenanceRecord, HistoricalIncident  # noqa: F401
from app.db.models.incident_memory import IncidentMemory  # noqa: F401

__all__ = [
    "Base",
    "Tower", "InfrastructureType",
    "Apartment", "Resident", "ResidentRole",
    "User", "UserRole",
    "Incident", "IncidentType", "IncidentSeverity", "IncidentStatus",
    "Contractor", "ContractorAssignment",
    "ContractorHistory",
    "Notification", "NotificationChannel", "NotificationStatus",
    "AgentLog",
    "MaintenanceRecord", "HistoricalIncident",
    "IncidentMemory",
]
