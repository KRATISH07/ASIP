"""
Database seed script — populates towers, apartments, residents,
contractors, and admin user for development/demo.

Run with: python -m seeds.seed
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionFactory, engine
from app.db.base import Base
from app.db.models import *
from app.core.auth import hash_password
from app.db.models.tower import InfrastructureType
from app.db.models.resident import ResidentRole
from app.db.models.user import UserRole


TOWERS = [
    {"name": "Tower A", "floors": 15, "total_apartments": 90, "infrastructure_type": InfrastructureType.both},
    {"name": "Tower B", "floors": 12, "total_apartments": 72, "infrastructure_type": InfrastructureType.water},
    {"name": "Tower C", "floors": 20, "total_apartments": 120, "infrastructure_type": InfrastructureType.both},
]

CONTRACTORS = [
    {
        "name": "AquaFix Pro", "specializations": ["water", "plumbing"],
        "rating": 4.8, "avg_response_time_hrs": 2.0, "success_rate": 0.97, "total_jobs": 145,
        "contact_info": {"phone": "+91-9876543210", "email": "aquafix@example.com", "address": "Sector 12, Noida"},
        "is_active": True,
    },
    {
        "name": "PowerSure Services", "specializations": ["electrical", "power"],
        "rating": 4.6, "avg_response_time_hrs": 1.5, "success_rate": 0.95, "total_jobs": 203,
        "contact_info": {"phone": "+91-9123456780", "email": "powersure@example.com", "address": "Sector 18, Gurugram"},
        "is_active": True,
    },
    {
        "name": "CityFix General", "specializations": ["water", "electrical", "civil"],
        "rating": 4.2, "avg_response_time_hrs": 3.5, "success_rate": 0.89, "total_jobs": 87,
        "contact_info": {"phone": "+91-9988776655", "email": "cityfix@example.com", "address": "Sector 5, Delhi"},
        "is_active": True,
    },
    {
        "name": "RapidRepair Elite", "specializations": ["water", "electrical"],
        "rating": 4.9, "avg_response_time_hrs": 1.0, "success_rate": 0.98, "total_jobs": 312,
        "contact_info": {"phone": "+91-9001234567", "email": "rapid@example.com", "address": "Sector 62, Noida"},
        "is_active": True,
    },
    {
        "name": "EcoPlumb Budget", "specializations": ["water", "plumbing"],
        "rating": 4.0, "avg_response_time_hrs": 4.5, "success_rate": 0.88, "total_jobs": 62,
        "contact_info": {"phone": "+91-9871112223", "email": "ecoplumb@example.com", "address": "Sector 22, Noida"},
        "is_active": True,
    },
    {
        "name": "VoltFlash Emergency", "specializations": ["electrical", "power"],
        "rating": 4.7, "avg_response_time_hrs": 0.6, "success_rate": 0.96, "total_jobs": 158,
        "contact_info": {"phone": "+91-9873334445", "email": "voltflash@example.com", "address": "Sector 34, Gurugram"},
        "is_active": True,
    },
    {
        "name": "SureBuild Civil", "specializations": ["civil"],
        "rating": 4.9, "avg_response_time_hrs": 3.5, "success_rate": 0.99, "total_jobs": 94,
        "contact_info": {"phone": "+91-9875556667", "email": "surebuild@example.com", "address": "Sector 45, Delhi"},
        "is_active": True,
    },
    {
        "name": "QuickTap Plumbing", "specializations": ["water", "plumbing"],
        "rating": 4.5, "avg_response_time_hrs": 0.8, "success_rate": 0.94, "total_jobs": 120,
        "contact_info": {"phone": "+91-9877778889", "email": "quicktap@example.com", "address": "Sector 50, Noida"},
        "is_active": True,
    },
]

RESIDENT_NAMES = [
    "Kratish Mewada", "Rahul Gupta", "Anjali Singh", "Vikram Mehta",
    "Sunita Patel", "Arjun Nair", "Kavita Reddy", "Suresh Kumar",
    "Pooja Joshi", "Nikhil Verma",
]


async def seed():
    print("🌱 Starting ASIP database seed...")

    # 1. Ensure PostgreSQL schemas exist
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.execute(text('CREATE SCHEMA IF NOT EXISTS "public"'))
        await conn.execute(text('CREATE SCHEMA IF NOT EXISTS "society_default"'))
    print("✅ Schemas 'public' and 'society_default' verified/created")

    # 2. Bind active tenant context to society_default so tables deploy to the correct search_path
    from app.core.tenant_context import set_tenant_schema
    set_tenant_schema("society_default")

    # 3. Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created in designated schemas")

    async with AsyncSessionFactory() as db:
        # Register default tenant
        from app.db.models.tenant import Tenant
        from sqlalchemy import select
        existing_tenant = await db.execute(select(Tenant).where(Tenant.slug == "default"))
        if not existing_tenant.scalar_one_or_none():
            tenant = Tenant(
                name="Greenfield Heights (Default)",
                slug="default",
                schema_name="society_default",
                is_active=True
            )
            db.add(tenant)
            await db.flush()
            print("✅ Default tenant registered in public.tenants")

        # Admin user
        # Idempotent user creation
        existing_admin = await db.execute(select(User).where(User.email == "admin@asip.ai"))
        if not existing_admin.scalar_one_or_none():
            admin = User(
                email="admin@asip.ai",
                hashed_password=hash_password("admin123"),
                full_name="ASIP Administrator",
                role=UserRole.admin,
                is_active=True,
            )
            db.add(admin)

        existing_manager = await db.execute(select(User).where(User.email == "manager@asip.ai"))
        if not existing_manager.scalar_one_or_none():
            manager = User(
                email="manager@asip.ai",
                hashed_password=hash_password("manager123"),
                full_name="Society Manager",
                role=UserRole.manager,
                is_active=True,
            )
            db.add(manager)
        await db.flush()
        print("✅ Users seeded (admin@asip.ai / admin123)")

        # Towers
        tower_objs = []
        from sqlalchemy import select
        for t in TOWERS:
            existing = await db.execute(select(Tower).where(Tower.name == t["name"]))
            tower = existing.scalar_one_or_none()
            if not tower:
                tower = Tower(**t)
                db.add(tower)
                await db.flush()
            tower_objs.append(tower)
        print(f"✅ {len(tower_objs)} towers seeded")

        # Apartments + Residents
        resident_idx = 0
        for tower in tower_objs:
            apts_per_floor = tower.total_apartments // tower.floors
            for floor in range(1, min(4, tower.floors) + 1):  # seed first 3 floors
                for apt_num in range(1, apts_per_floor + 1):
                    flat = f"{floor}0{apt_num}"
                    apt = Apartment(tower_id=tower.id, flat_number=flat, floor=floor, occupied=True)
                    db.add(apt)
                    await db.flush()

                    # Add a resident to each apartment
                    name = RESIDENT_NAMES[resident_idx % len(RESIDENT_NAMES)]
                    email = f"resident{resident_idx + 1}@asip.ai"
                    from sqlalchemy import select
                    existing_res = await db.execute(select(Resident).where(Resident.email == email))
                    if not existing_res.scalar_one_or_none():
                        resident = Resident(
                            apartment_id=apt.id,
                            name=name,
                            email=email,
                            phone=f"+91-90{resident_idx:08d}",
                            role=ResidentRole.owner,
                            notification_prefs={"email": True, "sms": True, "push": True},
                            is_active=True,
                        )
                        db.add(resident)
                    resident_idx += 1

        await db.flush()
        print(f"✅ {resident_idx} residents seeded")

        # Contractors
        contractor_objs = []
        from sqlalchemy import select
        for c in CONTRACTORS:
            # Use name as idempotency key
            existing_c = await db.execute(select(Contractor).where(Contractor.name == c["name"]))
            contractor = existing_c.scalar_one_or_none()
            if not contractor:
                contractor = Contractor(**c)
                db.add(contractor)
                await db.flush()
            contractor_objs.append(contractor)
        print(f"✅ {len(contractor_objs)} contractors seeded")

        # Contractor historical performance (sample data)
        # Create per-contractor history rows to enable scoring and ranking
        for contractor in contractor_objs:
            name = contractor.name.lower()
            # Create different patterns per contractor name for variety
            if "aquafix" in name:
                # AquaFix: many water jobs, high success, short durations
                for i in range(20):
                    # idempotent: avoid duplicating identical seeded rows by checking approximate existing count
                    from sqlalchemy import select, func
                    cnt = await db.execute(select(func.count()).select_from(ContractorHistory).where(ContractorHistory.contractor_id == contractor.id))
                    if cnt.scalar_one() >= 20:
                        break
                    db.add(ContractorHistory(
                        contractor_id=contractor.id,
                        incident_type="water_leak",
                        repair_duration_hours=3.0 + (i % 3) * 0.2,
                        repair_cost=7500 + i * 10,
                        resolution_success=True,
                        resident_feedback_score=4.6,
                    ))
            elif "power" in name or "powersure" in name:
                for i in range(15):
                    from sqlalchemy import select, func
                    cnt = await db.execute(select(func.count()).select_from(ContractorHistory).where(ContractorHistory.contractor_id == contractor.id))
                    if cnt.scalar_one() >= 15:
                        break
                    db.add(ContractorHistory(
                        contractor_id=contractor.id,
                        incident_type="power_outage",
                        repair_duration_hours=1.5 + (i % 4) * 0.5,
                        repair_cost=9500 + i * 20,
                        resolution_success=True,
                        resident_feedback_score=4.5,
                    ))
            elif "cityfix" in name:
                for i in range(10):
                    from sqlalchemy import select, func
                    cnt = await db.execute(select(func.count()).select_from(ContractorHistory).where(ContractorHistory.contractor_id == contractor.id))
                    if cnt.scalar_one() >= 10:
                        break
                    db.add(ContractorHistory(
                        contractor_id=contractor.id,
                        incident_type="general_maintenance",
                        repair_duration_hours=4.0 + (i % 5) * 0.6,
                        repair_cost=6000 + i * 15,
                        resolution_success=(i % 5 != 0),
                        resident_feedback_score=4.0 - (i % 3) * 0.2,
                    ))
            else:
                for i in range(12):
                    from sqlalchemy import select, func
                    cnt = await db.execute(select(func.count()).select_from(ContractorHistory).where(ContractorHistory.contractor_id == contractor.id))
                    if cnt.scalar_one() >= 12:
                        break
                    db.add(ContractorHistory(
                        contractor_id=contractor.id,
                        incident_type="mixed",
                        repair_duration_hours=2.0 + (i % 4) * 0.7,
                        repair_cost=8000 + i * 25,
                        resolution_success=True,
                        resident_feedback_score=4.3,
                    ))
        await db.flush()
        print("✅ Contractor historical data seeded")

        await db.commit()

    print("\n🎉 Seed complete! You can now start the backend.")
    print("   Admin login: admin@asip.ai / admin123")
    print("   Manager login: manager@asip.ai / manager123")


if __name__ == "__main__":
    asyncio.run(seed())
