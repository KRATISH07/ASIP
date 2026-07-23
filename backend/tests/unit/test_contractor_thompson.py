import pytest
import numpy as np
from app.services.contractor_service import compute_ranking_from_data

def test_thompson_sampling_exploration_and_exploitation():
    # Define contractors
    # Contractor A: established, highly successful
    # Contractor B: brand new, 0 jobs
    # Contractor C: established, very poor success rate
    contractors = [
        {
            "id": "A",
            "name": "Reliable Established",
            "success_rate": 0.80,
            "avg_response_time_hrs": 2.0,
            "total_jobs": 5,
            "is_active": True,
            "rating": 4.0,
            "specializations": ["water"]
        },
        {
            "id": "B",
            "name": "New Unknown",
            "success_rate": 0.5, # Prior success rate
            "avg_response_time_hrs": 2.0,
            "total_jobs": 0,
            "is_active": True,
            "rating": 4.0,
            "specializations": ["water"]
        },
        {
            "id": "C",
            "name": "Unreliable Established",
            "success_rate": 0.20,
            "avg_response_time_hrs": 2.0,
            "total_jobs": 100,
            "is_active": True,
            "rating": 1.5,
            "specializations": ["water"]
        }
    ]
    
    # Run ranking multiple times to observe the stochastic properties
    num_trials = 200
    first_place_counts = {"A": 0, "B": 0, "C": 0}
    
    for _ in range(num_trials):
        ranked = compute_ranking_from_data(contractors, k=3)
        top_contractor = ranked[0]["contractor_id"]
        first_place_counts[top_contractor] += 1
        
    print(f"\nThompson Sampling first place counts over {num_trials} trials:")
    print(first_place_counts)
    
    # Exploitation: Contractor A (highly reliable) should be selected first most of the time
    assert first_place_counts["A"] > first_place_counts["B"]
    
    # Exploration: Contractor B (new, 0 jobs) should be selected first occasionally
    assert first_place_counts["B"] > 0
    
    # Avoid bad exploration: Contractor C (unreliable, many jobs) has tight posterior around 0.20
    # and should be selected first zero times or extremely rarely
    assert first_place_counts["C"] < (num_trials * 0.05)
