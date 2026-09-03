"""
test_tier3_features.py — Automated Tests for Tier 3
====================================================
Verifies:
1. Citizen-initiated mutation requests require citizen authentication (reject unauth with 401).
2. Mutation request created with valid citizen token succeeds with MUT-2026-XXXX ID.
3. Non-existent ULPIN returns 404.
4. Approving mutation requires registrar role (rejects citizen/unauth).
5. Approving mutation RE-INVOKES Mirror Engine and rejects with 422 if proposed data fails reconciliation (e.g. massive area mismatch).
6. Approving clean mutation re-verifies score >= 85 and updates Curtain Ledger seal.
7. Normal usage within rate limits passes with 0 errors.
8. Burst calls exceeding rate limits trigger 429 Too Many Requests.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from starlette.testclient import TestClient
from main import app
from auth import create_access_token, DEMO_PROFILES

client = TestClient(app)


def get_token_for_role(role: str) -> str:
    profile = DEMO_PROFILES[role]
    return create_access_token(profile)


# ===========================================================================
# 1. Citizen-Initiated Mutation Requests (Tier 3a)
# ===========================================================================

def test_mutation_request_unauthenticated_rejected_401():
    res = client.post("/mutation-requests/", json={
        "ulpin": "UP231000000001",
        "applicant_name": "Ramesh Kumar",
        "mutation_type": "sale",
        "new_owner_name": "Sunita Verma",
        "new_owner_id_hash": "7b8f9e1a2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f",
        "declared_value_inr": 1500000.0,
        "deed_reference": "REG-2026-001",
    })
    assert res.status_code == 401


def test_mutation_request_created_with_citizen_token():
    cit_token = get_token_for_role("citizen")
    res = client.post(
        "/mutation-requests/",
        json={
            "ulpin": "UP231000000001",
            "applicant_name": "Ramesh Kumar",
            "mutation_type": "sale",
            "new_owner_name": "Sunita Verma",
            "new_owner_id_hash": "7b8f9e1a2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f",
            "declared_value_inr": 1500000.0,
            "deed_reference": "REG-2026-001",
            "proposed_area_ha": 0.2529,
        },
        headers={"Authorization": f"Bearer {cit_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["request_id"].startswith("MUT-2026-")
    assert data["mutation_request"]["status"] == "PENDING"


def test_mutation_request_nonexistent_ulpin_returns_404():
    cit_token = get_token_for_role("citizen")
    res = client.post(
        "/mutation-requests/",
        json={
            "ulpin": "FAKEULPIN999999",
            "applicant_name": "Test User",
            "mutation_type": "sale",
            "new_owner_name": "New Person",
            "new_owner_id_hash": "1111222233334444555566667777888811112222333344445555666677778888",
            "declared_value_inr": 1000000.0,
            "deed_reference": "REG-FAKE-001",
        },
        headers={"Authorization": f"Bearer {cit_token}"},
    )
    assert res.status_code == 404


def test_mutation_approve_requires_registrar_role():
    # Attempt approval without token -> 401
    res = client.post("/mutation-requests/MUT-2026-0001/approve")
    assert res.status_code == 401

    # Attempt approval with citizen token -> 403
    cit_token = get_token_for_role("citizen")
    res_cit = client.post(
        "/mutation-requests/MUT-2026-0001/approve",
        headers={"Authorization": f"Bearer {cit_token}"},
    )
    assert res_cit.status_code == 403


def test_mutation_approve_rejects_when_mirror_reconciliation_fails():
    """
    CRITICAL SPEC REQUIREMENT:
    Submit a mutation request with data that would fail Mirror Engine reconciliation
    (e.g., a massive area mismatch of 5.0 hectares vs 0.25 hectares polygon),
    and confirm the registrar's approval action rejects it with 422 rather than sealing unconditionally.
    """
    cit_token = get_token_for_role("citizen")
    create_res = client.post(
        "/mutation-requests/",
        json={
            "ulpin": "UP231000000001",
            "applicant_name": "Ramesh Kumar",
            "mutation_type": "sale",
            "new_owner_name": "Fraudulent Buyer",
            "new_owner_id_hash": "9999888877776666555544443333222299998888777766665555444433332222",
            "declared_value_inr": 2000000.0,
            "deed_reference": "DEED-MISMATCH-999",
            "proposed_area_ha": 5.0,  # 5.0 hectares vs ~0.25 hectares polygon = massive mismatch!
        },
        headers={"Authorization": f"Bearer {cit_token}"},
    )
    assert create_res.status_code == 200
    bad_req_id = create_res.json()["request_id"]

    # Now Sub-Registrar attempts to approve this mismatched mutation
    reg_token = get_token_for_role("registrar")
    appr_res = client.post(
        f"/mutation-requests/{bad_req_id}/approve",
        headers={"Authorization": f"Bearer {reg_token}"},
    )
    assert appr_res.status_code == 422
    err_detail = appr_res.json()["detail"]
    assert "Mirror Engine re-verification failed" in err_detail
    assert "below 85 threshold" in err_detail

    # Confirm mutation request status is marked REJECTED
    list_res = client.get(f"/mutation-requests/?ulpin=UP231000000001")
    req = next(r for r in list_res.json()["requests"] if r["request_id"] == bad_req_id)
    assert req["status"] == "REJECTED"
    assert "below 85 threshold" in req["rejection_reason"]


def test_mutation_approve_succeeds_for_clean_parcel():
    cit_token = get_token_for_role("citizen")
    create_res = client.post(
        "/mutation-requests/",
        json={
            "ulpin": "UP231000000001",
            "applicant_name": "Ramesh Kumar",
            "mutation_type": "sale",
            "new_owner_name": "Aarav Sharma",
            "new_owner_id_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "declared_value_inr": 2500000.0,
            "deed_reference": "REG-GENUINE-2026/104",
            "proposed_area_ha": 1.5104,  # Accurate area matching polygon (1.5104 ha)
        },
        headers={"Authorization": f"Bearer {cit_token}"},
    )
    assert create_res.status_code == 200
    clean_req_id = create_res.json()["request_id"]

    reg_token = get_token_for_role("registrar")
    appr_res = client.post(
        f"/mutation-requests/{clean_req_id}/approve",
        headers={"Authorization": f"Bearer {reg_token}"},
    )
    assert appr_res.status_code == 200
    data = appr_res.json()
    assert data["status"] == "success"
    assert data["mirror_score"] >= 85
    assert data["mutation_request"]["status"] == "APPROVED_AND_SEALED"


# ===========================================================================
# 2. Rate Limiting Tests (Tier 3b)
# ===========================================================================

def test_rate_limiting_normal_usage_passes():
    """Confirms 5-10 rapid legitimate requests do not trigger rate limiting."""
    for _ in range(5):
        res = client.get("/parcels/?limit=5")
        assert res.status_code == 200


def test_rate_limiting_burst_exceeded_429():
    """Confirms that excessive rapid spam requests trigger 429 Too Many Requests."""
    statuses = []
    # /auth/login limit is 30/minute
    for _ in range(35):
        res = client.post("/auth/login", json={"role": "citizen"})
        statuses.append(res.status_code)

    assert 429 in statuses, f"Expected 429 in statuses, got {set(statuses)}"

