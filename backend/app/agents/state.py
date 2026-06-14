"""
ASIPState: the shared typed state passed between all LangGraph nodes.
Every agent reads from and writes to this state dict.
This file was extended to support supervisor orchestration state fields.
"""
from typing import TypedDict, Optional, List, Any, Dict


class IncidentEvent(TypedDict):
    type: str           # IncidentType enum value
    severity: str       # IncidentSeverity enum value
    confidence: float
    description: str
    timestamp: str


class DiagnosisReport(TypedDict):
    probable_cause: str
    recommended_action: str
    confidence: float
    retrieved_context: Optional[str]


class ImpactReport(TypedDict):
    affected_towers: List[str]
    affected_apartments: int
    estimated_residents: int
    severity_score: float
    priority: str


class ContractorRecommendation(TypedDict):
    contractor_id: Optional[str]
    contractor_name: str
    estimated_cost: float
    estimated_time_hrs: float
    selection_reasoning: str


class NotificationPayload(TypedDict):
    channel: str
    subject: str
    content: str
    recipient_type: str   # "all_residents" | "affected_tower" | "management"


class FinalReport(TypedDict):
    incident_summary: str
    root_cause: str
    impact_summary: str
    action_plan: str
    contractor: Optional[ContractorRecommendation]
    estimated_resolution_hrs: float
    priority: str


class AutonomousDecision(TypedDict):
    requires_immediate_escalation: bool
    should_notify_residents: bool
    notification_priority: str
    should_activate_backup_system: bool
    auto_dispatch_contractor: bool
    recommended_contractor: Optional[str]
    estimated_risk_score: float
    decision_reasoning: str


class AgentOutput(TypedDict):
    agent_name: str
    decision: Optional[str]
    confidence: float
    reasoning: Optional[str]
    output: Optional[Any]


class ASIPState(TypedDict):
    incident_id: str
    sensor_data: dict
    incident_event: Optional[IncidentEvent]
    diagnosis: Optional[DiagnosisReport]
    impact: Optional[ImpactReport]
    contractor_recommendation: Optional[ContractorRecommendation]
    notifications: Optional[List[NotificationPayload]]
    final_report: Optional[FinalReport]
    error: Optional[str]
    next: str

    # Supervisor orchestration fields
    selected_agents: Optional[List[str]]
    completed_agents: Optional[List[str]]
    agent_outputs: Optional[Dict[str, AgentOutput]]
    supervisor_decisions: Optional[Dict[str, Any]]

    # V4 Autonomous Decision Engine
    autonomous_decision: Optional[Dict[str, Any]]
