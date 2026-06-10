from app.services.contractor_service import compute_ranking_from_data


def test_contractor_a_ranked_higher_than_b():
    # Contractor A: high success, fast repair
    contractor_a = {
        "id": "a",
        "name": "Contractor A",
        "success_rate": 0.95,
        "avg_response_time_hrs": 3.0,
        "total_jobs": 20,
        "is_active": True,
        "rating": 4.7,
    }

    # Contractor B: lower success, slower
    contractor_b = {
        "id": "b",
        "name": "Contractor B",
        "success_rate": 0.70,
        "avg_response_time_hrs": 6.0,
        "total_jobs": 15,
        "is_active": True,
        "rating": 4.0,
    }

    contractors = [contractor_a, contractor_b]
    rankings = compute_ranking_from_data(contractors, history_map=None, k=2)

    assert len(rankings) == 2
    # Contractor A should be first
    assert rankings[0]["name"] == "Contractor A"
    assert rankings[0]["final_score"] > rankings[1]["final_score"]
