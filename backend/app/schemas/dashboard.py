from typing import List, Optional
from pydantic import BaseModel


class DashboardKPI(BaseModel):
    total_incidents: int
    active_incidents: int
    critical_incidents: int
    resolved_today: int
    avg_resolution_time_hrs: Optional[float] = None


class RecentIncidentSummary(BaseModel):
    id: str
    type: str
    severity: str
    status: str
    tower_name: Optional[str] = None
    detected_at: str


class AgentActivitySummary(BaseModel):
    agent_name: str
    executions_today: int
    avg_execution_time_ms: Optional[float] = None
    success_rate: float


class DashboardOut(BaseModel):
    kpi: DashboardKPI
    recent_incidents: List[RecentIncidentSummary]
    agent_activity: List[AgentActivitySummary]
    severity_distribution: dict  # {"low": 5, "medium": 3, "high": 2, "critical": 1}
    incident_trend: List[dict]  # [{"date": "2026-06-01", "count": 5}, ...]


class AnalyticsOut(BaseModel):
    incident_trend: List[dict]
    resolution_time_trend: List[dict]
    contractor_performance: List[dict]
    severity_distribution: dict
    incident_type_distribution: dict
