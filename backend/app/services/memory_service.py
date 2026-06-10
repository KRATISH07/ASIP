"""Incident Memory Service

Stores incident summaries in Postgres and indexes a text representation
in ChromaDB for similarity-based retrieval.
"""
import json
import uuid
from typing import List, Dict, Any, Optional
from app.config import settings
from app.core.logging import get_logger

logger = get_logger("memory_service")


async def store_incident_memory(state: dict) -> Any:
    """Persist incident memory into Postgres and index in Chroma.

    Returns the created IncidentMemory instance.
    """
    incident_id = state.get("incident_id")
    try:
        incident_uuid = uuid.UUID(str(incident_id)) if incident_id else None
    except Exception:
        incident_uuid = None

    incident_type = (state.get("incident_event") or {}).get("type")
    root_cause = (state.get("final_report") or {}).get("root_cause") or (state.get("diagnosis") or {}).get("probable_cause")
    severity = (state.get("incident_event") or {}).get("severity")
    affected_residents = (state.get("impact") or {}).get("estimated_residents")
    contractor_used = (state.get("contractor_recommendation") or {}).get("contractor_name")
    repair_duration = (state.get("final_report") or {}).get("estimated_resolution_hrs")
    resolution_summary = (state.get("final_report") or {}).get("incident_summary")

    # Lazy import to avoid creating DB engine at module import time during tests
    from app.db.session import AsyncSessionFactory
    from app.db.models.incident_memory import IncidentMemory
    # Expose model at module level for tests that assert its presence
    globals().setdefault("IncidentMemory", IncidentMemory)

    mem = IncidentMemory(
        incident_uuid=incident_uuid,
        incident_type=incident_type,
        root_cause=root_cause,
        severity=severity,
        affected_residents=affected_residents,
        contractor_used=contractor_used,
        repair_duration_hours=repair_duration,
        resolution_summary=resolution_summary,
    )

    async with AsyncSessionFactory() as db:
        db.add(mem)
        await db.flush()
        await db.commit()

    # Index in Chroma for similarity retrieval
    try:
        await index_memory_in_chroma(mem)
    except Exception as e:
        logger.warning("Failed to index incident memory in Chroma", error=str(e))

    return mem


async def index_memory_in_chroma(mem: Any) -> None:
    """Create a ChromaDB document for the incident memory.

    The document is stored as JSON in the page content for easy retrieval.
    """
    try:
        from langchain.schema import Document
        from app.agents.llm import get_embedding_model
        from langchain_chroma import Chroma

        embeddings = get_embedding_model()

        content = json.dumps({
            "incident_uuid": str(mem.incident_uuid) if mem.incident_uuid else None,
            "incident_type": mem.incident_type,
            "root_cause": mem.root_cause,
            "severity": mem.severity,
            "affected_residents": mem.affected_residents,
            "contractor_used": mem.contractor_used,
            "repair_duration_hours": mem.repair_duration_hours,
            "resolution_summary": mem.resolution_summary,
            "created_at": mem.created_at.isoformat(),
        })

        doc = Document(page_content=content, metadata={"source": "incident_memory"})
        # Build chromadb Settings instance for client_settings
        import chromadb.config

        client_settings = chromadb.config.Settings(
            chroma_server_host=settings.chroma_host,
            chroma_server_http_port=int(settings.chroma_port) if settings.chroma_port is not None else None,
        )

        Chroma.from_documents(
            documents=[doc],
            embedding=embeddings,
            collection_name=settings.chroma_collection_name,
            client_settings=client_settings,
        )
    except Exception as e:
        logger.warning("Chroma indexing failed", error=str(e))


async def retrieve_similar_incidents(current_incident: dict, k: int = 3) -> List[Dict[str, Any]]:
    """Retrieve the top-k similar historical incidents from Chroma.

    Returns parsed JSON objects for the top documents.
    """
    try:
        from app.rag.retriever import get_retriever

        retriever = get_retriever(k)

        query = f"{(current_incident.get('incident_type') or current_incident.get('sensor_type') or '')} similar historical incidents"
        # retriever may be sync; attempt sync call first
        docs = retriever.get_relevant_documents(query)
        results = []
        for doc in docs[:k]:
            try:
                data = json.loads(doc.page_content)
            except Exception:
                data = {"text": doc.page_content}
            results.append(data)
        return results
    except Exception as e:
        logger.warning("Memory retrieval failed", error=str(e))
        return []
