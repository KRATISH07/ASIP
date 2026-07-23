import os
import sys
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Setup python path to import app modules if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Define constants directly to make script robust
INCIDENT_TYPES = [
    "water_pressure_drop",
    "water_shortage",
    "tank_overflow",
    "power_outage",
    "power_overload",
    "abnormal_infrastructure"
]

SEVERITIES = ["low", "medium", "high", "critical"]

def generate_data(num_records: int = 12000, seed: int = 42) -> pd.DataFrame:
    np.random.seed(seed)
    random.seed(seed)
    
    data = []
    start_date = datetime.now() - timedelta(days=365)
    
    # Severity properties for Log-Normal distribution of outage duration
    # mean_log and sigma for LogNormal(mean_log, sigma^2)
    severity_params = {
        "low": {"mean_log": np.log(1.5), "sigma": 0.3, "cost_mult": 150.0},
        "medium": {"mean_log": np.log(4.0), "sigma": 0.4, "cost_mult": 300.0},
        "high": {"mean_log": np.log(12.0), "sigma": 0.5, "cost_mult": 600.0},
        "critical": {"mean_log": np.log(36.0), "sigma": 0.6, "cost_mult": 1200.0}
    }
    
    # Incident type multipliers for duration and cost
    type_multipliers = {
        "water_pressure_drop": {"duration": 0.8, "cost": 0.9},
        "water_shortage": {"duration": 1.2, "cost": 1.1},
        "tank_overflow": {"duration": 0.9, "cost": 1.2},
        "power_outage": {"duration": 1.5, "cost": 1.5},
        "power_overload": {"duration": 1.3, "cost": 1.4},
        "abnormal_infrastructure": {"duration": 1.0, "cost": 1.0}
    }
    
    for i in range(num_records):
        severity = random.choice(SEVERITIES)
        incident_type = random.choice(INCIDENT_TYPES)
        
        # Base log-normal duration parameters
        params = severity_params[severity]
        t_mult = type_multipliers[incident_type]
        
        # Adjust mean_log based on type multiplier
        mean_log = params["mean_log"] + np.log(t_mult["duration"])
        sigma = params["sigma"]
        
        # Generate duration (hours) - must be strictly positive
        actual_outage_hrs = np.random.lognormal(mean_log, sigma)
        actual_outage_hrs = max(0.1, round(actual_outage_hrs, 2))
        
        # Base cost scales with duration, severity cost multiplier, type cost multiplier, and random noise
        # Base cost per hour
        cost_base = actual_outage_hrs * params["cost_mult"] * t_mult["cost"]
        # Add log-normal noise to cost (unexpected issues, parts, etc.)
        cost_noise = np.random.lognormal(np.log(200.0), 0.5)
        actual_cost = cost_base + cost_noise
        actual_cost = max(50.0, round(actual_cost, 2))
        
        # Affected residents (more affected on critical / water/power shortages)
        if severity == "low":
            affected_residents = random.randint(5, 30)
        elif severity == "medium":
            affected_residents = random.randint(25, 120)
        elif severity == "high":
            affected_residents = random.randint(100, 500)
        else: # critical
            affected_residents = random.randint(400, 2500)
            
        # Add more residents for water/power shortages
        if incident_type in ["water_shortage", "power_outage"]:
            affected_residents = int(affected_residents * 1.5)
            
        # Random timestamp in the last 365 days
        random_secs = random.randint(0, 365 * 24 * 3600)
        timestamp = start_date + timedelta(seconds=random_secs)
        
        data.append({
            "incident_type": incident_type,
            "severity": severity,
            "affected_residents": affected_residents,
            "timestamp": timestamp.isoformat(),
            "actual_outage_hrs": actual_outage_hrs,
            "actual_cost": actual_cost
        })
        
    df = pd.DataFrame(data)
    # Sort chronologically
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(by="timestamp").reset_index(drop=True)
    return df

if __name__ == "__main__":
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../app/ml/data"))
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "synthetic_incidents.csv")
    
    print(f"Generating synthetic incident data...")
    df = generate_data(12000)
    df.to_csv(output_file, index=False)
    print(f"Saved {len(df)} records to {output_file}")
    
    # Print some stats to verify
    print("\nSummary statistics by Severity:")
    print(df.groupby("severity")[["actual_outage_hrs", "actual_cost"]].agg(["mean", "median", "max"]))
