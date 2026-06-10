"""
CommunicationAgent: generates tailored notification drafts for
residents, management, and maintenance team using LLM.
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.agents.state import ASIPState, NotificationPayload
from app.agents.llm import get_llm
from app.core.logging import get_logger

logger = get_logger("communication_agent")

NOTIFICATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the communications officer for a residential society.
Generate professional, clear, and empathetic notifications for an infrastructure incident.
Create three notification drafts: one for residents, one for management, one for maintenance.

Respond with valid JSON array:
[
  {{
    "channel": "email",
    "subject": "string",
    "content": "string — full message body",
    "recipient_type": "residents"
  }},
  {{
    "channel": "email",
    "subject": "string",
    "content": "string",
    "recipient_type": "management"
  }},
  {{
    "channel": "sms",
    "subject": "",
    "content": "string — concise SMS under 160 chars",
    "recipient_type": "residents"
  }}
]"""),
    ("human", """
Incident Type: {incident_type}
Severity: {severity}
Description: {description}
Affected Residents: {residents}
Root Cause: {root_cause}
Recommended Action: {recommended_action}
Assigned Contractor: {contractor_name}
Estimated Resolution: {estimated_time_hrs} hours

Generate the three notification drafts as JSON.
"""),
])


async def communication_agent(state: ASIPState) -> ASIPState:
    logger.info("CommunicationAgent: generating notifications", incident_id=state["incident_id"])

    incident_event = state.get("incident_event", {})
    diagnosis = state.get("diagnosis", {})
    impact = state.get("impact", {})
    contractor = state.get("contractor_recommendation", {})

    llm = get_llm(temperature=0.3)
    chain = NOTIFICATION_PROMPT | llm | JsonOutputParser()

    try:
        notifications = await chain.ainvoke({
            "incident_type": incident_event.get("type", "Unknown"),
            "severity": incident_event.get("severity", "Unknown"),
            "description": incident_event.get("description", "N/A"),
            "residents": impact.get("estimated_residents", 0),
            "root_cause": diagnosis.get("probable_cause", "Under investigation"),
            "recommended_action": diagnosis.get("recommended_action", "Pending"),
            "contractor_name": contractor.get("contractor_name", "To be assigned"),
            "estimated_time_hrs": contractor.get("estimated_time_hrs", "Unknown"),
        })
        logger.info("Notifications generated", count=len(notifications))
    except Exception as e:
        logger.error("CommunicationAgent LLM call failed", error=str(e))
        notifications = [_fallback_notification(incident_event)]

    return {**state, "notifications": notifications, "next": "supervisor_agent"}


def _fallback_notification(event: dict) -> dict:
    return {
        "channel": "email",
        "subject": f"Infrastructure Alert: {event.get('type', 'Incident')}",
        "content": f"Dear Resident, we have detected a {event.get('type', 'infrastructure')} issue "
                   f"of {event.get('severity', 'unknown')} severity. Our team is working on it.",
        "recipient_type": "residents",
    }
