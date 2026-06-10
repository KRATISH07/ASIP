from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.repositories.contractor_repo import ContractorRepository
from app.db.models.contractor import Contractor
from app.db.models.contractor_history import ContractorHistory
from datetime import datetime


def compute_ranking_from_data(contractors: List[Dict[str, Any]], history_map: Optional[Dict[str, List[Dict[str, Any]]]] = None, k: int = 5) -> List[Dict[str, Any]]:
    """Pure-Python ranking function usable in unit tests.

    `contractors` is a list of dict-like objects with keys: id/name/success_rate/avg_response_time_hrs/total_jobs/is_active/rating/specializations
    `history_map` maps contractor id -> list of history dicts with keys repair_duration_hours, repair_cost, resident_feedback_score
    """
    history_map = history_map or {}

    if not contractors:
        return []

    success_rates = [max(0.0, float(c.get("success_rate", 0.0) or 0.0)) for c in contractors]
    repair_times = [float(c.get("avg_response_time_hrs", 0.0) or 0.0) for c in contractors]
    experiences = [int(c.get("total_jobs", 0) or 0) for c in contractors]

    min_rt, max_rt = min(repair_times), max(repair_times)
    min_exp, max_exp = (min(experiences), max(experiences)) if experiences else (0, 0)

    results: List[Dict[str, Any]] = []

    for c in contractors:
        cid = str(c.get("id") or c.get("contractor_id") or c.get("name"))
        hist_list = history_map.get(cid, [])
        avg_feedback = None
        if hist_list:
            feedbacks = [h.get("resident_feedback_score") for h in hist_list if h.get("resident_feedback_score") is not None]
            if feedbacks:
                avg_feedback = sum(feedbacks) / len(feedbacks)

        success_score = float(c.get("success_rate", 0.0) or 0.0) * 100.0
        rt = float(c.get("avg_response_time_hrs", 0.0) or (hist_list[0].get("repair_duration_hours") if hist_list else 0.0))
        if max_rt - min_rt > 0:
            repair_score = 100.0 * (max_rt - rt) / (max_rt - min_rt)
        else:
            repair_score = 100.0

        if avg_feedback is not None:
            feedback_score = float(avg_feedback) * 20.0
        else:
            feedback_score = float(c.get("rating", 3.0)) * 20.0

        availability_score = 100.0 if bool(c.get("is_active", True)) else 0.0

        jobs = int(c.get("total_jobs", 0) or 0)
        if max_exp - min_exp > 0:
            experience_score = 100.0 * (jobs - min_exp) / (max_exp - min_exp)
        else:
            experience_score = 50.0

        weights = {
            "success_rate": 0.4,
            "repair_time": 0.25,
            "feedback": 0.15,
            "availability": 0.10,
            "experience": 0.10,
        }

        final_score = (
            success_score * weights["success_rate"]
            + repair_score * weights["repair_time"]
            + feedback_score * weights["feedback"]
            + availability_score * weights["availability"]
            + experience_score * weights["experience"]
        )

        results.append(
            {
                "contractor_id": cid,
                "name": c.get("name"),
                "final_score": round(final_score, 2),
                "breakdown": {
                    "success_rate_score": round(success_score, 2),
                    "repair_time_score": round(repair_score, 2),
                    "feedback_score": round(feedback_score, 2),
                    "availability_score": round(availability_score, 2),
                    "experience_score": round(experience_score, 2),
                },
                "historical_evidence": hist_list[:5],
            }
        )

    results.sort(key=lambda x: x["final_score"], reverse=True)
    return results[:k]



def _specialty_for_incident(incident_type: Optional[str]) -> Optional[str]:
    if not incident_type:
        return None
    t = incident_type.lower()
    if "water" in t or "tank" in t or "pressure" in t:
        return "water"
    if "power" in t or "electric" in t or "electrical" in t:
        return "electrical"
    return None


async def rank_contractors(db: AsyncSession, incident_type: Optional[str] = None, k: int = 5, impact: Optional[dict] = None) -> List[Dict[str, Any]]:
    """Return ranked contractors with score breakdown and historical evidence.

    Uses the following weighted scoring:
      - Success Rate: 40%
      - Repair Time: 25% (lower is better)
      - Resident Feedback: 15%
      - Availability: 10%
      - Experience (jobs completed): 10%
    """
    repo = ContractorRepository(db)
    specialty = _specialty_for_incident(incident_type)
    contractors: List[Contractor] = await repo.list_active(specialization=specialty)

    if not contractors:
        return []

    # Gather baseline stats for normalization
    success_rates = [max(0.0, float(c.success_rate or 0.0)) for c in contractors]
    repair_times = [float(c.avg_response_time_hrs or 0.0) for c in contractors]
    experiences = [int(c.total_jobs or 0) for c in contractors]

    min_rt, max_rt = min(repair_times), max(repair_times)
    min_exp, max_exp = (min(experiences), max(experiences)) if experiences else (0, 0)

    results: List[Dict[str, Any]] = []

    for c in contractors:
        # Historical aggregates from contractor_history
        q = select(func.avg(ContractorHistory.repair_duration_hours), func.avg(ContractorHistory.repair_cost), func.avg(ContractorHistory.resident_feedback_score), func.count(ContractorHistory.id)).where(ContractorHistory.contractor_id == c.id)
        r = await db.execute(q)
        avg_repair_duration, avg_cost, avg_feedback, hist_count = r.one()

        # Normalize components
        success_score = float(c.success_rate or 0.0) * 100.0  # 0-100

        # Repair time: lower is better
        rt = float(c.avg_response_time_hrs or (avg_repair_duration or 0.0))
        if max_rt - min_rt > 0:
            repair_score = 100.0 * (max_rt - rt) / (max_rt - min_rt)
        else:
            repair_score = 100.0

        # Resident feedback: prefer historical feedback average, else map contractor rating (1-5) => 0-100
        if avg_feedback:
            feedback_score = float(avg_feedback) * 20.0
        else:
            feedback_score = float(c.rating or 3.0) * 20.0

        availability_score = 100.0 if bool(c.is_active) else 0.0

        # Experience: normalize total_jobs
        jobs = int(c.total_jobs or 0)
        if max_exp - min_exp > 0:
            experience_score = 100.0 * (jobs - min_exp) / (max_exp - min_exp)
        else:
            experience_score = 50.0

        # Weights
        weights = {
            "success_rate": 0.4,
            "repair_time": 0.25,
            "feedback": 0.15,
            "availability": 0.10,
            "experience": 0.10,
        }

        final_score = (
            success_score * weights["success_rate"]
            + repair_score * weights["repair_time"]
            + feedback_score * weights["feedback"]
            + availability_score * weights["availability"]
            + experience_score * weights["experience"]
        )

        # Historical evidence: fetch recent history rows
        evidence_q = select(ContractorHistory).where(ContractorHistory.contractor_id == c.id).order_by(ContractorHistory.created_at.desc()).limit(5)
        evidence_res = await db.execute(evidence_q)
        evidence_rows = evidence_res.scalars().all()
        historical = [
            {
                "incident_type": h.incident_type,
                "repair_duration_hours": float(h.repair_duration_hours) if h.repair_duration_hours is not None else None,
                "repair_cost": float(h.repair_cost) if h.repair_cost is not None else None,
                "resolution_success": bool(h.resolution_success) if h.resolution_success is not None else None,
                "resident_feedback_score": float(h.resident_feedback_score) if h.resident_feedback_score is not None else None,
                "created_at": h.created_at.isoformat() if isinstance(h.created_at, datetime) else None,
            }
            for h in evidence_rows
        ]

        results.append(
            {
                "contractor_id": str(c.id),
                "name": c.name,
                "specializations": c.specializations,
                "final_score": round(final_score, 2),
                "breakdown": {
                    "success_rate_score": round(success_score, 2),
                    "repair_time_score": round(repair_score, 2),
                    "feedback_score": round(feedback_score, 2),
                    "availability_score": round(availability_score, 2),
                    "experience_score": round(experience_score, 2),
                },
                "historical_evidence": historical,
            }
        )

    # Sort by final_score desc
    results.sort(key=lambda x: x["final_score"], reverse=True)
    return results[:k]
