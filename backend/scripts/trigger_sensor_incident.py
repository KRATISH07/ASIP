#!/usr/bin/env python3
"""
ASIP Sensor Incident Trigger Script
Queries the database for Tower A, logins to get the auth token,
and sends a critical sensor reading to trigger the AI workflow.
"""
import asyncio
import sys
import os
from datetime import datetime, timezone
import httpx

# Add parent directory to path to allow importing app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import AsyncSessionFactory
from app.db.models.tower import Tower
from sqlalchemy import select

API_URL = "http://127.0.0.1:8000"

async def main():
    print("Connecting to database...")
    async with AsyncSessionFactory() as db:
        # Get a valid tower from greenfield heights
        from app.core.tenant_context import set_tenant_schema
        set_tenant_schema("society_default")
        
        result = await db.execute(select(Tower).order_by(Tower.name.asc()))
        tower = result.scalars().first()
        if not tower:
            print("❌ No towers found in the database. Make sure seeds are run.")
            return
        
        tower_id = str(tower.id)
        tower_name = tower.name
        print(f"✅ Found tower: {tower_name} (ID: {tower_id})")

    # 1. Login as Admin to get bearer token
    print("\nAuthenticating with ASIP API...")
    async with httpx.AsyncClient() as client:
        try:
            login_res = await client.post(
                f"{API_URL}/auth/login",
                json={"email": "admin@asip.ai", "password": "admin123"}
            )
            login_res.raise_for_status()
            token = login_res.json()["access_token"]
            print("✅ Successfully logged in as admin@asip.ai")
        except Exception as e:
            print(f"❌ Failed to login: {e}")
            return

        # 2. Trigger anomaly payload (Water Pressure Drop)
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "tower_id": tower_id,
            "sensor_type": "water_pressure",
            "value": 0.2, # critical <= 0.5
            "unit": "bar",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "idempotency_key": None
        }

        print(f"\nSending critical water pressure reading (0.2 bar) for {tower_name}...")
        try:
            res = await client.post(
                f"{API_URL}/incidents/sensor-data",
                json=payload,
                headers=headers
            )
            res.raise_for_status()
            print("🎉 Response status:", res.status_code)
            print("🎉 Response body:", res.json())
            print("\nAI multi-agent workflow has been launched in the background!")
            print("Check the incidents/dashboard page in your web app to watch the logs.")
        except Exception as e:
            print(f"❌ Failed to send sensor reading: {e}")

if __name__ == "__main__":
    asyncio.run(main())
