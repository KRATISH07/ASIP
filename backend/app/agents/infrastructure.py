"""
InfrastructureAgent: performs root-cause analysis using RAG.
Retrieves relevant context from the knowledge base (maintenance manuals,
historical incidents, repair procedures) and generates a structured diagnosis.
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.agents.state import ASIPState, DiagnosisReport
from app.agents.llm import get_llm
from app.core.llm.chain import invoke_chain
from app.core.logging import get_logger

logger = get_logger("infrastructure_agent")

DIAGNOSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert infrastructure engineer for residential societies.
Your job is to perform root-cause analysis on infrastructure incidents.
You will be given sensor data, the detected incident type, and relevant context
from maintenance manuals and historical records.

Always respond with valid JSON matching this schema:
{{
  "probable_cause": "string — technical root cause",
  "recommended_action": "string — specific repair steps",
  "confidence": float (0.0 to 1.0),
  "retrieved_context": "string — relevant excerpt used"
}}"""),
    ("human", """
Incident Type: {incident_type}
Severity: {severity}
Sensor Reading: {sensor_data}

Retrieved Context from Knowledge Base:
{context}

Provide your root-cause analysis as JSON.
"""),
])


async def infrastructure_agent(state: ASIPState) -> ASIPState:
    logger.info("InfrastructureAgent: performing RCA", incident_id=state["incident_id"])

    incident_event = state.get("incident_event")
    if not incident_event:
        return {**state, "next": "impact_agent"}

    # RAG retrieval
    context = await _retrieve_context(incident_event["type"], state["sensor_data"])

    llm = get_llm(temperature=0.1)
    payload = {
        "incident_type": incident_event["type"],
        "severity": incident_event["severity"],
        "sensor_data": str(state["sensor_data"]),
        "context": context,
    }
    try:
        diagnosis: DiagnosisReport = await invoke_chain(DIAGNOSIS_PROMPT, llm, JsonOutputParser(), payload)
        logger.info("Diagnosis complete", probable_cause=diagnosis.get("probable_cause", "")[:80])
    except Exception as e:
        logger.error("InfrastructureAgent LLM call failed", error=str(e))
        diagnosis = DiagnosisReport(
            probable_cause="Could not determine — LLM unavailable",
            recommended_action="Manual inspection required",
            confidence=0.3,
            retrieved_context=context[:200] if context else None,
        )

    return {**state, "diagnosis": diagnosis, "next": "impact_agent"}


async def _retrieve_context(incident_type: str, sensor_data: dict) -> str:
    """Retrieve relevant documents from ChromaDB vector store."""
    base_parts = []

    # Attempt RAG retrieval (optional)
    try:
        from app.rag.retriever import get_retriever
        retriever = get_retriever()
        query = f"{incident_type} root cause repair procedure {sensor_data.get('sensor_type', '')}"
        docs = retriever.get_relevant_documents(query)
        base_parts.append("\n\n".join([doc.page_content for doc in docs[:3]]))
    except Exception as e:
        logger.warning("RAG retrieval failed — proceeding without context", error=str(e))

    # Always attempt to retrieve similar incidents from memory and append summaries
    try:
        import importlib
        memory_service = importlib.import_module("app.services.memory_service")
        memories = await memory_service.retrieve_similar_incidents({"incident_type": incident_type, **sensor_data}, k=3)
        if memories:
            mem_texts = []
            for m in memories:
                mem_texts.append(f"SUMMARY: {m.get('resolution_summary') or m.get('root_cause') or m.get('incident_type')}")
            base_parts.append("Similar historical incidents:\n" + "\n".join(mem_texts))
    except Exception:
        # non-fatal for retrieval
        logger.warning("Memory retrieval failed in _retrieve_context", error="memory retrieval error")

    if base_parts:
        return "\n\n".join([p for p in base_parts if p])
    return "No context available — knowledge base not initialized."
