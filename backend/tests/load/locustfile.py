import uuid
import random
from datetime import datetime, timezone
from locust import HttpUser, task, between

class ASIPLoadTestUser(HttpUser):
    wait_time = between(0.5, 2.0)
    
    def on_start(self):
        """Log in at the start of the session to obtain a JWT token."""
        self.auth_header = {}
        # Attempt to log in with seeded user credentials
        login_data = {
            "email": "admin@asip.ai",
            "password": "password123"
        }
        try:
            with self.client.post("/auth/login", json=login_data, catch_response=True) as response:
                if response.status_code == 200:
                    token = response.json().get("access_token")
                    self.auth_header = {"Authorization": f"Bearer {token}"}
                    response.success()
                else:
                    response.failure(f"Failed to log in: {response.text}")
        except Exception as e:
            print(f"Exception during login: {str(e)}")

    @task(5)
    def health_check(self):
        """GET /health - Public endpoint."""
        self.client.get("/health")

    @task(3)
    def list_incidents(self):
        """GET /incidents - Authenticated endpoint."""
        if self.auth_header:
            self.client.get("/incidents", headers=self.auth_header)

    @task(2)
    def get_analytics(self):
        """GET /analytics/learning - Authenticated endpoint."""
        if self.auth_header:
            self.client.get("/analytics/learning", headers=self.auth_header)

    @task(1)
    def submit_sensor_data(self):
        """POST /incidents/sensor-data - Authenticated endpoint.
        
        Submits sensor values representing normal fluctuations (non-incident) 
        as well as occasional anomalies to test background trigger logic.
        """
        if not self.auth_header:
            return
            
        # 90% chance of a normal sensor reading (doesn't trigger slow AI agent pipeline)
        # 10% chance of an anomalous reading (triggers background agent run)
        is_anomaly = random.random() < 0.10
        
        if is_anomaly:
            # Low water pressure triggers incident
            sensor_type = "water_pressure"
            value = round(random.uniform(0.1, 0.4), 2)
            unit = "bar"
        else:
            # Normal water pressure
            sensor_type = "water_pressure"
            value = round(random.uniform(1.5, 3.5), 2)
            unit = "bar"
            
        payload = {
            "tower_id": str(uuid.UUID("00000000-0000-0000-0000-000000000001")),
            "sensor_type": sensor_type,
            "value": value,
            "unit": unit,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {"source": "locust_load_test"}
        }
        
        self.client.post("/incidents/sensor-data", json=payload, headers=self.auth_header)
