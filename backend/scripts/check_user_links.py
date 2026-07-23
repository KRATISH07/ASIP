import asyncio
import sys
from sqlalchemy import select

sys.path.insert(0, "/Users/kratish/study/languages/ASIP/backend")
from app.db.session import AsyncSessionFactory
from app.db.models.user import User

async def main():
    async with AsyncSessionFactory() as db:
        res = await db.execute(select(User).where(User.email.in_(["resident1@asip.ai", "admin@asip.ai", "manager@asip.ai"])))
        users = res.scalars().all()
        print("Logged-in Users check:")
        for u in users:
            print(f" - Email: {u.email}, Role: {u.role}, Resident ID: {u.resident_id}, Contractor ID: {u.contractor_id}")

if __name__ == "__main__":
    asyncio.run(main())
