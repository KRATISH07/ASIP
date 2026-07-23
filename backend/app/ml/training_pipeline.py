import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error

# Add parent directory to sys.path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.ml.features import extract_features, get_feature_schema_hash, FEATURE_COLUMNS

def fetch_real_incidents_from_db() -> list[dict]:
    """Fetch real resolved incidents from database to include in model training."""
    try:
        import asyncio
        from app.db.session import AsyncSessionFactory
        from app.db.models.incident_memory import IncidentMemory
        from sqlalchemy import select

        async def _fetch():
            async with AsyncSessionFactory() as db:
                stmt = select(IncidentMemory).where(IncidentMemory.actual_outage_hrs.isnot(None))
                res = await db.execute(stmt)
                return res.scalars().all()

        memories = asyncio.run(_fetch())
        records = []
        for m in memories:
            records.append({
                "timestamp": m.created_at,
                "incident_type": m.incident_type,
                "severity": m.severity,
                "affected_residents": m.affected_residents,
                "actual_outage_hrs": m.actual_outage_hrs,
                "actual_cost": m.actual_cost,
            })
        return records
    except Exception as e:
        print(f"Warning: Failed to fetch real incidents from database: {e}")
        return []


def train_and_evaluate():
    # 1. Load data
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
    data_path = os.path.join(data_dir, "synthetic_incidents.csv")
    
    if not os.path.exists(data_path):
        print(f"Error: Data file not found at {data_path}. Run synthetic data generation first.")
        sys.exit(1)
        
    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    
    # Fetch and merge real database feedback records
    real_records = fetch_real_incidents_from_db()
    if real_records:
        print(f"Fetched {len(real_records)} real incidents from database. Merging with baseline dataset.")
        df_real = pd.DataFrame(real_records)
        df = pd.concat([df, df_real], ignore_index=True)

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    # Sort chronologically to prevent future leakage
    df = df.sort_values(by="timestamp").reset_index(drop=True)

    
    # 2. Extract features
    print("Extracting canonical features...")
    X = extract_features(df)
    
    y_duration = df["actual_outage_hrs"]
    y_cost = df["actual_cost"]
    
    print(f"Dataset size: {len(X)} samples.")
    print(f"Features list: {FEATURE_COLUMNS}")
    
    # 3. TimeSeriesSplit Cross Validation for the median (0.50) model
    tscv = TimeSeriesSplit(n_splits=5)
    
    duration_maes = []
    cost_maes = []
    
    print("\n--- Performing TimeSeriesSplit Cross-Validation ---")
    for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_dur_train, y_dur_test = y_duration.iloc[train_idx], y_duration.iloc[test_idx]
        y_cost_train, y_cost_test = y_cost.iloc[train_idx], y_cost.iloc[test_idx]
        
        # Fit median duration model
        model_dur = HistGradientBoostingRegressor(loss="quantile", quantile=0.5, random_state=42)
        model_dur.fit(X_train, y_dur_train)
        pred_dur = model_dur.predict(X_test)
        mae_dur = mean_absolute_error(y_dur_test, pred_dur)
        duration_maes.append(mae_dur)
        
        # Fit median cost model
        model_cost = HistGradientBoostingRegressor(loss="quantile", quantile=0.5, random_state=42)
        model_cost.fit(X_train, y_cost_train)
        pred_cost = model_cost.predict(X_test)
        mae_cost = mean_absolute_error(y_cost_test, pred_cost)
        cost_maes.append(mae_cost)
        
        print(f"Fold {fold+1} | Duration MAE: {mae_dur:.3f} hrs | Cost MAE: ${mae_cost:.2f}")
        
    avg_dur_mae = float(np.mean(duration_maes))
    avg_cost_mae = float(np.mean(cost_maes))
    print(f"Average CV Duration MAE: {avg_dur_mae:.3f} hrs")
    print(f"Average CV Cost MAE: ${avg_cost_mae:.2f}")
    
    # 4. Train final models on the complete dataset
    print("\nTraining final quantile models on all data...")
    quantiles = [0.05, 0.50, 0.95]
    
    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "models"))
    os.makedirs(models_dir, exist_ok=True)
    
    for q in quantiles:
        q_str = f"q{int(q*100):02d}"
        
        # Train and save duration model
        print(f"  Training duration model for quantile {q}...")
        model_dur = HistGradientBoostingRegressor(loss="quantile", quantile=q, random_state=42)
        model_dur.fit(X, y_duration)
        duration_file = os.path.join(models_dir, f"duration_{q_str}.joblib")
        joblib.dump(model_dur, duration_file)
        
        # Train and save cost model
        print(f"  Training cost model for quantile {q}...")
        model_cost = HistGradientBoostingRegressor(loss="quantile", quantile=q, random_state=42)
        model_cost.fit(X, y_cost)
        cost_file = os.path.join(models_dir, f"cost_{q_str}.joblib")
        joblib.dump(model_cost, cost_file)
        
    # 5. Write metadata contract
    schema_hash = get_feature_schema_hash()
    metadata = {
        "trained_at": datetime.utcnow().isoformat(),
        "schema_hash": schema_hash,
        "features": FEATURE_COLUMNS,
        "metrics": {
            "duration_mae_hrs": avg_dur_mae,
            "cost_mae_usd": avg_cost_mae
        }
    }
    
    metadata_path = os.path.join(models_dir, "metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
        
    print(f"\nAll models saved successfully to {models_dir}")
    print(f"Schema Hash: {schema_hash}")
    print(f"Metadata contract written to {metadata_path}")

if __name__ == "__main__":
    train_and_evaluate()
