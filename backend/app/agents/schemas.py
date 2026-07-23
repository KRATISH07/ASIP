from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class InfrastructureDiagnosis(BaseModel):
    probable_cause: str = Field(description="technical root cause of the incident")
    recommended_action: str = Field(description="specific physical repair steps to be taken")
    confidence: float = Field(ge=0.0, le=1.0, description="confidence score between 0.0 and 1.0")
    retrieved_context: str = Field(description="brief summary of relevant documentation/history used")


class ContractorSelection(BaseModel):
    contractor_id: Optional[str] = Field(None, description="unique database UUID of the selected contractor")
    contractor_name: str = Field(description="name of the contractor")
    estimated_cost: float = Field(ge=0.0, description="estimated cost of the repair in INR")
    estimated_time_hrs: float = Field(ge=0.0, description="estimated repair time in hours")
    selection_reasoning: str = Field(description="reasoning for selecting this specific contractor")


class NotificationDraft(BaseModel):
    channel: Literal["email", "sms", "push_notification"] = Field(description="communication channel")
    subject: str = Field(description="subject line (empty for SMS)")
    content: str = Field(description="full notification message body (SMS must be under 160 characters)")
    recipient_type: Literal["residents", "management", "maintenance"] = Field(description="intended recipient audience")


class NotificationListSchema(BaseModel):
    notifications: List[NotificationDraft] = Field(
        description="list of three tailored notification drafts (residents, management, maintenance)"
    )


class SupervisorReportSchema(BaseModel):
    incident_summary: str = Field(description="2-3 sentence executive summary of the incident and status")
    root_cause: str = Field(description="technical root cause of the issue")
    impact_summary: str = Field(description="summary of residents and systems affected")
    action_plan: str = Field(description="numbered steps detailing the action and repair plan")
    estimated_resolution_hrs: float = Field(ge=0.0, description="total estimated resolution time in hours")
    priority: Literal["low", "medium", "high", "critical"] = Field(description="priority level classification")
