from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_standard_scenario_review():
    response = client.post(
        "/v1/reviews",
        json={
            "brief": (
                "2 bedroom apartment, 92 sq m. Bedroom 1, Bedroom 2 / Study, "
                "Kitchen, Living room. Need to work from home and host parents. "
                "Prefer open feel, visual connection, and privacy. "
                "8-seat dining table wanted. "
                "Maximize storage while keeping wide circulation."
            )
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert any(
        "North orientation" in item for item in data["missing_information"]
    )
    assert any(
        "8-seat dining table" in item and "spatial footprint conflict" in item
        for item in data["contradictions"]
    )
    assert any(
        rec["requires_human_approval"] is True
        for rec in data["recommendations"]
    )


def test_human_approval_decision():
    create_response = client.post(
        "/v1/reviews",
        json={
            "brief": (
                "2 bedroom apartment, 92 sq m. Bedroom 1, Bedroom 2 / Study, "
                "Kitchen, Living room. Need to work from home and host parents. "
                "Prefer open feel, visual connection, and privacy. "
                "8-seat dining table wanted."
            )
        },
    )
    assert create_response.status_code == 200
    run_id = create_response.json()["run_id"]
    recommendation_id = create_response.json()["recommendations"][0]["id"]

    response = client.post(
        f"/v1/reviews/{run_id}/decisions",
        json={"recommendation_id": recommendation_id, "action": "accept"},
    )
    assert response.status_code == 200
    assert response.json()["new_status"] == "accept"


def test_failure_path_not_found():
    missing_review = client.get("/v1/reviews/invalid-id-123")
    assert missing_review.status_code == 404

    create_response = client.post(
        "/v1/reviews",
        json={"brief": "Sample brief for failure path test."},
    )
    assert create_response.status_code == 200
    run_id = create_response.json()["run_id"]

    bad_recommendation = client.post(
        f"/v1/reviews/{run_id}/decisions",
        json={"recommendation_id": "fake-recommendation-id", "action": "accept"},
    )
    assert bad_recommendation.status_code == 404