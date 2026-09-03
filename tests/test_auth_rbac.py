"""
test_auth_rbac.py — Tests for Tier 1 Lightweight Role-Based Access Control (RBAC)
================================================================================
Verifies that:
1. Privileged write endpoints reject unauthenticated requests with 401 Unauthorized.
2. Privileged write endpoints reject unauthorized roles with 403 Forbidden.
3. Privileged write endpoints succeed with the correct role's Bearer token.
4. Read-only endpoints remain 100% open without requiring any token.
5. Login and token issuance work for all 4 demo profiles.
"""

import pytest
from starlette.testclient import TestClient

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from main import app
from auth import create_access_token, DEMO_PROFILES

client = TestClient(app)


def get_token_for_role(role: str) -> str:
    """Helper to generate a valid signed JWT for testing."""
    profile = DEMO_PROFILES[role]
    return create_access_token(profile)


# ===========================================================================
# 1. Login & Token Verification Tests
# ===========================================================================

def test_login_by_role_quick_demo():
    for role in ["registrar", "community_member", "bank", "citizen"]:
        res = client.post("/auth/login", json={"role": role})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["role"] == role
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "honesty_label" in data


def test_login_with_valid_credentials():
    res = client.post("/auth/login", json={"username": "registrar_up", "password": "bhoomi_registrar_2026"})
    assert res.status_code == 200
    assert res.json()["role"] == "registrar"


def test_login_with_invalid_credentials():
    res = client.post("/auth/login", json={"username": "registrar_up", "password": "wrong_password"})
    assert res.status_code == 401
    assert "Invalid username or password" in res.json()["detail"]


def test_auth_me_endpoint():
    # Without token -> anonymous
    res = client.get("/auth/me")
    assert res.status_code == 200
    assert res.json()["authenticated"] is False

    # With registrar token -> authenticated
    token = get_token_for_role("registrar")
    res2 = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["authenticated"] is True
    assert data2["user"]["role"] == "registrar"


# ===========================================================================
# 2. Privileged Write Endpoints — Unauthorized / Forbidden Checks
# ===========================================================================

def test_seal_parcel_without_token_rejected_401():
    res = client.post("/seal/UP231000000001", json={"declared_value_inr": 500000.0})
    assert res.status_code == 401
    assert "Authentication required" in res.json()["detail"]


def test_seal_parcel_with_citizen_token_rejected_403():
    citizen_token = get_token_for_role("citizen")
    res = client.post(
        "/seal/UP231000000001",
        json={"declared_value_inr": 500000.0},
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert res.status_code == 403
    assert "Access forbidden" in res.json()["detail"]


def test_seal_parcel_with_bank_token_rejected_403():
    bank_token = get_token_for_role("bank")
    res = client.post(
        "/seal/UP231000000001",
        json={"declared_value_inr": 500000.0},
        headers={"Authorization": f"Bearer {bank_token}"},
    )
    assert res.status_code == 403


def test_seal_parcel_with_registrar_token_accepted():
    registrar_token = get_token_for_role("registrar")
    res = client.post(
        "/seal/UP231000000001",
        json={"declared_value_inr": 500000.0},
        headers={"Authorization": f"Bearer {registrar_token}"},
    )
    # Status code is 200 (not 401 or 403)
    assert res.status_code == 200
    data = res.json()
    assert "sealed" in data


def test_mutate_parcel_without_token_rejected_401():
    res = client.post("/mutate/UP231000000001", json={
        "new_owner_name": "Test",
        "new_owner_id_hash": "a" * 64,
        "declared_value_inr": 500000.0,
    })
    assert res.status_code == 401


def test_mutate_parcel_with_wrong_role_rejected_403():
    comm_token = get_token_for_role("community_member")
    res = client.post(
        "/mutate/UP231000000001",
        json={
            "new_owner_name": "Test",
            "new_owner_id_hash": "a" * 64,
            "declared_value_inr": 500000.0,
        },
        headers={"Authorization": f"Bearer {comm_token}"},
    )
    assert res.status_code == 403


def test_pool_claim_without_token_rejected_401():
    res = client.post("/pool/claim/UP231000000001", json={"claimant_address": "0x123"})
    assert res.status_code == 401


def test_community_vote_without_token_rejected_401():
    res = client.post("/community/vote", json={"action_id": 0, "member_indices": [0, 1]})
    assert res.status_code == 401


def test_community_vote_with_bank_token_rejected_403():
    bank_token = get_token_for_role("bank")
    res = client.post(
        "/community/vote",
        json={"action_id": 0, "member_indices": [0, 1]},
        headers={"Authorization": f"Bearer {bank_token}"},
    )
    assert res.status_code == 403
    assert "Access forbidden" in res.json()["detail"]


def test_community_propose_without_token_rejected_401():
    res = client.post("/community/propose", json={"description": "Test proposal"})
    assert res.status_code == 401


def test_community_propose_with_community_member_token_accepted():
    token = get_token_for_role("community_member")
    res = client.post(
        "/community/propose",
        json={"description": "Authorize Forest Resource Leasing (Tendu Leaves)"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert "status_label" in res.json()


# ===========================================================================
# 3. Read-Only Endpoints — 100% Open (Curtain Principle & Public Transparency)
# ===========================================================================

def test_read_only_endpoints_open_without_token():
    open_endpoints = [
        "/health",
        "/parcels/?limit=5",
        "/parcels/UP231000000001",
        "/parcels/UP231000000001/mirror-score",
        "/sealed/UP231000000001",
        "/pool/balance",
        "/pool/premium-preview/UP231000000001?declared_value=500000",
        "/community/info",
        "/community/gini",
        "/villages/",
        "/auth/roles",
    ]
    for ep in open_endpoints:
        res = client.get(ep)
        assert res.status_code == 200, f"Endpoint {ep} should be open but returned HTTP {res.status_code}"
