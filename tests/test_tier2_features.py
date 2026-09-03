"""
test_tier2_features.py — Automated Tests for Tier 2 (PDF Certificate & Dispute Filing)
======================================================================================
Verifies:
1. GET /parcels/{ulpin}/certificate returns 400 if parcel is unsealed (presumptive record).
2. GET /parcels/{ulpin}/certificate returns 200 with valid binary PDF content when parcel is sealed.
3. POST /disputes/file successfully registers a grievance off-chain with DSP-2026-XXXX ID.
4. POST /disputes/file rejects non-existent ULPIN with 404.
5. GET /disputes/ lists registered disputes.
6. POST /disputes/{id}/resolve requires registrar role (rejects unauthenticated with 401).
7. POST /disputes/{id}/resolve with registrar token successfully updates status to RESOLVED.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from starlette.testclient import TestClient
from main import app
from auth import create_access_token, DEMO_PROFILES
from web3_bridge import get_bridge

client = TestClient(app)


def get_token_for_role(role: str) -> str:
    profile = DEMO_PROFILES[role]
    return create_access_token(profile)


# ===========================================================================
# 1. Title Certificate Tests (Tier 2a)
# ===========================================================================

def test_certificate_rejected_for_unsealed_parcel():
    # Make sure an unsealed parcel returns 400
    res = client.get("/parcels/UP231000000006/certificate")
    assert res.status_code == 400
    assert "Cannot generate Title Attestation Certificate" in res.json()["detail"]
    assert "presumptive record only" in res.json()["detail"]


def test_certificate_succeeds_for_sealed_parcel():
    # Seal UP231000000001 first using registrar token
    reg_token = get_token_for_role("registrar")
    seal_res = client.post(
        "/seal/UP231000000001",
        json={"declared_value_inr": 1000000.0},
        headers={"Authorization": f"Bearer {reg_token}"},
    )
    assert seal_res.status_code == 200

    # Request the PDF certificate
    res = client.get("/parcels/UP231000000001/certificate")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in res.headers["content-disposition"]
    assert res.content.startswith(b"%PDF-")
    assert len(res.content) > 1000  # Non-trivial PDF size


def test_certificate_nonexistent_parcel_returns_404():
    res = client.get("/parcels/NONEXISTENT999/certificate")
    assert res.status_code == 404


# ===========================================================================
# 2. Dispute / Grievance Filing Tests (Tier 2b + Part A Updates)
# ===========================================================================

def test_file_dispute_unauthenticated_rejected_401():
    # Part A1 Verification: calling without token must be rejected with 401
    res = client.post("/disputes/file", json={
        "ulpin": "UP231000000001",
        "complainant_name": "Anonymous Attacker",
        "dispute_type": "boundary_overlap",
        "description": "Attempting unauthenticated spam filing.",
    })
    assert res.status_code == 401
    assert "detail" in res.json()


def test_file_dispute_success():
    # Part A1 Verification: calling with citizen token succeeds
    cit_token = get_token_for_role("citizen")
    res = client.post(
        "/disputes/file",
        json={
            "ulpin": "UP231000000001",
            "complainant_name": "Ramesh Kumar",
            "contact_info": "+91-98765-43210",
            "dispute_type": "boundary_overlap",
            "description": "Neighbor installed irrigation borewell encroaching 2 meters over the eastern boundary line.",
            "evidence_summary": "Village Amin field measurement report dated August 2026.",
        },
        headers={"Authorization": f"Bearer {cit_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["dispute_id"].startswith("DSP-2026-")
    assert data["ulpin"] == "UP231000000001"
    assert data["dispute"]["status"] == "OPEN"


def test_file_dispute_nonexistent_ulpin_404():
    cit_token = get_token_for_role("citizen")
    res = client.post(
        "/disputes/file",
        json={
            "ulpin": "FAKEULPIN000000",
            "complainant_name": "Test User",
            "dispute_type": "encroachment",
            "description": "Testing 404 response.",
        },
        headers={"Authorization": f"Bearer {cit_token}"},
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"]


def test_list_disputes_privacy_scoping():
    # Part A3 Verification:
    # Unauthenticated / non-registrar caller must have contact_info redacted
    res_anon = client.get("/disputes/")
    assert res_anon.status_code == 200
    anon_data = res_anon.json()
    assert len(anon_data["disputes"]) >= 1
    for d in anon_data["disputes"]:
        assert d["contact_info"] == "[Restricted - Sub-Registrar Access Only]"

    # Authenticated registrar caller must receive unredacted contact_info
    reg_token = get_token_for_role("registrar")
    res_reg = client.get("/disputes/", headers={"Authorization": f"Bearer {reg_token}"})
    assert res_reg.status_code == 200
    reg_data = res_reg.json()
    assert len(reg_data["disputes"]) >= 1
    # Check that at least one dispute has unredacted contact info
    has_unredacted = any(d["contact_info"] != "[Restricted - Sub-Registrar Access Only]" for d in reg_data["disputes"])
    assert has_unredacted, "Registrar view must contain unredacted contact details"



def test_resolve_dispute_requires_registrar_role():
    # Without token -> 401
    res = client.post("/disputes/DSP-2026-0001/resolve", json={
        "status": "RESOLVED",
        "resolution_notes": "Boundary re-measured and accepted by both parties.",
    })
    assert res.status_code == 401

    # With citizen token -> 403
    cit_token = get_token_for_role("citizen")
    res_cit = client.post(
        "/disputes/DSP-2026-0001/resolve",
        json={
            "status": "RESOLVED",
            "resolution_notes": "Attempted resolution by citizen.",
        },
        headers={"Authorization": f"Bearer {cit_token}"},
    )
    assert res_cit.status_code == 403

    # With registrar token -> 200
    reg_token = get_token_for_role("registrar")
    res_reg = client.post(
        "/disputes/DSP-2026-0001/resolve",
        json={
            "status": "RESOLVED",
            "resolution_notes": "Tehsil joint inspection completed. Boundary stones reset per cadastral map coordinates.",
        },
        headers={"Authorization": f"Bearer {reg_token}"},
    )
    assert res_reg.status_code == 200
    assert res_reg.json()["updated_dispute"]["status"] == "RESOLVED"
