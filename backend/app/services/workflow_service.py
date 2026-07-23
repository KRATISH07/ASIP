"""
Workflow orchestrator: ties together FastAPI, LangGraph, and PostgreSQL.
It is called from the sensor-data endpoint and runs the full
Monitoring → Supervisor → Infrastructure → Impact → Contractor → Communication workflow.
"""
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.request_context import get_trace_id
from app.repositories.incident_repo import IncidentRepository
from app.repositories.notification_repo import AgentLogRepository
from app.repositories.workflow_run_repo import WorkflowRunRepository
from app.db.models.incident import Incident, IncidentStatus
from app.db.models.workflow_run import WorkflowRun, WorkflowRunStatus

logger = get_logger("workflow_service")

# State schema version — bump when ASIPState structure changes.
# Stored in every state dict so agents can migrate forward during rolling deploys.
_STATE_SCHEMA_VERSION = "v5.1"


class WorkflowService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.incident_repo = IncidentRepository(db)
        self.log_repo = AgentLogRepository(db)
        self.workflow_run_repo = WorkflowRunRepository(db)

    async def process_sensor_data(
        self, sensor_payload: dict, incident_id: Optional[str] = None
    ) -> Optional[Incident]:
        """
        Entry point: receives sensor data, runs the full agent workflow.
        Returns the created Incident if one was detected, else None.
        """
        from app.agents.graph import get_compiled_graph
        from app.agents.state import ASIPState

        logger.info("Processing sensor data", tower_id=sensor_payload.get("tower_id"))

        graph = get_compiled_graph()

        # Fix #5: Inject correlation trace_id from request context.
        # get_trace_id() reads from Python contextvars — set at the HTTP layer.
        # This propagates through all agent logs without modifying agent signatures.
        # Fix #9: _schema_version field allows forward-migration during rolling deploys.
        trace_id = get_trace_id()
        if incident_id is None:
            incident_id = str(uuid.uuid4())

        initial_incident_event = None
        try:
            existing_incident = await self.incident_repo.get_by_id(uuid.UUID(incident_id))
            if existing_incident:
                initial_incident_event = {
                    "type": existing_incident.type.value if hasattr(existing_incident.type, "value") else str(existing_incident.type),
                    "severity": existing_incident.severity.value if hasattr(existing_incident.severity, "value") else str(existing_incident.severity),
                    "confidence": 1.0,
                    "description": existing_incident.description,
                    "timestamp": existing_incident.detected_at.isoformat() if existing_incident.detected_at else datetime.now(timezone.utc).isoformat()
                }
        except Exception as db_err:
            logger.warning("Failed to lookup existing incident for state initialization", error=str(db_err))

        initial_state: ASIPState = {
            "sensor_data":     sensor_payload,
            "incident_event":  initial_incident_event,
            "diagnosis":       None,
            "impact":          None,
            "contractor_recommendation": None,
            "notifications":   None,
            "final_report":    None,
            "error":           None,
            "next":            "monitoring_agent",
            "incident_id":     incident_id,
            "trace_id":        trace_id,          # Fix #5: correlation ID
            "_schema_version": _STATE_SCHEMA_VERSION,  # Fix #9: schema version
            "agent_logs_to_persist": [],
        }

        # Create workflow run tracking entry
        run = await self.workflow_run_repo.create({
            "incident_id": uuid.UUID(incident_id),
            "status": WorkflowRunStatus.running,
            "current_step": "monitoring_agent",
            "completed_steps": [],
            "retry_count": 0,
        })

        start = time.time()
        config = {"configurable": {"thread_id": incident_id}}
        try:
            final_state = await graph.ainvoke(initial_state, config=config)
        except Exception as e:
            elapsed_ms = int((time.time() - start) * 1000)
            logger.error(
                "Agent workflow failed",
                error=str(e),
                trace_id=trace_id,
                elapsed_ms=elapsed_ms,
            )
            # Retrieve checkpoint state to record step failure details
            completed = []
            next_step = None
            try:
                state_info = await graph.aget_state(config)
                if state_info:
                    completed = state_info.values.get("completed_agents") or []
                    next_step = state_info.next[0] if state_info.next else None
            except Exception as state_err:
                logger.warning("Failed to retrieve state history on failure", error=str(state_err))

            # If incident already exists in DB (e.g., manual complaint), persist logs that completed before failure
            try:
                existing_inc = await self.incident_repo.get_by_id(uuid.UUID(incident_id))
                if existing_inc:
                    state_info = await graph.aget_state(config)
                    if state_info:
                        agent_logs = state_info.values.get("agent_logs_to_persist", [])
                        for log_data in agent_logs:
                            log_data["incident_id"] = existing_inc.id
                            await self.log_repo.create(log_data)
            except Exception as log_err:
                logger.warning("Failed to record completed agent logs on failure", incident_id=incident_id, error=str(log_err))

            await self.workflow_run_repo.update(run.id, {
                "status": WorkflowRunStatus.failed,
                "completed_steps": completed,
                "current_step": next_step,
                "failed_at_step": next_step or "monitoring_agent",
                "last_error": str(e),
            })

            # Fix #10: Record pipeline failures for survivorship bias prevention.
            await self._record_pipeline_failure(
                incident_id=incident_id,
                sensor_payload=sensor_payload,
                error=str(e),
                trace_id=trace_id,
            )
            await self.db.commit()
            return None
        elapsed_ms = int((time.time() - start) * 1000)

        # If no incident was detected by monitoring agent, stop
        if not final_state.get("incident_event"):
            logger.info("No incident detected from sensor data")
            await self.workflow_run_repo.update(run.id, {
                "status": WorkflowRunStatus.completed,
                "completed_steps": final_state.get("completed_agents") or ["monitoring_agent"],
                "current_step": None,
            })
            return None

        # Persist incident
        event = final_state["incident_event"]
        raw_report = final_state.get("final_report") or {}
        versioned_decision = {
            "_asip_schema_version": "v5.1",
            "_generated_at": datetime.now(timezone.utc).isoformat(),
            **raw_report,
        }
        incident_data = {
            "id": uuid.UUID(initial_state["incident_id"]),
            "type": event["type"],
            "severity": event["severity"],
            "confidence": event.get("confidence", 0.8),
            "status": IncidentStatus.action_planned,
            "tower_id": uuid.UUID(str(sensor_payload["tower_id"])),
            "description": event.get("description"),
            "sensor_data": sensor_payload,
            "ai_decision": versioned_decision,
            "detected_at": datetime.now(timezone.utc),
        }
        # Check if the incident already exists (e.g. manual report created via API)
        existing_incident = None
        try:
            existing_incident = await self.incident_repo.get_by_id(uuid.UUID(initial_state["incident_id"]))
        except TypeError:
            pass

        if existing_incident:
            incident_update_data = {
                "type": event["type"],
                "severity": event["severity"],
                "confidence": event.get("confidence", 0.8),
                "status": IncidentStatus.action_planned,
                "ai_decision": versioned_decision,
            }
            if not existing_incident.description:
                incident_update_data["description"] = event.get("description")
            incident = await self.incident_repo.update(existing_incident.id, incident_update_data)
        else:
            incident = await self.incident_repo.create(incident_data)

        # Create contractor assignment if recommendation exists
        contractor_rec = final_state.get("contractor_recommendation")
        if contractor_rec and contractor_rec.get("contractor_id"):
            try:
                from app.repositories.contractor_repo import ContractorRepository
                c_repo = ContractorRepository(self.db)
                await c_repo.create_assignment({
                    "incident_id": incident.id,
                    "contractor_id": uuid.UUID(str(contractor_rec["contractor_id"])),
                    "estimated_cost": contractor_rec.get("estimated_cost"),
                    "estimated_time_hrs": contractor_rec.get("estimated_time_hrs"),
                    "selection_reasoning": contractor_rec.get("selection_reasoning"),
                })
            except Exception as assignment_err:
                logger.warning(
                    "Failed to create contractor assignment",
                    incident_id=str(incident.id),
                    error=str(assignment_err)
                )

        # Store the incident run in history (IncidentMemory) so the learning loop has historical context
        try:
            from app.services.memory_service import store_incident_memory
            await store_incident_memory(final_state)
        except Exception as mem_err:
            logger.warning(
                "Failed to store incident memory during workflow completion",
                incident_id=str(incident.id),
                error=str(mem_err),
            )

        # Persist collected agent logs
        agent_logs = final_state.get("agent_logs_to_persist", [])
        if agent_logs:
            try:
                for log_data in agent_logs:
                    log_data["incident_id"] = incident.id
                    await self.log_repo.create(log_data)
            except Exception as log_err:
                logger.warning(
                    "Failed to persist agent logs at workflow completion",
                    incident_id=str(incident.id),
                    error=str(log_err),
                )

        # Update workflow run to completed
        await self.workflow_run_repo.update(run.id, {
            "status": WorkflowRunStatus.completed,
            "completed_steps": final_state.get("completed_agents") or [],
            "current_step": None,
        })

        await self.db.commit()

        logger.info(
            "Incident persisted",
            incident_id=str(incident.id),
            severity=incident.severity.value,
            elapsed_ms=elapsed_ms,
        )
        return incident

    async def retry_workflow_run(self, run_id: uuid.UUID) -> Optional[Incident]:
        """
        Resumes a failed workflow run from its last checkpoint using LangGraph config.
        If it fails again and exceeds max retries, executes a compensating transaction
        to mark the incident as escalated for manual review.
        """
        from app.agents.graph import get_compiled_graph
        from app.db.models.incident import IncidentStatus

        run = await self.workflow_run_repo.get_by_id(run_id)
        if not run or run.status not in (WorkflowRunStatus.failed, WorkflowRunStatus.pending):
            logger.warning("Workflow run not eligible for retry", run_id=str(run_id))
            return None

        # Increment retry count and set status to running
        run = await self.workflow_run_repo.update(run_id, {
            "retry_count": run.retry_count + 1,
            "status": WorkflowRunStatus.running,
        })
        await self.db.commit()

        graph = get_compiled_graph()
        config = {"configurable": {"thread_id": str(run.incident_id)}}

        try:
            # Resume LangGraph execution from last checkpoint
            final_state = await graph.ainvoke(None, config=config)
        except Exception as e:
            completed = []
            next_step = None
            try:
                state_info = await graph.aget_state(config)
                if state_info:
                    completed = state_info.values.get("completed_agents") or []
                    next_step = state_info.next[0] if state_info.next else None
            except Exception as state_err:
                logger.warning("Failed to retrieve state history on retry failure", error=str(state_err))

            max_retries = 3
            if run.retry_count >= max_retries:
                # Compensating: update status to compensating and register escalated incident
                logger.error("Workflow run exceeded max retries. Transitioning to compensating.", run_id=str(run_id))
                await self.workflow_run_repo.update(run_id, {
                    "status": WorkflowRunStatus.compensating,
                    "completed_steps": completed,
                    "current_step": None,
                    "failed_at_step": next_step or run.failed_at_step,
                    "last_error": str(e),
                })

                # Retrieve sensor payload from checkpointer state
                sensor_data = {}
                if state_info and state_info.values.get("sensor_data"):
                    sensor_data = state_info.values.get("sensor_data")

                incident_data = {
                    "id": run.incident_id,
                    "type": sensor_data.get("sensor_type") or "abnormal_infrastructure",
                    "severity": sensor_data.get("severity") or "high",
                    "confidence": 0.5,
                    "status": IncidentStatus.escalated,
                    "tower_id": uuid.UUID(sensor_data.get("tower_id")) if sensor_data.get("tower_id") else None,
                    "description": f"Automation pipeline failed to complete. Last error: {e}. Requires manual review.",
                    "sensor_data": sensor_data,
                    "ai_decision": {
                        "requires_manual_review": True,
                        "failed_step": next_step or run.failed_at_step,
                        "last_error": str(e),
                        "retry_count": run.retry_count,
                    },
                    "detected_at": datetime.now(timezone.utc),
                }

                try:
                    incident = await self.incident_repo.create(incident_data)
                    await self.db.commit()
                    return incident
                except Exception as db_err:
                    logger.error("Failed to create compensating incident", error=str(db_err))
                    await self.db.commit()
                    return None
            else:
                await self.workflow_run_repo.update(run_id, {
                    "status": WorkflowRunStatus.failed,
                    "completed_steps": completed,
                    "current_step": next_step,
                    "failed_at_step": next_step or run.failed_at_step,
                    "last_error": str(e),
                })
                await self.db.commit()
                return None

        # Success path on retry
        if not final_state.get("incident_event"):
            await self.workflow_run_repo.update(run_id, {
                "status": WorkflowRunStatus.completed,
                "completed_steps": final_state.get("completed_agents") or ["monitoring_agent"],
                "current_step": None,
            })
            await self.db.commit()
            return None

        sensor_payload = final_state.get("sensor_data") or {}
        event = final_state["incident_event"]
        raw_report = final_state.get("final_report") or {}
        versioned_decision = {
            "_asip_schema_version": "v5.1",
            "_generated_at": datetime.now(timezone.utc).isoformat(),
            **raw_report,
        }
        incident_data = {
            "id": run.incident_id,
            "type": event["type"],
            "severity": event["severity"],
            "confidence": event.get("confidence", 0.8),
            "status": IncidentStatus.action_planned,
            "tower_id": uuid.UUID(str(sensor_payload["tower_id"])) if sensor_payload.get("tower_id") else None,
            "description": event.get("description"),
            "sensor_data": sensor_payload,
            "ai_decision": versioned_decision,
            "detected_at": datetime.now(timezone.utc),
        }

        existing_incident = None
        try:
            # Check if the incident already exists (e.g. manual report created via API)
            existing_incident = await self.incident_repo.get_by_id(incident_data["id"])
        except TypeError:
            pass

        try:
            if existing_incident:
                incident_update_data = {
                    "type": event["type"],
                    "severity": event["severity"],
                    "confidence": event.get("confidence", 0.8),
                    "status": IncidentStatus.action_planned,
                    "ai_decision": versioned_decision,
                }
                if not existing_incident.description:
                    incident_update_data["description"] = event.get("description")
                incident = await self.incident_repo.update(existing_incident.id, incident_update_data)
            else:
                incident = await self.incident_repo.create(incident_data)

            # Create contractor assignment if recommendation exists
            contractor_rec = final_state.get("contractor_recommendation")
            if contractor_rec and contractor_rec.get("contractor_id"):
                try:
                    from app.repositories.contractor_repo import ContractorRepository
                    c_repo = ContractorRepository(self.db)
                    await c_repo.create_assignment({
                        "incident_id": incident.id,
                        "contractor_id": uuid.UUID(str(contractor_rec["contractor_id"])),
                        "estimated_cost": contractor_rec.get("estimated_cost"),
                        "estimated_time_hrs": contractor_rec.get("estimated_time_hrs"),
                        "selection_reasoning": contractor_rec.get("selection_reasoning"),
                    })
                except Exception as assignment_err:
                    logger.warning(
                        "Failed to create contractor assignment on retry",
                        incident_id=str(incident.id),
                        error=str(assignment_err)
                    )

            try:
                from app.services.memory_service import store_incident_memory
                await store_incident_memory(final_state)
            except Exception as mem_err:
                logger.warning("Failed to store incident memory during retry completion", error=str(mem_err))

            await self.workflow_run_repo.update(run_id, {
                "status": WorkflowRunStatus.completed,
                "completed_steps": final_state.get("completed_agents") or [],
                "current_step": None,
            })
            await self.db.commit()
            return incident
        except Exception as db_err:
            logger.error("Failed to persist incident on successful retry", error=str(db_err))
            await self.db.commit()
            return None

    async def reconcile_failed_runs(self, max_retries: int = 3) -> List[Incident]:
        """Query failed workflow runs and retry them."""
        failed_runs = await self.workflow_run_repo.get_runnable_retries(max_retries=max_retries)
        logger.info(f"Reconciler found {len(failed_runs)} runnable failed workflow runs.")

        incidents = []
        for run in failed_runs:
            logger.info("Reconciler retrying workflow run", run_id=str(run.id), incident_id=str(run.incident_id))
            try:
                incident = await self.retry_workflow_run(run.id)
                if incident:
                    incidents.append(incident)
            except Exception as e:
                logger.error(f"Reconciler error during retry of run {run.id}", error=str(e))

        return incidents

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

    async def _record_pipeline_failure(
        self,
        incident_id: str,
        sensor_payload: dict,
        error: str,
        trace_id: str,
    ) -> None:
        """Record pipeline failures as structured log entries (Fix #10)."""
        try:
            incident_type = sensor_payload.get("sensor_type") or sensor_payload.get("incident_type") or "unknown"
            severity = sensor_payload.get("severity") or "unknown"
            error_category = (
                "llm_timeout"    if "timeout" in error.lower() else
                "llm_rate_limit" if "rate" in error.lower() else
                "db_error"       if "sqlalchemy" in error.lower() or "asyncpg" in error.lower() else
                "chroma_error"   if "chroma" in error.lower() else
                "unknown"
            )
            logger.warning(
                "Pipeline failure recorded for learning loop",
                incident_id=incident_id,
                incident_type=incident_type,
                severity=severity,
                error_category=error_category,
                trace_id=trace_id,
            )
        except Exception:
            pass  # failure recording must never raise

