import os
import sys
import asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Set up python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.models.user import User, UserRole
from app.repositories.user_repo import UserRepository
from app.core.auth import hash_password
from app.config import settings

SEED_USERS = [
    {"email": "admin@asip.ai", "password": "password123", "role": UserRole.admin, "full_name": "ASIP Administrator"},
    {"email": "manager@asip.ai", "password": "password123", "role": UserRole.manager, "full_name": "Society Manager"},
    {"email": "resident1@asip.ai", "password": "password123", "role": UserRole.resident, "full_name": "Aarav Sharma"},
    {"email": "gateway@asip.ai", "password": "password123", "role": UserRole.sensor_gateway, "full_name": "IoT Edge Gateway #1"},
]

async def main():
    print(f"Connecting to database: {settings.database_url}")
    engine = create_async_engine(settings.database_url)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with SessionLocal() as db:
        repo = UserRepository(db)
        for u in SEED_USERS:
            result = await db.execute(select(User).where(User.email == u["email"]))
            existing = result.scalar_one_or_none()
            if existing:
                existing.hashed_password = hash_password(u["password"])
                existing.role = u["role"]
                print(f"Updated user '{u['email']}' role={u['role'].value}")
            else:
                user = await repo.create(
                    email=u["email"],
                    password=u["password"],
                    role=u["role"],
                    full_name=u["full_name"]
                )
                print(f"Created user '{u['email']}' role={u['role'].value}")
            await db.commit()

        # Synchronize to society_default schema so multi-tenant queries resolve cleanly
        async with engine.begin() as conn:
            await conn.execute(text("CREATE SCHEMA IF NOT EXISTS society_default;"))
            await conn.execute(text("CREATE TABLE IF NOT EXISTS society_default.users (LIKE public.users INCLUDING ALL);"))
            await conn.execute(text("INSERT INTO society_default.users SELECT * FROM public.users ON CONFLICT (email) DO UPDATE SET hashed_password = EXCLUDED.hashed_password, role = EXCLUDED.role;"))
            
        print("✅ All default demo accounts (admin, manager, resident1, gateway) verified and synchronized.")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
