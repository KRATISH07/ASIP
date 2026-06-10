from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies import get_current_user
from app.db.models.incident import Incident, IncidentStatus, IncidentSeverity
from app.db.models.agent_log import AgentLog
from app.db.models.tower import Tower
from app.schemas.dashboard import DashboardOut, DashboardKPI, RecentIncidentSummary, AgentActivitySummary, AnalyticsOut
from app.db.models.user import User

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/", response_model=DashboardOut, summary="Get dashboard summary")
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
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

    # 7-day incident trend
    trend = []
    for i in range(6, -1, -1):
        day = today_start - timedelta(days=i)
        day_end = day + timedelta(days=1)
        count = (await db.execute(
            select(func.count(Incident.id)).where(
                Incident.detected_at >= day,
                Incident.detected_at < day_end,
            )
        )).scalar_one()
        trend.append({"date": day.strftime("%Y-%m-%d"), "count": count})

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
    current_user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # 30-day trend
    trend = []
    for i in range(29, -1, -1):
        day = today_start - timedelta(days=i)
        day_end = day + timedelta(days=1)
        count = (await db.execute(
            select(func.count(Incident.id)).where(
                Incident.detected_at >= day,
                Incident.detected_at < day_end,
            )
        )).scalar_one()
        trend.append({"date": day.strftime("%Y-%m-%d"), "count": count})

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
