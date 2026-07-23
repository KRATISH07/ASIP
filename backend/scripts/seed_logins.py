import asyncio
import sys
from sqlalchemy import select

sys.path.insert(0, "/Users/kratish/study/languages/ASIP/backend")
from app.db.session import AsyncSessionFactory
from app.db.models.user import User, UserRole
from app.db.models.resident import Resident
from app.db.models.contractor import Contractor
from app.core.auth import hash_password

async def seed_logins():
    async with AsyncSessionFactory() as db:
        # 1. Resident login: get first resident
        res_stmt = select(Resident).limit(1)
        res_run = await db.execute(res_stmt)
        resident = res_run.scalar_one_or_none()
        
        if resident:
            email = "resident1@asip.ai"
            existing = await db.execute(select(User).where(User.email == email))
            if not existing.scalar_one_or_none():
                user_res = User(
                    email=email,
                    hashed_password=hash_password("password123"),
                    full_name=resident.name,
                    role=UserRole.resident,
                    resident_id=resident.id,
                    is_active=True
                )
                db.add(user_res)
                print(f"Seeded resident user: {email} / password123")
                
        # 2. Contractor login: get first contractor
        con_stmt = select(Contractor).limit(1)
        con_run = await db.execute(con_stmt)
        contractor = con_run.scalar_one_or_none()
        
        if contractor:
            email = "contractor1@asip.ai"
            existing = await db.execute(select(User).where(User.email == email))
            if not existing.scalar_one_or_none():
                user_con = User(
                    email=email,
                    hashed_password=hash_password("password123"),
                    full_name=contractor.name,
                    role=UserRole.contractor,
                    contractor_id=contractor.id,
                    is_active=True
                )
                db.add(user_con)
                print(f"Seeded contractor user: {email} / password123")
                
        # 3. Sensor Gateway login
        gateway_email = "gateway@asip.ai"
        existing_gw = await db.execute(select(User).where(User.email == gateway_email))
        if not existing_gw.scalar_one_or_none():
            user_gw = User(
                email=gateway_email,
                hashed_password=hash_password("password123"),
                full_name="Edge Ingestion Gateway",
                role=UserRole.sensor_gateway,
                is_active=True
            )
            db.add(user_gw)
            print(f"Seeded gateway user: {gateway_email} / password123")
            
        await db.commit()
        print("Logins seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_logins())
