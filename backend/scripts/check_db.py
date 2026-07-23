import asyncio
import uuid
from app.db.session import AsyncSessionFactory
from app.db.models.incident import Incident
from app.db.models.workflow_run import WorkflowRun
from app.db.models.contractor import ContractorAssignment
from sqlalchemy import select, text

async def main():
    async with AsyncSessionFactory() as db:
        await db.execute(text('SET search_path TO "society_default", public'))
        
        print("--- INCIDENTS IN DB ---")
        inc_stmt = select(Incident).order_by(Incident.detected_at.desc())
        res = await db.execute(inc_stmt)
        incidents = res.scalars().all()
        for inc in incidents:
            print(f"ID: {inc.id} | Type: {inc.type} | Status: {inc.status} | Severity: {inc.severity} | Detected At: {inc.detected_at}")
            
        print("\n--- WORKFLOW RUNS IN DB ---")
        wf_stmt = select(WorkflowRun).order_by(WorkflowRun.created_at.desc())
        res2 = await db.execute(wf_stmt)
        runs = res2.scalars().all()
        for run in runs:
            print(f"ID: {run.id} | Incident ID: {run.incident_id} | Status: {run.status} | Steps: {run.completed_steps} | Failed Step: {run.failed_at_step} | Error: {run.last_error}")

        print("\n--- CONTRACTOR ASSIGNMENTS ---")
        ca_stmt = select(ContractorAssignment)
        res3 = await db.execute(ca_stmt)
        assignments = res3.scalars().all()
        for ca in assignments:
            print(f"ID: {ca.id} | Incident ID: {ca.incident_id} | Contractor ID: {ca.contractor_id} | Cost: {ca.estimated_cost} | Reasoning: {ca.selection_reasoning}")

if __name__ == "__main__":
    asyncio.run(main())
