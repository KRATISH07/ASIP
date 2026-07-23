import asyncio
import httpx
import time

async def main():
    headers = {"Authorization": "Bearer demo-token"}
    payload = {
        "type": "tank_overflow",
        "severity": "high",
        "confidence": 1.0,
        "description": "Resident Complaint (Tower Z, Room 999): test water leak",
        "sensor_data": {"manual_report": True}
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create
        print("Sending POST request to /incidents/ ...")
        res = await client.post("http://127.0.0.1:8000/incidents/", json=payload, headers=headers)
        print("Create response status:", res.status_code)
        create_data = res.json()
        print("Create response data:", create_data)
        
        incident_id = create_data["id"]
        
        print("\nWaiting 20 seconds for background AI pipeline to complete...")
        await asyncio.sleep(20)
        
        # Fetch updated
        print("Fetching updated incident details...")
        res2 = await client.get(f"http://127.0.0.1:8000/incidents/{incident_id}", headers=headers)
        print("Get response status:", res2.status_code)
        get_data = res2.json()
        print("Get response data:", get_data)

if __name__ == "__main__":
    asyncio.run(main())
