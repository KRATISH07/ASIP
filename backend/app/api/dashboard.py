from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies import require_roles
from app.db.models.incident import Incident, IncidentStatus, IncidentSeverity
from app.db.models.agent_log import AgentLog
from app.db.models.tower import Tower
from app.schemas.dashboard import DashboardOut, DashboardKPI, RecentIncidentSummary, AgentActivitySummary, AnalyticsOut
from app.db.models.user import User, UserRole

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _build_date_range(today_start: datetime, days: int) -> list[str]:
    """Return a list of YYYY-MM-DD strings covering the last `days` days (oldest first)."""
    return [(today_start - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days - 1, -1, -1)]


@router.get("/", response_model=DashboardOut, summary="Get dashboard summary")
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = require_roles(UserRole.manager, UserRole.admin),
):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # KPI counts
    total = (await db.execute(select(func.count(Incident.id)))).scalar_one()

    active = (await db.execute(

        select(func.count(Incident.id)).where(
            Incident.status.notin_([IncidentStatus.resolved])
        )
    )).scalar_one()
    critical = (await db.execute(
        select(func.count(Incident.id)).where(
            Incident.severity == IncidentSeverity.critical,
            Incident.status != IncidentStatus.resolved
        )
    )).scalar_one()
    resolved_today = (await db.execute(
        select(func.count(Incident.id)).where(
            Incident.resolved_at >= today_start
        )
    )).scalar_one()

    # Recent incidents (last 10)
    recent_q = (
        select(Incident, Tower.name.label("tower_name"))
        .outerjoin(Tower, Incident.tower_id == Tower.id)
        .order_by(Incident.detected_at.desc())
        .limit(10)
    )
    recent_rows = (await db.execute(recent_q)).all()
    recent_incidents = [
        RecentIncidentSummary(
            id=str(row.Incident.id),
            type=row.Incident.type.value,
            severity=row.Incident.severity.value,
            status=row.Incident.status.value,
            tower_name=row.tower_name,
            detected_at=row.Incident.detected_at.isoformat(),
            custom_type=row.Incident.sensor_data.get("custom_type") if (row.Incident.sensor_data and isinstance(row.Incident.sensor_data, dict)) else None,
        )
        for row in recent_rows
    ]

    # Agent activity (today)
    agent_q = (
        select(AgentLog.agent_name, func.count(AgentLog.id), func.avg(AgentLog.execution_time_ms))
        .where(AgentLog.created_at >= today_start)
        .group_by(AgentLog.agent_name)
    )
    agent_rows = (await db.execute(agent_q)).all()
    agent_activity = [
        AgentActivitySummary(
            agent_name=row[0],
            executions_today=row[1],
            avg_execution_time_ms=float(row[2]) if row[2] else None,
            success_rate=1.0,
        )
        for row in agent_rows
    ]

    # Severity distribution
    sev_q = select(Incident.severity, func.count(Incident.id)).group_by(Incident.severity)
    sev_rows = (await db.execute(sev_q)).all()
    severity_dist = {row[0].value: row[1] for row in sev_rows}

    # 7-day incident trend — single GROUP BY query instead of 7 separate SELECTs
    window_start = today_start - timedelta(days=6)
    trend_q = (
        select(
            cast(Incident.detected_at, Date).label("day"),
            func.count(Incident.id).label("count"),
        )
        .where(Incident.detected_at >= window_start)
        .group_by(cast(Incident.detected_at, Date))
    )
    trend_rows = {
        str(row.day): row.count
        for row in (await db.execute(trend_q)).all()
    }
    # Fill in zeros for days with no incidents
    trend = [
        {"date": d, "count": trend_rows.get(d, 0)}
        for d in _build_date_range(today_start, 7)
    ]

    return DashboardOut(
        kpi=DashboardKPI(
            total_incidents=total,
            active_incidents=active,
            critical_incidents=critical,
            resolved_today=resolved_today,
        ),
        recent_incidents=recent_incidents,
        agent_activity=agent_activity,
        severity_distribution=severity_dist,
        incident_trend=trend,
    )


@router.get("/analytics", response_model=AnalyticsOut, summary="Get analytics data for charts")
async def get_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = require_roles(UserRole.manager, UserRole.admin),
):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # 30-day trend — single GROUP BY query instead of 30 separate SELECTs
    window_start = today_start - timedelta(days=29)
    trend_q = (
        select(
            cast(Incident.detected_at, Date).label("day"),
            func.count(Incident.id).label("count"),
        )
        .where(Incident.detected_at >= window_start)
        .group_by(cast(Incident.detected_at, Date))
    )
    trend_rows = {
        str(row.day): row.count
        for row in (await db.execute(trend_q)).all()
    }
    trend = [
        {"date": d, "count": trend_rows.get(d, 0)}
        for d in _build_date_range(today_start, 30)
    ]

    # Severity distribution
    sev_rows = (await db.execute(
        select(Incident.severity, func.count(Incident.id)).group_by(Incident.severity)
    )).all()
    severity_dist = {row[0].value: row[1] for row in sev_rows}

    # Incident type distribution
    type_rows = (await db.execute(
        select(Incident.type, func.count(Incident.id)).group_by(Incident.type)
    )).all()
    type_dist = {row[0].value: row[1] for row in type_rows}

    return AnalyticsOut(
        incident_trend=trend,
        resolution_time_trend=[],
        contractor_performance=[],
        severity_distribution=severity_dist,
        incident_type_distribution=type_dist,
    )



