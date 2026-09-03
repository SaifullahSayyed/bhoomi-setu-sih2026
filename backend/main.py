"""
main.py — Bhoomi Setu FastAPI Backend
======================================
Priority 1b / 1c / 3a | Status: Working Prototype

Exposes REST endpoints for:
  - Parcel listing and filtering
  - Mirror Confidence Scoring (single + batch)
  - Sealing (CurtainLedger), mutation, and state retrieval
  - Assurance Pool operations (premium, claims, pool balance)
  - Community Tenure operations (voting, Gini detection)

Run with: uvicorn main:app --reload --port 8000
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from starlette.requests import Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from auth import (
    DEMO_PROFILES,
    DEMO_USERS_BY_USERNAME,
    LoginRequest,
    TokenResponse,
    create_access_token,
    require_role,
    get_current_user_optional,
)
from certificate import generate_title_certificate
from mirror_engine import MirrorEngine, MirrorConfig, get_engine
from off_chain_store import get_store
from web3_bridge import get_bridge

limiter = Limiter(key_func=get_remote_address, default_limits=[])
                                                                             
           
                                                                             
app = FastAPI(
    title="Bhoomi Setu API",
    description=(
        "Backend for Bhoomi Setu (SIH26014) — Integrated GIS-based Land Governance. "
        "Implements Mirror (reconciliation), Curtain (selective disclosure via blockchain sealing), "
        "and Insurance (risk-indexed assurance pool) Torrens principles. "
        "Priority 1–3: Working Prototype. Priority 4: Architecture Demo."
    ),
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],                                           
    allow_methods=["*"],
    allow_headers=["*"],
)

                                                                             
                                                                
                                                                             
DATA_DIR = Path(__file__).parent.parent / "data"

_parcels_cache: list[dict] | None = None
_community_data_cache: dict | None = None


def _load_all_parcels() -> list[dict]:
    global _parcels_cache
    if _parcels_cache is not None:
        return _parcels_cache

    parcels: list[dict] = []
    for fname in ["parcels_village_A.json", "parcels_village_B.json"]:
        fpath = DATA_DIR / fname
        if fpath.exists():
            data = json.loads(fpath.read_text(encoding="utf-8"))
            parcels.extend(data.get("parcels", []))

                                          
    comm_path = DATA_DIR / "parcels_village_C_community.json"
    if comm_path.exists():
        comm = json.loads(comm_path.read_text(encoding="utf-8"))
        parcels.extend(comm.get("parcels", []))

    if not parcels:
        raise RuntimeError(
            "No data found. Run: python scripts/generate_synthetic_data.py"
        )

    _parcels_cache = parcels
    return parcels


def _load_community_data() -> dict:
    global _community_data_cache
    if _community_data_cache is not None:
        return _community_data_cache
    comm_path = DATA_DIR / "parcels_village_C_community.json"
    if not comm_path.exists():
        raise RuntimeError("Community data not found. Run the data generator first.")
    _community_data_cache = json.loads(comm_path.read_text(encoding="utf-8"))
    return _community_data_cache


def _get_parcel_by_ulpin(ulpin: str) -> dict | None:
    return next((p for p in _load_all_parcels() if p["ulpin"] == ulpin), None)


                                                                             
                                          
                                                                             
@app.on_event("startup")
async def startup_event() -> None:
    try:
        parcels = _load_all_parcels()
        engine = get_engine()
        engine.build_index(parcels)
        print(f"[Startup] Mirror Engine indexed {len(parcels)} parcels.")
    except RuntimeError as e:
        print(f"[Startup] Warning: {e}. Generate data before calling scoring endpoints.")


                                                                             
                 
                                                                             
class SealRequest(BaseModel):
    declared_value_inr: float = 0.0
    override_score: int | None = None                                             


class MutateRequest(BaseModel):
    new_owner_name: str
    new_owner_id_hash: str
    declared_value_inr: float


class ClaimRequest(BaseModel):
    claimant_address: str


class VoteRequest(BaseModel):
    action_id: int
    member_indices: list[int]
    offline_batch: bool = False                                               


class ProposeActionRequest(BaseModel):
    description: str


class DisputeFilingRequest(BaseModel):
    ulpin: str
    complainant_name: str
    contact_info: str | None = None
    dispute_type: str = "boundary_overlap"
    description: str
    evidence_summary: str | None = None


class DisputeResolutionRequest(BaseModel):
    status: str = "RESOLVED"
    resolution_notes: str


class MutationFilingRequest(BaseModel):
    ulpin: str
    applicant_name: str
    mutation_type: str = "sale"
    new_owner_name: str
    new_owner_id_hash: str
    declared_value_inr: float
    deed_reference: str
    proposed_area_ha: float | None = None


                                                                             
              
                                                                             
@app.get("/", tags=["health"])
def root() -> dict:
    bridge = get_bridge()
    return {
        "service": "Bhoomi Setu API",
        "status": "running",
        "blockchain_mode": bridge.mode,
        "priority_1_status": "Working Prototype",
        "priority_2_status": "Working Prototype",
        "priority_3_status": "Working Prototype",
        "priority_4_status": "Architecture Demo",
    }


@app.get("/health", tags=["health"])
def health() -> dict:
    try:
        parcels = _load_all_parcels()
        count = len(parcels)
        data_ok = True
    except RuntimeError:
        count = 0
        data_ok = False
    bridge = get_bridge()
    return {
        "data_loaded": data_ok,
        "parcel_count": count,
        "blockchain_mode": bridge.mode,
    }


# ===========================================================================
# Tier 1 — RBAC Authentication Endpoints
# ===========================================================================

@app.post("/auth/login", response_model=TokenResponse, tags=["auth"])
@limiter.limit("30/minute")
def login(request: Request, login_data: LoginRequest) -> dict:
    """
    Tier 1 RBAC — Issues a signed JWT access token for role-based authorization.
    Supports either:
      1. Quick Demo Login by role: {"role": "registrar" | "community_member" | "bank" | "citizen"}
      2. Username/Password Login: {"username": "...", "password": "..."}
    Honesty Label: Prototype RBAC — demo credentials for judging purposes, not a production identity system.
    """
    profile = None
    if login_data.role and login_data.role in DEMO_PROFILES:
        profile = DEMO_PROFILES[login_data.role]
    elif login_data.username and login_data.password:
        candidate = DEMO_USERS_BY_USERNAME.get(login_data.username)
        if candidate and candidate["password"] == login_data.password:
            profile = candidate
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either a valid 'role' (registrar, community_member, bank, citizen) or 'username' & 'password'.",
        )

    token = create_access_token(profile)
    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer",
        "role": profile["role"],
        "username": profile["username"],
        "display_name": profile["display_name"],
        "designation": profile["designation"],
        "jurisdiction": profile.get("jurisdiction", ""),
        "honesty_label": "Prototype RBAC — demo credentials for judging purposes, not a production identity system.",
    }


@app.get("/auth/roles", tags=["auth"])
def list_demo_roles() -> dict:
    """Returns all pre-seeded demo role profiles for 1-click judging evaluation."""
    return {
        "status_label": "Prototype RBAC",
        "honesty_label": "Demo credentials for judging purposes, not a production identity system.",
        "profiles": [
            {
                "role": p["role"],
                "username": p["username"],
                "password": p["password"],
                "display_name": p["display_name"],
                "designation": p["designation"],
                "jurisdiction": p["jurisdiction"],
                "allowed_actions": p["allowed_actions"],
            }
            for p in DEMO_PROFILES.values()
        ],
    }


@app.get("/auth/me", tags=["auth"])
def get_auth_me(user: dict | None = Depends(get_current_user_optional)) -> dict:
    """Returns the authenticated identity from the Bearer token, or anonymous status."""
    if not user:
        return {"authenticated": False, "role": "anonymous"}
    return {"authenticated": True, "user": user}



                                                                             
                  
                                                                             
@app.get("/parcels/", tags=["parcels"])
@limiter.limit("120/minute")
def list_parcels(
    request: Request,
    village: str | None = Query(None, description="Filter by village name"),
    schema_type: str | None = Query(None, description="'individual' or 'community'"),
    score_min: int = Query(0, ge=0, le=100),
    score_max: int = Query(100, ge=0, le=100),
    has_flag: str | None = Query(None, description="Filter by flag keyword (e.g. 'area_mismatch')"),
    limit: int = Query(500, le=1000),
    offset: int = Query(0, ge=0),
) -> dict:
    parcels = _load_all_parcels()
    total_dataset = len(parcels)
    engine = get_engine()

    results = []
    for p in parcels:
        if village and p.get("village", "").lower() != village.lower():
            continue
        if schema_type and p.get("schema_type", "individual") != schema_type:
            continue
        result = engine.score_parcel(p)
        if not (score_min <= result.mirror_score <= score_max):
            continue
        if has_flag and not any(has_flag in f for f in result.flags):
            continue
        results.append({**p, "mirror_result": result.to_dict()})

    total = len(results)
    page = results[offset:offset + limit]
    return {
        "total": total,
        "total_dataset_count": total_dataset,
        "offset": offset,
        "limit": limit,
        "parcels": page,
    }


@app.get("/parcels/{ulpin}", tags=["parcels"])
def get_parcel(ulpin: str) -> dict:
    p = _get_parcel_by_ulpin(ulpin)
    if not p:
        raise HTTPException(status_code=404, detail=f"Parcel {ulpin} not found")
    engine = get_engine()
    score = engine.score_parcel(p)
    bridge = get_bridge()
    on_chain = bridge.get_sealed_state(ulpin)
    return {
        "parcel": p,
        "mirror_result": score.to_dict(),
        "on_chain_state": on_chain,
    }


@app.get("/parcels/{ulpin}/certificate", tags=["parcels"])
def get_parcel_certificate(ulpin: str) -> StreamingResponse:
    """
    Tier 2a — Generates and downloads a PDF Torrens Title Attestation Certificate for sealed parcels.
    Requires parcel to have been sealed on Curtain Ledger (score >= 85).
    Honesty Label: Prototype certificate — not a legally issued government document.
    """
    p = _get_parcel_by_ulpin(ulpin)
    if not p:
        raise HTTPException(status_code=404, detail=f"Parcel {ulpin} not found")

    bridge = get_bridge()
    sealed_state = bridge.get_sealed_state(ulpin)

    # Must be sealed on-chain (is_sealed=True and found=True)
    if not sealed_state.get("is_sealed") or not sealed_state.get("found"):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot generate Title Attestation Certificate for parcel {ulpin}: "
                f"Parcel is unsealed (presumptive record only). "
                f"Sealing on Curtain Ledger (Mirror Score >= 85) is required before a conclusive title certificate can be issued."
            ),
        )

    pdf_buffer = generate_title_certificate(p, sealed_state)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="BhoomiSetu_TitleCertificate_{ulpin}.pdf"',
            "X-Honesty-Label": "Prototype certificate - not a legally issued government document.",
        },
    )


@app.get("/parcels/{ulpin}/mirror-score", tags=["mirror"])
def get_mirror_score(ulpin: str) -> dict:
    """
    Priority 1b — Mirror Engine: returns confidence score and flags for a single parcel.
    """
    p = _get_parcel_by_ulpin(ulpin)
    if not p:
        raise HTTPException(status_code=404, detail=f"Parcel {ulpin} not found")
    engine = get_engine()
    result = engine.score_parcel(p)
    return {
        "status": "Working Prototype",
        "result": result.to_dict(),
    }


@app.post("/parcels/batch-score", tags=["mirror"])
def batch_score() -> dict:
    """
    Priority 1b — Scores the entire dataset at once.
    Re-builds the cross-parcel index before scoring to catch duplicate claims.
    """
    parcels = _load_all_parcels()
    engine = get_engine()
    engine.build_index(parcels)
    summary = engine.score_all(parcels)
    return {
        "status": "Working Prototype",
        "summary": {k: v for k, v in summary.items() if k != "results"},
        "results": summary["results"],
    }


                                                                             
                                        
                                                                             
@app.post("/seal/{ulpin}", tags=["curtain"])
@limiter.limit("30/minute")
def seal_parcel(
    ulpin: str,
    seal_data: SealRequest,
    request: Request,
    current_user: dict = Depends(require_role(["registrar"])),
) -> dict:
    """
    Priority 1c — Curtain Ledger: seals a parcel on-chain if Mirror Score ≥ threshold.
    Also pays the risk-indexed Assurance Pool premium (Priority 2a).

    Only the current validated state (owner hash + score + CID) is written on-chain.
    Full historical record is stored in the off-chain store (IPFS-equivalent).
    """
    p = _get_parcel_by_ulpin(ulpin)
    if not p:
        raise HTTPException(status_code=404, detail=f"Parcel {ulpin} not found")
    if p.get("schema_type") == "community":
        raise HTTPException(
            status_code=400,
            detail="Community parcels are sealed via the CommunityTenure contract, not CurtainLedger.",
        )

    engine = get_engine()
    score_result = engine.score_parcel(p)

    threshold = MirrorConfig().sealing_threshold
    effective_score = seal_data.override_score if seal_data.override_score is not None else score_result.mirror_score

    if effective_score < threshold:
        return {
            "sealed": False,
            "reason": f"Mirror Score {effective_score} is below sealing threshold {threshold}. Flags: {score_result.flags}",
            "mirror_result": score_result.to_dict(),
            "threshold": threshold,
        }

    store = get_store()
    cid = store.put(p)

    owner_hash = p["owners"][0]["id_hash"] if p.get("owners") else "community"

    bridge = get_bridge()
    seal_result = bridge.seal_parcel(
        ulpin=ulpin,
        owner_id_hash=owner_hash,
        mirror_score=effective_score,
        off_chain_cid=cid,
        declared_value=seal_data.declared_value_inr,
    )

    # Idempotent seal: if contract rejected because parcel is already sealed,
    # read back the existing state and return it as a success. This prevents
    # demo failures if /seal is called twice (e.g. on page reload or during testing).
    if not seal_result.get("success") and "already sealed" in str(seal_result.get("error", "")):
        existing = bridge.get_sealed_state(ulpin)
        if existing.get("is_sealed") or existing.get("found"):
            return {
                "sealed": True,
                "ulpin": ulpin,
                "score_used": existing.get("mirror_score", effective_score),
                "off_chain_cid": existing.get("off_chain_cid", cid),
                "on_chain": {**existing, "success": True, "note": "Already sealed — existing state returned"},
                "override_applied": seal_data.override_score is not None,
                "status_label": "Working Prototype",
            }

    return {
        "sealed": seal_result.get("success", False),
        "ulpin": ulpin,
        "score_used": effective_score,
        "off_chain_cid": cid,
        "on_chain": seal_result,
        "override_applied": seal_data.override_score is not None,
        "status_label": "Working Prototype",
    }


@app.get("/sealed/{ulpin}", tags=["curtain"])
def get_sealed_state(ulpin: str) -> dict:
    """
    Priority 1c — Returns current on-chain state (Curtain principle).
    Bank view calls this — sees sealed/not-sealed without full ownership history.
    """
    bridge = get_bridge()
    state = bridge.get_sealed_state(ulpin)
    return {
        "status_label": "Working Prototype",
        "curtain_principle_note": (
            "This endpoint implements the Curtain principle: callers see only "
            "the current verified state, not the full historical chain of title."
        ),
        **state,
    }


@app.post("/mutate/{ulpin}", tags=["curtain"])
def mutate_parcel(
    ulpin: str,
    request: MutateRequest,
    current_user: dict = Depends(require_role(["registrar"])),
) -> dict:
    """
    Priority 1c — Records a transfer/mutation. Re-runs Mirror Engine before updating seal.
    Any ownership change requires a fresh verification score above threshold.
    """
    p = _get_parcel_by_ulpin(ulpin)
    if not p:
        raise HTTPException(status_code=404, detail=f"Parcel {ulpin} not found")

                                                                                      
    engine = get_engine()
    new_score = engine.score_parcel(p)

    threshold = MirrorConfig().sealing_threshold
    if new_score.mirror_score < threshold:
        return {
            "mutated": False,
            "reason": f"Re-verification score {new_score.mirror_score} below threshold {threshold}",
            "mirror_result": new_score.to_dict(),
        }

    store = get_store()
    updated_parcel = {**p, "owners": [{"name": request.new_owner_name, "id_hash": request.new_owner_id_hash, "share_fraction": 1.0}]}
    new_cid = store.put(updated_parcel)

    bridge = get_bridge()
    result = bridge.mutate_parcel(
        ulpin, request.new_owner_id_hash,
        new_score.mirror_score, new_cid, request.declared_value_inr
    )
    return {"mutated": True, "on_chain": result, "new_off_chain_cid": new_cid}


                                                                             
                                        
                                                                             
@app.get("/pool/balance", tags=["assurance"])
def pool_balance() -> dict:
    """Priority 2a — Returns current pool balance."""
    bridge = get_bridge()
    return {
        "status_label": "Working Prototype",
        "pool_note": "Prototype self-funding assurance mechanism — not a legally binding insurance product.",
        **bridge.get_pool_balance(),
    }


@app.post("/pool/claim/{ulpin}", tags=["assurance"])
def file_claim(
    ulpin: str,
    request: ClaimRequest,
    current_user: dict = Depends(require_role(["registrar"])),
) -> dict:
    """
    Priority 2a — Admin/oracle triggers a payout from the Assurance Pool.
    In production: this would be triggered by a court/tribunal attestation oracle.
    For the prototype: manually triggerable by the admin account.
    """
    bridge = get_bridge()
    result = bridge.file_claim(ulpin, request.claimant_address)
    return {
        "status_label": "Working Prototype",
        "oracle_note": (
            "In production, this trigger would come from a certified court/tribunal oracle. "
            "For this prototype it is manually triggered by the admin account. "
            "This is a prototype self-funding mechanism — not a legally binding payout."
        ),
        **result,
    }


@app.get("/pool/premium-preview/{ulpin}", tags=["assurance"])
def preview_premium(ulpin: str, declared_value: float = Query(..., gt=0)) -> dict:
    """
    Priority 2a — Previews the risk-indexed premium for a parcel before sealing.
    Shows the formula calculation transparently.
    """
    p = _get_parcel_by_ulpin(ulpin)
    if not p:
        raise HTTPException(status_code=404, detail=f"Parcel {ulpin} not found")
    engine = get_engine()
    score_result = engine.score_parcel(p)

                                                 
    bridge = get_bridge()
    premium_info = bridge._get_premium_info(ulpin, score_result.mirror_score, declared_value)
    return {
        "ulpin": ulpin,
        "mirror_score": score_result.mirror_score,
        "premium_preview": premium_info,
        "status_label": "Working Prototype",
    }


                                                                             
                                          
                                                                             
@app.get("/community/info", tags=["community"])
def community_info() -> dict:
    """Priority 2b — Returns Dongri Pahad community data including members and voting history."""
    data = _load_community_data()
    engine = get_engine()
    gini_result = engine.compute_community_gini(
        data.get("voting_history", []),
        data.get("registered_members", []),
    )
    return {
        "status_label": "Working Prototype",
        "village": data.get("village_name"),
        "community_entity": "Dongri Pahad Gram Sabha",
        "member_count": len(data.get("registered_members", [])),
        "registered_members": data.get("registered_members", []),
        "voting_history_count": len(data.get("voting_history", [])),
        "voting_history": data.get("voting_history", []),
        "governance_health": gini_result,
        "elite_capture_note": (
            "Elite-Capture Detection uses the Gini coefficient over voting participation. "
            "G=0 is perfect equality; G=1 is total concentration. "
            "Formula: G = (2×Σ(i·x_i))/(n·Σx_i) − (n+1)/n"
        ),
    }


@app.get("/community/gini", tags=["community"])
def community_gini() -> dict:
    """Priority 2b — Returns current Gini coefficient and governance health status."""
    data = _load_community_data()
    engine = get_engine()
    result = engine.compute_community_gini(
        data.get("voting_history", []),
        data.get("registered_members", []),
    )
    return {"status_label": "Working Prototype", **result}


@app.post("/community/propose", tags=["community"])
def propose_action(
    request: ProposeActionRequest,
    current_user: dict = Depends(require_role(["community_member"])),
) -> dict:
    """Priority 2b — Proposes a new action for community multi-sig vote."""
    bridge = get_bridge()
    result = bridge.propose_community_action(request.description)
    return {"status_label": "Working Prototype", **result}


@app.post("/community/vote", tags=["community"])
def cast_votes(
    request: VoteRequest,
    current_user: dict = Depends(require_role(["community_member"])),
) -> dict:
    """
    Priority 2b — Cast votes (online or offline batch simulation).
    If offline_batch=True, simulates the offline vote collection flow.
    """
    bridge = get_bridge()
    if request.offline_batch:
        result = bridge.submit_offline_batch(request.action_id, request.member_indices)
    else:
        results = [
            bridge.sign_community_action(request.action_id, idx)
            for idx in request.member_indices
        ]
        result = {"success": all(r["success"] for r in results), "individual_results": results}
    return {"status_label": "Working Prototype", **result}


                                                                             
                   
                                                                             
@app.get("/villages/", tags=["parcels"])
def list_villages() -> dict:
    parcels = _load_all_parcels()
    village_map: dict[str, dict] = {}
    for p in parcels:
        v = p.get("village", "Unknown")
        if v not in village_map:
            village_map[v] = {
                "name": v,
                "district": p.get("district"),
                "state": p.get("state"),
                "schema_type": p.get("schema_type", "individual"),
                "parcel_count": 0,
            }
        village_map[v]["parcel_count"] += 1
    return {"villages": list(village_map.values())}


# ===========================================================================
# Tier 2b — Citizen-Initiated Dispute / Grievance Filing
# ===========================================================================

DISPUTES_FILE = DATA_DIR / "disputes.json"


def _load_disputes() -> list[dict]:
    if DISPUTES_FILE.exists():
        try:
            return json.loads(DISPUTES_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_disputes(disputes: list[dict]):
    DISPUTES_FILE.write_text(json.dumps(disputes, indent=2, ensure_ascii=False), encoding="utf-8")


@app.post("/disputes/file", tags=["disputes"])
def file_dispute(
    request: DisputeFilingRequest,
    current_user: dict = Depends(require_role(["citizen", "registrar"])),
) -> dict:
    """
    Tier 2b — Citizen-initiated dispute and grievance filing.
    Persists dispute records off-chain with a unique tracking identifier.
    RBAC: Requires authenticated 'citizen' or 'registrar' role to prevent spam filings.
    Honesty Label: Working Prototype (Off-Chain Grievance Storage).
    """
    p = _get_parcel_by_ulpin(request.ulpin)
    if not p:
        raise HTTPException(status_code=404, detail=f"Parcel {request.ulpin} not found in cadastral registry.")

    disputes = _load_disputes()
    dispute_num = len(disputes) + 1
    dispute_id = f"DSP-2026-{dispute_num:04d}"

    complainant = request.complainant_name
    if current_user and current_user.get("display_name"):
        complainant = current_user.get("display_name")

    record = {
        "dispute_id": dispute_id,
        "ulpin": request.ulpin,
        "complainant_name": complainant,
        "contact_info": request.contact_info or "Registered Citizen Portal User",
        "dispute_type": request.dispute_type,
        "description": request.description,
        "evidence_summary": request.evidence_summary or "Submitted via Citizen Grievance Portal.",
        "filed_at": datetime.now(timezone.utc).isoformat(),
        "status": "OPEN",
        "assigned_to": f"Sub-Registrar ({p.get('district', 'District')} Jurisdiction)",
    }
    disputes.append(record)
    _save_disputes(disputes)

    return {
        "status": "success",
        "dispute_id": dispute_id,
        "ulpin": request.ulpin,
        "dispute": record,
        "honesty_label": "Working Prototype — Off-Chain Grievance Storage",
    }


@app.get("/disputes/", tags=["disputes"])
def list_disputes(
    ulpin: str | None = Query(None, description="Filter disputes by ULPIN"),
    status: str | None = Query(None, description="Filter by status (OPEN, UNDER_INQUIRY, RESOLVED)"),
    current_user: dict | None = Depends(get_current_user_optional),
) -> dict:
    """
    Tier 2b — Lists all registered land disputes for Sub-Registrar review.
    Privacy Scoping: Citizen contact details (phone/email) are redacted unless authenticated as registrar.
    """
    disputes = _load_disputes()
    if ulpin:
        disputes = [d for d in disputes if d.get("ulpin") == ulpin]
    if status:
        disputes = [d for d in disputes if d.get("status") == status]

    is_registrar = current_user and current_user.get("role") == "registrar"

    sanitized_disputes = []
    for d in disputes:
        d_copy = dict(d)
        if not is_registrar:
            d_copy["contact_info"] = "[Restricted - Sub-Registrar Access Only]"
        sanitized_disputes.append(d_copy)

    return {
        "total_disputes": len(sanitized_disputes),
        "disputes": sanitized_disputes,
        "honesty_label": "Working Prototype — Off-Chain Grievance Storage",
    }



@app.post("/disputes/{dispute_id}/resolve", tags=["disputes"])
def resolve_dispute(
    dispute_id: str,
    request: DisputeResolutionRequest,
    current_user: dict = Depends(require_role(["registrar"])),
) -> dict:
    """Tier 2b — Sub-Registrar updates or adjudicates grievance inquiry status."""
    disputes = _load_disputes()
    target = next((d for d in disputes if d.get("dispute_id") == dispute_id), None)
    if not target:
        raise HTTPException(status_code=404, detail=f"Dispute {dispute_id} not found.")

    target["status"] = request.status
    target["resolution_notes"] = request.resolution_notes
    target["resolved_by"] = current_user.get("display_name", "Sub-Registrar")
    target["resolved_at"] = datetime.now(timezone.utc).isoformat()
    _save_disputes(disputes)

    return {
        "status": "success",
        "dispute_id": dispute_id,
        "updated_dispute": target,
        "honesty_label": "Working Prototype",
    }


# ===========================================================================
# Tier 3a — Citizen-Initiated Mutation Requests
# ===========================================================================

MUTATIONS_FILE = DATA_DIR / "mutation_requests.json"


def _load_mutation_requests() -> list[dict]:
    if MUTATIONS_FILE.exists():
        try:
            return json.loads(MUTATIONS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_mutation_requests(requests: list[dict]):
    MUTATIONS_FILE.write_text(json.dumps(requests, indent=2, ensure_ascii=False), encoding="utf-8")


@app.post("/mutation-requests/", tags=["mutations"])
def create_mutation_request(
    request: MutationFilingRequest,
    current_user: dict = Depends(require_role(["citizen", "registrar"])),
) -> dict:
    """
    Tier 3a — Citizen-initiated mutation / land title transfer request.
    Queues mutation application for Sub-Registrar review with deed reference.
    Honesty Label: Working Prototype (Off-Chain Queue).
    """
    p = _get_parcel_by_ulpin(request.ulpin)
    if not p:
        raise HTTPException(status_code=404, detail=f"Parcel {request.ulpin} not found in cadastral registry.")

    requests = _load_mutation_requests()
    req_num = len(requests) + 1
    req_id = f"MUT-2026-{req_num:04d}"

    applicant = request.applicant_name
    if current_user and current_user.get("display_name"):
        applicant = current_user.get("display_name")

    record = {
        "request_id": req_id,
        "ulpin": request.ulpin,
        "applicant_name": applicant,
        "mutation_type": request.mutation_type,
        "new_owner_name": request.new_owner_name,
        "new_owner_id_hash": request.new_owner_id_hash,
        "declared_value_inr": request.declared_value_inr,
        "deed_reference": request.deed_reference,
        "proposed_area_ha": request.proposed_area_ha,
        "filed_at": datetime.now(timezone.utc).isoformat(),
        "status": "PENDING",
        "rejection_reason": None,
        "mirror_verification": None,
        "tx_hash": None,
    }
    requests.append(record)
    _save_mutation_requests(requests)

    return {
        "status": "success",
        "request_id": req_id,
        "mutation_request": record,
        "honesty_label": "Working Prototype",
    }


@app.get("/mutation-requests/", tags=["mutations"])
def list_mutation_requests(
    ulpin: str | None = Query(None, description="Filter by ULPIN"),
    status: str | None = Query(None, description="Filter by status (PENDING, APPROVED_AND_SEALED, REJECTED)"),
) -> dict:
    """Tier 3a — Lists queued mutation requests for Sub-Registrar review."""
    requests = _load_mutation_requests()
    if ulpin:
        requests = [r for r in requests if r.get("ulpin") == ulpin]
    if status:
        requests = [r for r in requests if r.get("status") == status]
    return {
        "total_requests": len(requests),
        "requests": requests,
        "honesty_label": "Working Prototype",
    }


@app.post("/mutation-requests/{request_id}/approve", tags=["mutations"])
def approve_mutation_request(
    request_id: str,
    current_user: dict = Depends(require_role(["registrar"])),
) -> dict:
    """
    Tier 3a — Sub-Registrar approves & seals a citizen mutation request.
    CRITICAL: Re-invokes Mirror Engine scoring on mutated parcel representation
    BEFORE calling CurtainLedger.sol. Rejects if score < 85 or flags prevent sealing.
    """
    requests = _load_mutation_requests()
    target = next((r for r in requests if r.get("request_id") == request_id), None)
    if not target:
        raise HTTPException(status_code=404, detail=f"Mutation request {request_id} not found.")

    if target.get("status") != "PENDING":
        raise HTTPException(
            status_code=400,
            detail=f"Mutation request {request_id} is already processed with status '{target.get('status')}'.",
        )

    p = _get_parcel_by_ulpin(target["ulpin"])
    if not p:
        raise HTTPException(status_code=404, detail=f"Parcel {target['ulpin']} not found.")

    simulated_parcel = dict(p)
    if target.get("proposed_area_ha") is not None:
        simulated_parcel["area_textual"] = target["proposed_area_ha"]
        simulated_parcel["area_unit"] = "hectares"
        simulated_parcel["ror_text"] = f"area: {target['proposed_area_ha']} hectares"

    current_mutations = list(simulated_parcel.get("mutation_history") or [])
    current_mutations.append({
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "event_type": target["mutation_type"],
        "from_owner": simulated_parcel.get("owners", [{}])[0].get("name", "Previous Owner"),
        "to_owner": target["new_owner_name"],
        "remarks": f"Deed Ref: {target['deed_reference']}",
    })
    simulated_parcel["mutation_history"] = current_mutations
    simulated_parcel["owners"] = [{
        "name": target["new_owner_name"],
        "id_hash": target["new_owner_id_hash"],
        "share": 1.0,
    }]

    # Re-invoke Mirror Engine scoring
    engine = get_engine()
    score_result = engine.score_parcel(simulated_parcel)

    threshold = MirrorConfig().sealing_threshold
    if score_result.mirror_score < threshold or not score_result.sealing_eligible:
        reason = (
            f"Mirror Engine re-verification failed: score {score_result.mirror_score}/100 "
            f"below {threshold} threshold. Flags: {', '.join(score_result.flags)}. "
            f"Curtain Ledger mutation seal blocked."
        )
        target["status"] = "REJECTED"
        target["rejection_reason"] = reason
        target["mirror_verification"] = score_result.to_dict()
        _save_mutation_requests(requests)
        raise HTTPException(status_code=422, detail=reason)

    store = get_store()
    new_cid = store.put(simulated_parcel)

    bridge = get_bridge()

    # STATE SYNC FIX: proposeMutation() on CurtainLedger requires the parcel to
    # already be sealed (sp.isSealed == true). After a fresh Hardhat start, a parcel
    # that was sealed in a previous session is gone from contract state — so we must
    # re-seal it first before mutating. Check current on-chain state and seal if needed.
    existing_state = bridge.get_sealed_state(target["ulpin"])
    if not existing_state.get("is_sealed") or not existing_state.get("found"):
        # Parcel not yet sealed on-chain in this session — seal it first using
        # the original parcel owner so the chain-of-trust is complete.
        original_owner_hash = p["owners"][0]["id_hash"] if p.get("owners") else "initial_owner"
        original_cid = store.put(p)
        bridge.seal_parcel(
            ulpin=target["ulpin"],
            owner_id_hash=original_owner_hash,
            mirror_score=score_result.mirror_score,
            off_chain_cid=original_cid,
            declared_value=p.get("declared_value_inr", 0.0),
        )

    result = bridge.mutate_parcel(
        target["ulpin"],
        target["new_owner_id_hash"],
        score_result.mirror_score,
        new_cid,
        target["declared_value_inr"],
    )

    target["status"] = "APPROVED_AND_SEALED"
    target["mirror_verification"] = score_result.to_dict()
    target["new_cid"] = new_cid
    target["tx_hash"] = result.get("tx_hash") if isinstance(result, dict) else "0xSimulated"
    target["approved_by"] = current_user.get("display_name", "Sub-Registrar")
    target["approved_at"] = datetime.now(timezone.utc).isoformat()
    _save_mutation_requests(requests)

    return {
        "status": "success",
        "request_id": request_id,
        "ulpin": target["ulpin"],
        "mirror_score": score_result.mirror_score,
        "on_chain": result,
        "mutation_request": target,
        "honesty_label": "Working Prototype",
    }




                                                                             
                                                         
                                                                             
@app.get("/gnn/risk/{ulpin}", tags=["gnn"])
def get_dispute_risk(ulpin: str) -> dict:
    """
    Priority 4a — Dispute-Risk GNN Pipeline Demo.
    Label: Prototype pipeline — trained on synthetic data, not a validated real-world accuracy result.
    """
    from gnn_model import get_gnn
    p = _get_parcel_by_ulpin(ulpin)
    if not p:
        raise HTTPException(status_code=404, detail=f"Parcel {ulpin} not found")
    engine = get_engine()
    score_result = engine.score_parcel(p)
    gnn = get_gnn()
    risk_info = gnn.predict_dispute_risk(p, score_result.mirror_score)
    return {
        "status_label": "Architecture Demo",
        **risk_info,
    }


@app.get("/gnn/graph-summary", tags=["gnn"])
def get_graph_summary() -> dict:
    """Priority 4a — Graph topology metrics across the synthetic dataset."""
    from gnn_model import get_gnn
    parcels = _load_all_parcels()
    gnn = get_gnn()
    return {
        "status_label": "Architecture Demo",
        **gnn.build_graph_summary(parcels),
    }


@app.get("/harmonize/demo", tags=["harmonize"])
def get_harmonize_demo() -> dict:
    from schema_harmonizer import run_demo
    return {
        "status_label": "Architecture Demo (Proof of Concept)",
        "demonstration_records": run_demo(),
        "disclaimer": "Proof-of-concept demonstration across 3 mock state formats only.",
    }


@app.get("/shapefile/status", tags=["shapefile"])
def get_shapefile_status() -> dict:
    try:
        from shapefile_ingest import is_shapefile_support_available
        available = is_shapefile_support_available()
    except Exception:
        available = False
    return {
        "status_label": "Architecture Demo (Extended Capability)",
        "available": available,
        "engine": "GeoPandas / pyogrio (GDAL)" if available else "Unavailable",
        "sample_shapefile_path": "data/mock_gov_export/svamitva_drone_survey_parcels.shp",
    }


@app.get("/shapefile/import-sample", tags=["shapefile"])
def import_sample_shapefile() -> dict:
    try:
        from shapefile_ingest import ingest_shapefile, is_shapefile_support_available
        if not is_shapefile_support_available():
            return {
                "success": False,
                "status_label": "Architecture Demo (Extended Capability)",
                "status": "unavailable",
                "message": "Extended geospatial capability (GeoPandas/pyogrio) is not installed in the active environment. Install backend/requirements-geo-extended.txt to enable Shapefile ingestion.",
                "parcels": [],
                "count": 0,
            }

        shp_path = Path(__file__).parent.parent / "data" / "mock_gov_export" / "svamitva_drone_survey_parcels.shp"
        if not shp_path.exists():
            import sys
            scripts_dir = Path(__file__).parent.parent / "scripts"
            if str(scripts_dir) not in sys.path:
                sys.path.insert(0, str(scripts_dir))
            from generate_mock_shapefile import generate_mock_shapefile
            generate_mock_shapefile()

        ingest_res = ingest_shapefile(str(shp_path))
        if not ingest_res.get("success"):
            return {
                "status_label": "Architecture Demo (Extended Capability)",
                **ingest_res
            }

        ingested_list = ingest_res.get("parcels", [])
        sandbox_engine = MirrorEngine()
        sandbox_engine.build_index(_load_all_parcels() + ingested_list)

        scored_parcels = []
        for p in ingested_list:
            score_res = sandbox_engine.score_parcel(p)
            p_scored = {**p, "mirror_result": score_res.to_dict()}
            scored_parcels.append(p_scored)

        return {
            "status_label": "Architecture Demo (Extended Capability)",
            "success": True,
            "count": len(scored_parcels),
            "source_format": "Government Esri Shapefile (.shp/.dbf/.shx/SVAMITVA)",
            "message": f"Successfully ingested and Mirror-scored {len(scored_parcels)} parcels from SVAMITVA Shapefile export.",
            "parcels": scored_parcels,
        }
    except Exception as e:
        return {
            "status_label": "Architecture Demo (Extended Capability)",
            "success": False,
            "status": "error",
            "message": f"Error during Shapefile ingestion: {str(e)}",
            "parcels": [],
            "count": 0,
        }


