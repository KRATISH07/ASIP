import uuid
from typing import Optional, List
from pydantic import BaseModel, EmailStr


class ContractorCreate(BaseModel):
    name: str
    specializations: List[str]
    rating: float = 3.0
    avg_response_time_hrs: float = 4.0
    contact_info: dict


class ContractorOut(BaseModel):
    id: uuid.UUID
    name: str
    specializations: List[str]
    rating: float
    avg_response_time_hrs: float
    total_jobs: int
    success_rate: float
    contact_info: dict
    is_active: bool

    model_config = {"from_attributes": True}


class NotificationOut(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    recipient_id: Optional[uuid.UUID] = None
    channel: str
    subject: Optional[str] = None
    content: str
    status: str
    sent_at: Optional[str] = None

    model_config = {"from_attributes": True}


class AgentLogOut(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    agent_name: str
    execution_time_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    status: str
    error: Optional[str] = None
    input_payload: Optional[dict] = None
    output_payload: Optional[dict] = None
    created_at: str

    model_config = {"from_attributes": True}
