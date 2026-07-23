import hashlib
import json
import pandas as pd
from typing import List, Dict, Any

# Map categories to numbers for canonical feature encoding
SEVERITY_MAP: Dict[str, int] = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4
}

INCIDENT_TYPE_MAP: Dict[str, int] = {
    "water_pressure_drop": 0,
    "water_shortage": 1,
    "tank_overflow": 2,
    "power_outage": 3,
    "power_overload": 4,
    "abnormal_infrastructure": 5
}

# The exact columns expected by the model
FEATURE_COLUMNS: List[str] = [
    "severity_encoded",
    "incident_type_encoded",
    "affected_residents",
    "hour_of_day",
    "day_of_week",
    "is_weekend"
]

def get_feature_schema_hash() -> str:
    """Returns a stable hash representing the feature schema definition.
    
    If the list of columns or order changes, the hash changes. This is used
    as a safety contract to ensure that loaded model files match the running
    feature extraction code.
    """
    schema_info = {
        "columns": FEATURE_COLUMNS,
        "severity_map": SEVERITY_MAP,
        "incident_type_map": INCIDENT_TYPE_MAP
    }
    serialized = json.dumps(schema_info, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """Canonical feature extraction shared by training and serving.
    
    Expects a DataFrame containing the following columns:
    - severity: str ('low', 'medium', 'high', 'critical')
    - incident_type: str
    - affected_residents: int/float
    - timestamp: datetime or string representation of a datetime
    
    Returns a DataFrame with numerical columns matching FEATURE_COLUMNS.
    """
    df_out = pd.DataFrame(index=df.index)
    
    # 1. Encode Severity
    severity_series = df["severity"].astype(str).str.lower()
    df_out["severity_encoded"] = severity_series.map(SEVERITY_MAP).fillna(2).astype(int) # Default to medium
    
    # 2. Encode Incident Type
    type_series = df["incident_type"].astype(str)
    df_out["incident_type_encoded"] = type_series.map(INCIDENT_TYPE_MAP).fillna(5).astype(int) # Default to abnormal_infrastructure
    
    # 3. Affected Residents
    if "affected_residents" in df.columns:
        df_out["affected_residents"] = pd.to_numeric(df["affected_residents"], errors="coerce").fillna(50).astype(float)
    else:
        df_out["affected_residents"] = 50.0
        
    if "timestamp" in df.columns:
        timestamps = pd.to_datetime(df["timestamp"])
        # Handle missing timestamps by filling with current time
        now = pd.Timestamp.now()
        timestamps = timestamps.fillna(now)
        df_out["hour_of_day"] = timestamps.dt.hour.astype(int)
        df_out["day_of_week"] = timestamps.dt.dayofweek.astype(int)
        df_out["is_weekend"] = (timestamps.dt.dayofweek >= 5).astype(int)
    else:
        # Fallbacks for serving when timestamp is not supplied
        now = pd.Timestamp.now()
        df_out["hour_of_day"] = now.hour
        df_out["day_of_week"] = now.dayofweek
        df_out["is_weekend"] = int(now.dayofweek >= 5)
        
    return df_out[FEATURE_COLUMNS]
