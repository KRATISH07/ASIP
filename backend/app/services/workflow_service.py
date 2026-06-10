"""
WorkflowService orchestrates the LangGraph multi-agent pipeline.
It is called from the sensor-data endpoint and runs the full
Monitoring → Supervisor → Infrastructure → Impact → Contractor → Communication workflow.
"""
import time
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.repositories.incident_repo import IncidentRepository
from app.repositories.notification_repo import AgentLogRepository
from app.db.models.incident import Incident, IncidentStatus

logger = get_logger("workflow_service")


class WorkflowService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.incident_repo = IncidentRepository(db)
        self.log_repo = AgentLogRepository(db)

    async def process_sensor_data(self, sensor_payload: dict) -> Optional[Incident]:
        """
        Entry point: receives sensor data, runs the full agent workflow.
        Returns the created Incident if one was detected, else None.
        """
        from app.agents.graph import build_graph
        from app.agents.state import ASIPState

        logger.info("Processing sensor data", tower_id=sensor_payload.get("tower_id"))

        graph = build_graph()

        initial_state: ASIPState = {
            "sensor_data": sensor_payload,
            "incident_event": None,
            "diagnosis": None,
            "impact": None,
            "contractor_recommendation": None,
            "notifications": None,
            "final_report": None,
            "error": None,
            "next": "monitoring_agent",
            "incident_id": str(uuid.uuid4()),
        }

        start = time.time()
        try:
            final_state = await graph.ainvoke(initial_state)
        except Exception as e:
            logger.error("Agent workflow failed", error=str(e))
            return None
        elapsed_ms = int((time.time() - start) * 1000)

        # If no incident was detected by monitoring agent, stop
        if not final_state.get("incident_event"):
            logger.info("No incident detected from sensor data")
            return None

        # Persist incident
        event = final_state["incident_event"]
        incident_data = {
            "id": uuid.UUID(initial_state["incident_id"]),
            "type": event["type"],
            "severity": event["severity"],
            "confidence": event.get("confidence", 0.8),
            "status": IncidentStatus.action_planned,
            "tower_id": uuid.UUID(str(sensor_payload["tower_id"])),
            "description": event.get("description"),
            "sensor_data": sensor_payload,
            "ai_decision": final_state.get("final_report"),
            "detected_at": datetime.now(timezone.utc),
        }
        incident = await self.incident_repo.create(incident_data)

        logger.info(
            "Incident persisted",
            incident_id=str(incident.id),
            severity=incident.severity.value,
            elapsed_ms=elapsed_ms,
        )
        return incident

    async def _save_agent_log(
        self,
        incident_id: str,
        agent_name: str,
        input_payload: dict,
        output_payload: dict,
        execution_time_ms: int,
    ) -> None:
        await self.log_repo.create({
            "incident_id": uuid.UUID(incident_id),
            "agent_name": agent_name,
            "input_payload": input_payload,
            "output_payload": output_payload,
            "execution_time_ms": execution_time_ms,
            "status": "success",
        })
