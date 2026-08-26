import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def get_dashboard_metrics():
    res = client.get("/parcels/?limit=500")
    parcels = res.json().get("parcels", [])
    total = len(parcels)
    sealing_ready_clean = sum(
        1 for p in parcels
        if p.get("mirror_result", {}).get("sealing_eligible") and len(p.get("mirror_result", {}).get("flags", [])) == 0
    )
    sealing_ready_flags = sum(
        1 for p in parcels
        if p.get("mirror_result", {}).get("sealing_eligible") and len(p.get("mirror_result", {}).get("flags", [])) > 0
    )
    unsealed_flagged = sum(
        1 for p in parcels
        if not p.get("mirror_result", {}).get("sealing_eligible") and len(p.get("mirror_result", {}).get("flags", [])) > 0
    )
    community_fra = sum(1 for p in parcels if p.get("schema_type") == "community")
    total_flagged = sum(1 for p in parcels if len(p.get("mirror_result", {}).get("flags", [])) > 0)
    return {
        "total_parcels": total,
        "sealing_ready_clean": sealing_ready_clean,
        "sealing_ready_flags": sealing_ready_flags,
        "unsealed_flagged": unsealed_flagged,
        "community_fra": community_fra,
        "total_flagged": total_flagged,
        "sum_check": sealing_ready_clean + sealing_ready_flags + unsealed_flagged + community_fra,
    }


def main():
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=== BEFORE SHAPEFILE IMPORT ===")
    before = get_dashboard_metrics()
    for k, v in before.items():
        print(f"  {k:22}: {v}")

    print("\n>>> EXECUTING SHAPEFILE INGESTION ENDPOINT (/shapefile/import-sample) <<<")
    shp_res = client.get("/shapefile/import-sample")
    shp_data = shp_res.json()
    print(f"Shapefile Import Success: {shp_data.get('success')}, Count: {shp_data.get('count')}")

    print("\n=== AFTER SHAPEFILE IMPORT ===")
    after = get_dashboard_metrics()
    for k, v in after.items():
        print(f"  {k:22}: {v}")

    print("\n=== SIDE-BY-SIDE ISOLATION VERIFICATION ===")
    print(f"{'Metric':<24} | {'Before':<8} | {'After':<8} | {'Status'}")
    print("-" * 55)
    for k in before:
        match = before[k] == after[k]
        status_str = "MATCH (Identical)" if match else "CHANGED (Polluted)"
        print(f"{k:<24} | {before[k]:<8} | {after[k]:<8} | {status_str}")

    assert before == after, "Isolation failed: Dashboard dataset was mutated by shapefile import!"
    print("\n✅ VERIFIED: Primary dataset is 100% isolated. Zero mutations observed.")


if __name__ == "__main__":
    main()
