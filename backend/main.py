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
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from mirror_engine import MirrorEngine, MirrorConfig, get_engine
from off_chain_store import get_store
from web3_bridge import get_bridge

                                                                             
           
                                                                             
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


                                                                             
                  
                                                                             
@app.get("/parcels/", tags=["parcels"])
def list_parcels(
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
def seal_parcel(ulpin: str, request: SealRequest) -> dict:
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
    effective_score = request.override_score if request.override_score is not None else score_result.mirror_score

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
    declared_value = request.declared_value_inr or p.get("declared_value_inr", 0)

    bridge = get_bridge()
    result = bridge.seal_parcel(ulpin, owner_hash, effective_score, cid, declared_value)

    return {
        "sealed": result.get("success", False),
        "mirror_result": score_result.to_dict(),
        "on_chain": result,
        "off_chain_cid": cid,
        "threshold": threshold,
        "override_applied": request.override_score is not None,
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
def mutate_parcel(ulpin: str, request: MutateRequest) -> dict:
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
def file_claim(ulpin: str, request: ClaimRequest) -> dict:
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
def propose_action(request: ProposeActionRequest) -> dict:
    """Priority 2b — Proposes a new action for community multi-sig vote."""
    bridge = get_bridge()
    result = bridge.propose_community_action(request.description)
    return {"status_label": "Working Prototype", **result}


@app.post("/community/vote", tags=["community"])
def cast_votes(request: VoteRequest) -> dict:
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


