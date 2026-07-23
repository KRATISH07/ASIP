import os
import pytest
import pandas as pd
import numpy as np
from app.ml.features import (
    extract_features, 
    get_feature_schema_hash, 
    FEATURE_COLUMNS, 
    SEVERITY_MAP, 
    INCIDENT_TYPE_MAP
)
from app.services.predictive_service import _load_models, predict_impact

def test_feature_extraction_columns_and_defaults():
    # Construct a dummy DataFrame mimicking raw records
    df = pd.DataFrame([
        {
            "severity": "critical",
            "incident_type": "water_shortage",
            "affected_residents": 250,
            "timestamp": "2026-06-15T12:00:00"
        },
        {
            "severity": "unknown_sev", # test fallback default
            "incident_type": "unknown_type", # test fallback default
            "affected_residents": None, # test fallback default
            # Omitted timestamp to test default hour/day/weekend logic
        }
    ])
    
    X = extract_features(df)
    
    # Assert return type and columns
    assert isinstance(X, pd.DataFrame)
    assert list(X.columns) == FEATURE_COLUMNS
    
    # Assert values for first row (explicit inputs)
    assert X.loc[0, "severity_encoded"] == SEVERITY_MAP["critical"] # 4
    assert X.loc[0, "incident_type_encoded"] == INCIDENT_TYPE_MAP["water_shortage"] # 1
    assert X.loc[0, "affected_residents"] == 250.0
    assert X.loc[0, "hour_of_day"] == 12
    assert X.loc[0, "day_of_week"] == 0 # 2026-06-15 is Monday (0)
    assert X.loc[0, "is_weekend"] == 0
    
    # Assert values for second row (defaults)
    assert X.loc[1, "severity_encoded"] == 2 # Default to medium (2)
    assert X.loc[1, "incident_type_encoded"] == 5 # Default to abnormal_infrastructure (5)
    assert X.loc[1, "affected_residents"] == 50.0 # Default
    assert 0 <= X.loc[1, "hour_of_day"] <= 23
    assert 0 <= X.loc[1, "day_of_week"] <= 6

def test_schema_hash_stability():
    h1 = get_feature_schema_hash()
    h2 = get_feature_schema_hash()
    assert h1 == h2
    assert isinstance(h1, str)
    assert len(h1) == 64 # SHA-256 hex digest

@pytest.mark.asyncio
async def test_predict_impact_with_ml_models():
    # Ensure models are trained and can be loaded
    models = _load_models()
    if models is None:
        pytest.skip("ML models not trained or metadata mismatch; skipping prediction test")
        
    incident = {
        "type": "power_outage",
        "severity": "high",
        "affected_residents": 150
    }
    
    # Run predict_impact. This should load the ML models because we didn't mock _load_models in this test module.
    prediction = await predict_impact(
        incident_event=incident,
        sensor_data={},
        historical_context=[]
    )
    
    # Assert predictions exist and are floats
    assert "predicted_outage_hrs" in prediction
    assert "estimated_repair_cost" in prediction
    assert "prediction_interval" in prediction
    assert "cost_prediction_interval" in prediction
    
    # Check monotonicity constraints
    duration = prediction["predicted_outage_hrs"]
    dur_interval = prediction["prediction_interval"]
    assert dur_interval["lower_90"] <= duration <= dur_interval["upper_90"]
    
    cost = prediction["estimated_repair_cost"]
    cost_interval = prediction["cost_prediction_interval"]
    assert cost_interval["lower_90"] <= cost <= cost_interval["upper_90"]
    
    assert "Used trained HistGradientBoostingRegressor ML" in prediction["reasoning"]
