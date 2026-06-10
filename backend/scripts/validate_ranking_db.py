"""Validate contractor ranking using live DB data (contractors + contractor_history).
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.db.session import AsyncSessionFactory
from app.services.contractor_service import rank_contractors


async def main():
    async with AsyncSessionFactory() as db:
        ranked = await rank_contractors(db, incident_type="water_leak", k=5)
        import json
        print(json.dumps(ranked, indent=2))


if __name__ == '__main__':
    asyncio.run(main())
