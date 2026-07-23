"""Feedback Service — V4 Learning Loop

Stores post-resolution feedback (actual vs predicted values, decision accuracy)
into the incident_memory table. This enables future predictive models to learn
from real outcomes.

IMPORTANT: memory_service.py is protected and must NOT be modified.
This service handles the feedback write path independently.
"""
import uuid
from typing import Optional
from app.core.logging import get_logger

logger = get_logger("feedback_service")


def _compute_decision_accuracy(
    predicted_outage_hrs: Optional[float],
    actual_outage_hrs: Optional[float],
    predicted_cost: Optional[float],
    actual_cost: Optional[float],
) -> Optional[float]:
    """Compute a 0–1 accuracy score comparing predictions to actuals.

    Uses mean absolute percentage error (MAPE) inverted:
      accuracy = 1 - mean( |predicted - actual| / max(1, actual) )
    Clamped to [0, 1].
    Returns None when both pairs are unavailable.
    """
    errors = []
    if predicted_outage_hrs is not None and actual_outage_hrs is not None:
        denom = max(1.0, actual_outage_hrs)
        errors.append(abs(predicted_outage_hrs - actual_outage_hrs) / denom)
    if predicted_cost is not None and actual_cost is not None:
        denom = max(1.0, actual_cost)
        errors.append(abs(predicted_cost - actual_cost) / denom)

    if not errors:
        return None

    mape = sum(errors) / len(errors)
    return round(max(0.0, min(1.0, 1.0 - mape)), 3)


async def store_feedback(
    incident_uuid: str,
    actual_outage_hrs: Optional[float] = None,
    actual_cost: Optional[float] = None,
    root_cause: Optional[str] = None,
    resolution_summary: Optional[str] = None,
    contractor_used: Optional[str] = None,
) -> dict:
    """Locate the IncidentMemory record for ``incident_uuid`` and write back
    actual outcome values + computed decision_accuracy.

    Returns a summary dict with the fields that were updated.
    """
    # Lazy import — avoids creating DB engine at module load time
    from app.db.session import AsyncSessionFactory
    from app.db.models.incident_memory import IncidentMemory
    from sqlalchemy import select

    try:
        incident_uuid_obj = uuid.UUID(str(incident_uuid))
    except Exception:
        raise ValueError(f"Invalid incident UUID: {incident_uuid!r}")

    async with AsyncSessionFactory() as db:
        stmt = select(IncidentMemory).where(
            IncidentMemory.incident_uuid == incident_uuid_obj
        ).order_by(IncidentMemory.created_at.desc()).limit(1)

        result = await db.execute(stmt)
        mem = result.scalar_one_or_none()

        if not mem:
            logger.warning("Feedback: no IncidentMemory found", incident_uuid=str(incident_uuid))
            return {"updated": False, "reason": "No memory record found for this incident"}

        # Read predicted values that were stored when the incident was processed
        predicted_outage_hrs = mem.predicted_outage_hrs
        predicted_cost = mem.predicted_cost

        # V4 decision accuracy (MAPE-based composite)
        accuracy = _compute_decision_accuracy(
            predicted_outage_hrs=predicted_outage_hrs,
            actual_outage_hrs=actual_outage_hrs,
            predicted_cost=predicted_cost,
            actual_cost=actual_cost,
        )

        # V5 prediction accuracy — derived from learning_service math
        # (outage accuracy only, separate from composite decision_accuracy)
        prediction_accuracy: Optional[float] = None
        if predicted_outage_hrs is not None and actual_outage_hrs is not None:
            try:
                from app.services.learning_service import (
                    _signed_error_ratio,
                    _accuracy_from_error,
                )
                err = _signed_error_ratio(float(predicted_outage_hrs), float(actual_outage_hrs))
                prediction_accuracy = round(_accuracy_from_error(err), 3)
            except Exception:
                pass

        mem.actual_outage_hrs   = actual_outage_hrs
        mem.actual_cost         = actual_cost
        mem.repair_duration_hours = actual_outage_hrs  # Fix #1: update SQL record with actual duration
        mem.decision_accuracy   = accuracy
        mem.prediction_accuracy = prediction_accuracy
        if root_cause is not None:
            mem.root_cause = root_cause
        if resolution_summary is not None:
            mem.resolution_summary = resolution_summary
        if contractor_used is not None:
            mem.contractor_used = contractor_used

        await db.commit()
        await db.refresh(mem)

    # FIX #1 — RAG Memory Decontamination
    # The memory_service writes estimated_resolution_hrs (LLM's prediction) as
    # repair_duration_hours into incident_memory AND indexes it in ChromaDB.
    # Future retrieval returns this predicted value as if it were historical fact.
    # Once we have actual values from feedback, we must update the Chroma document
    # to replace the hallucinated ground truth with real data.
    # memory_service.py is protected — we call ChromaDB directly here.
    if actual_outage_hrs is not None and mem.incident_uuid:
        try:
            await _reindex_chroma_with_actuals(
                incident_uuid=str(mem.incident_uuid),
                actual_outage_hrs=actual_outage_hrs,
                actual_cost=actual_cost,
                mem=mem,
            )
        except Exception as chroma_err:
            # Non-critical: DB write already succeeded. Log and continue.
            logger.warning(
                "Chroma reindex failed — RAG memory still has predicted values",
                incident_uuid=str(incident_uuid),
                error=str(chroma_err),
            )

    # Trigger model retraining asynchronously in the background if performance has degraded
    import asyncio
    asyncio.create_task(_trigger_model_retrain_if_needed())

    logger.info(
        "Feedback stored",
        incident_uuid=str(incident_uuid),
        actual_outage_hrs=actual_outage_hrs,
        actual_cost=actual_cost,
        decision_accuracy=accuracy,
        prediction_accuracy=prediction_accuracy,
    )

    return {
        "updated":              True,
        "incident_uuid":        str(incident_uuid),
        "predicted_outage_hrs": predicted_outage_hrs,
        "actual_outage_hrs":    actual_outage_hrs,
        "predicted_cost":       predicted_cost,
        "actual_cost":          actual_cost,
        "decision_accuracy":    accuracy,
        "prediction_accuracy":  prediction_accuracy,
    }


async def _trigger_model_retrain_if_needed() -> None:
    """Evaluate recent model performance metrics and run retraining pipeline if thresholds are breached."""
    import sys
    import os
    import asyncio
    from app.config import settings
    
    # Skip spawning processes in unit tests to protect test isolation
    if settings.environment == "testing" or "pytest" in sys.modules:
        return

    from app.db.session import AsyncSessionFactory
    from app.db.models.incident_memory import IncidentMemory
    from sqlalchemy import select

    try:
        async with AsyncSessionFactory() as db:
            # Query the last 100 feedback records to compute rolling MAE
            stmt = (
                select(IncidentMemory)
                .where(IncidentMemory.actual_outage_hrs.isnot(None))
                .order_by(IncidentMemory.created_at.desc())
                .limit(100)
            )
            result = await db.execute(stmt)
            memories = result.scalars().all()

        if not memories:
            return

        feedback_records = []
        for m in memories:
            feedback_records.append({
                "predicted_outage_hrs": m.predicted_outage_hrs,
                "actual_outage_hrs": m.actual_outage_hrs,
                "predicted_cost": m.predicted_cost,
                "actual_cost": m.actual_cost,
            })

        from app.services.learning_service import evaluate_model_performance
        perf = evaluate_model_performance(feedback_records)

        if perf.get("should_retrain"):
            logger.info(
                "ML model retraining triggered due to MAE threshold breach",
                reasons=perf.get("reasons"),
                sample_count=perf.get("sample_count")
            )
            
            python_exe = sys.executable
            pipeline_script = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../ml/training_pipeline.py")
            )
            
            # Spawn the CPU-heavy scikit-learn training process as a background OS process
            # so the async event loop continues serving FastAPI requests without delay.
            process = await asyncio.create_subprocess_exec(
                python_exe,
                pipeline_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            logger.info("Model retraining background process spawned", pid=process.pid)
    except Exception as e:
        logger.error("Failed to execute background model retraining check", error=str(e))



async def _reindex_chroma_with_actuals(
    incident_uuid: str,
    actual_outage_hrs: float,
    actual_cost: Optional[float],
    mem: object,
) -> None:
    """Update the ChromaDB document for this incident with actual ground truth.

    This replaces the predicted repair_duration_hours (written at incident creation
    time from the LLM's estimate) with the real observed value. Without this,
    every future RAG retrieval returns hallucinated durations as historical evidence.

    Architecture note: memory_service.py is protected and cannot be modified.
    We call ChromaDB directly using the same client settings it uses, targeting
    the same collection. The document ID convention matches what memory_service
    uses for indexing (incident_uuid string).
    """
    import json
    from app.config import settings
    from app.agents.llm import get_embedding_model

    try:
        import chromadb
        import chromadb.config

        client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=int(settings.chroma_port) if settings.chroma_port else 8000,
        )
        collection = client.get_collection(settings.chroma_collection_name)

        # Build the corrected document content with actual values
        corrected_content = json.dumps({
            "incident_uuid":        incident_uuid,
            "incident_type":        getattr(mem, "incident_type", None),
            "root_cause":           getattr(mem, "root_cause", None),
            "severity":             getattr(mem, "severity", None),
            "affected_residents":   getattr(mem, "affected_residents", None),
            "contractor_used":      getattr(mem, "contractor_used", None),
            # KEY FIX: use actual duration, not the LLM-estimated duration
            "repair_duration_hours": actual_outage_hrs,
            "repair_cost":          actual_cost,
            "resolution_summary":   getattr(mem, "resolution_summary", None),
            "_ground_truth":        True,   # marks this as verified data
            "_feedback_updated":    True,
        })

        embeddings_model = get_embedding_model()
        embedding = embeddings_model.embed_query(corrected_content)

        # ChromaDB upsert: replaces the document if it exists, inserts if not
        collection.upsert(
            ids=[incident_uuid],
            documents=[corrected_content],
            embeddings=[embedding],
            metadatas=[{
                "incident_type":     getattr(mem, "incident_type", "") or "",
                "severity":          getattr(mem, "severity", "") or "",
                "ground_truth":      "true",
                "actual_outage_hrs": str(actual_outage_hrs),
            }],
        )
        logger.info(
            "Chroma document updated with actual ground truth",
            incident_uuid=incident_uuid,
            actual_outage_hrs=actual_outage_hrs,
        )
    except Exception as e:
        raise RuntimeError(f"Chroma reindex failed: {e}") from e
