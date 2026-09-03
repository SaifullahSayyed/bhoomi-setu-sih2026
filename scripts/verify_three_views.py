import sys, os
sys.path.insert(0, "backend")
os.chdir("backend")
from fastapi.testclient import TestClient
from main import app
client = TestClient(app)
ULPIN = "UP231000000001"

reg_token = client.post("/auth/login", json={"role": "registrar"}).json()["access_token"]
seal_res = client.post("/seal/"+ULPIN, json={"declared_value_inr": 1725435.93}, headers={"Authorization": "Bearer "+reg_token})
s = seal_res.json()
print("[SEAL]    status="+str(seal_res.status_code)+" sealed="+str(s.get("sealed"))+" score="+str(s.get("score_used")))

cit_token = client.post("/auth/login", json={"role": "citizen"}).json()["access_token"]
mut_body = {"ulpin": ULPIN, "mutation_type": "sale", "new_owner_name": "Priya Dubey", "new_owner_id_hash": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2", "declared_value_inr": 1850000.0, "deed_reference": "REG-SALE-2026/8942", "proposed_area_ha": 1.5104}
mut_res = client.post("/mutation-requests/", json=mut_body, headers={"Authorization": "Bearer "+cit_token})
req_id = mut_res.json().get("request_id")
print("[FILE]    status="+str(mut_res.status_code)+" request_id="+str(req_id))

approve_res = client.post("/mutation-requests/"+req_id+"/approve", headers={"Authorization": "Bearer "+reg_token})
ar = approve_res.json()
mut_status = ar.get("mutation_request", {}).get("status", "UNKNOWN")
print("[APPROVE] status="+str(approve_res.status_code)+" mut_status="+mut_status)

print()
print("=== THREE-VIEW CONSISTENCY CHECK ===")

mut_list = client.get("/mutation-requests/?ulpin="+ULPIN).json()
latest = next((r for r in mut_list["requests"] if r["request_id"] == req_id), {})
v1 = latest.get("status", "MISSING")
print("[VIEW 1 - Mutations Tab]       status="+v1)

on_chain = client.get("/parcels/"+ULPIN).json().get("on_chain_state", {})
print("[VIEW 2 - Citizen Land Status] found="+str(on_chain.get("found"))+" is_sealed="+str(on_chain.get("is_sealed"))+" score="+str(on_chain.get("mirror_score", 0)))

sr = client.get("/sealed/"+ULPIN).json()
print("[VIEW 3 - Bank Collateral]     found="+str(sr.get("found"))+" is_sealed="+str(sr.get("is_sealed"))+" score="+str(sr.get("mirror_score", 0)))

ok = v1=="APPROVED_AND_SEALED" and on_chain.get("found") and on_chain.get("is_sealed") and sr.get("found") and sr.get("is_sealed")
print()
print("RESULT: ALL THREE VIEWS AGREE - CONSISTENT SEALED STATE" if ok else "RESULT: MISMATCH DETECTED")
sys.exit(0 if ok else 1)
