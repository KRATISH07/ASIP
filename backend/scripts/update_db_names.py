import asyncio
import sys
from sqlalchemy import text

sys.path.insert(0, "/Users/kratish/study/languages/ASIP/backend")
from app.db.session import AsyncSessionFactory

async def update_db_names():
    async with AsyncSessionFactory() as db:
        # Check society_default schema (resident profile)
        await db.execute(text('SET search_path TO "society_default", public'))
        
        # Update residents table
        res_update = await db.execute(text("""
            UPDATE residents 
            SET name = 'Kratish Mewada' 
            WHERE name = 'Priya Sharma' OR email = 'resident1@asip.ai'
        """))
        print(f"Updated resident name in residents table. Rows affected: {res_update.rowcount}")
        
        # Update public.users table
        user_update = await db.execute(text("""
            UPDATE public.users 
            SET full_name = 'Kratish Mewada' 
            WHERE full_name = 'Priya Sharma' OR email = 'resident1@asip.ai'
        """))
        print(f"Updated user full name in users table. Rows affected: {user_update.rowcount}")
        
        await db.commit()
        print("Database update successfully completed!")

if __name__ == "__main__":
    asyncio.run(update_db_names())
