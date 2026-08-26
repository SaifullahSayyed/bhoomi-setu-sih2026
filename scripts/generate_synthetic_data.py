"""
generate_synthetic_data.py — Bhoomi Setu Synthetic Dataset Generator
======================================================================
Priority 1a | Status: Working Prototype

PURPOSE
-------
Generates a realistic mock dataset of ~500 land parcels across three fictional
Indian villages. The dataset is the single source of truth for all other modules
(Mirror Engine, Curtain Ledger, GNN, etc.) and is designed to be *regenerated*
or *extended* — never hardcoded.

THREE VILLAGES
--------------
  A) Rampur Khurd      — Uttar Pradesh style, bigha/biswa units, individual ownership
  B) Vellore Nagar     — Tamil Nadu style, cents/grounds units, individual ownership
  C) Dongri Pahad      — Jharkhand tribal belt, Forest Rights Act community schema
                         (Gram Sabha ownership, NOT individual — distinct data model)

INJECTED ANOMALIES (cross-state diversity simulation)
------------------------------------------------------
  ~15% of parcels: textual RoR area ≠ GeoJSON polygon area (>10% discrepancy)
  ~5%  of parcels: duplicate ULPIN or spatially overlapping coordinates
  ~5   parcels   : benami pattern (owner appears on many high-value parcels vs. stated income)

ULPIN FORMAT (simulated)
------------------------
  14 characters: 2-char state code + 3-char district code + 9-digit sequential ID
  e.g. UP231000000001 — not real ULPINs, clearly labeled as synthetic.

ON-CHAIN PRIVACY NOTE
---------------------
  Owner names are pseudonymised fictional names. ID hashes are SHA-256 of a
  fictional ID string — NOT real Aadhaar numbers. Never use real PII.

USAGE
-----
  python generate_synthetic_data.py [--seed 42] [--village-a 200] [--village-b 200] [--village-c 100]
  Outputs to ../data/ by default.
"""

import argparse
import csv
import hashlib
import json
import math
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

                                                                             
                                     
                                                                           
                                                                           
                                                                             
UNIT_TO_HECTARES: dict[str, float] = {
    "hectares": 1.0,
    "acres": 0.404686,
    "bigha": 0.2529,                                                                
    "biswa": 0.012645,                                 
    "cents": 0.00404686,                         
    "grounds": 0.02230,                                              
    "guntha": 0.01012,                            
    "marla": 0.002529,                                               
}

                                                                             
                       
                                                                             
VILLAGES = {
    "A": {
        "name": "Rampur Khurd",
        "district": "Pratapgarh",
        "state": "Uttar Pradesh",
        "state_code": "UP",
        "district_code": "231",
        "primary_unit": "bigha",
        "secondary_unit": "biswa",
        "lat_center": 25.892,
        "lon_center": 81.981,
        "lang": "hi",
        "record_style": "ror_hindi_template",
        "individual": True,
    },
    "B": {
        "name": "Vellore Nagar",
        "district": "Vellore",
        "state": "Tamil Nadu",
        "state_code": "TN",
        "district_code": "042",
        "primary_unit": "cents",
        "secondary_unit": "grounds",
        "lat_center": 12.916,
        "lon_center": 79.132,
        "lang": "ta",
        "record_style": "ror_english_template",
        "individual": True,
    },
    "C": {
        "name": "Dongri Pahad",
        "district": "Khunti",
        "state": "Jharkhand",
        "state_code": "JH",
        "district_code": "117",
        "primary_unit": "acres",
        "secondary_unit": "acres",
        "lat_center": 23.072,
        "lon_center": 85.278,
        "lang": "hi",
        "record_style": "fra_community_template",
        "individual": False,                                                    
    },
}

                                                                             
                                                             
                                                                             
FIRST_NAMES_HI = ["Ramesh", "Sunita", "Prabha", "Mohan", "Geeta", "Hari", "Kamla",
                   "Vijay", "Savitri", "Ashok", "Pushpa", "Suresh", "Rekha", "Dinesh",
                   "Meena", "Rajesh", "Usha", "Santosh", "Kusum", "Bharat", "Nirmala"]
LAST_NAMES_HI  = ["Yadav", "Gupta", "Tiwari", "Verma", "Mishra", "Singh", "Patel",
                   "Sharma", "Maurya", "Chauhan", "Srivastava", "Pandey", "Dubey"]
FIRST_NAMES_TA = ["Murugan", "Kavitha", "Selvam", "Anitha", "Rajan", "Priya", "Senthil",
                   "Meenakshi", "Arjun", "Vijayalakshmi", "Kumar", "Padmini", "Suresh"]
LAST_NAMES_TA  = ["Pillai", "Nadar", "Gounder", "Mudaliar", "Chettiar", "Naicker",
                   "Rajan", "Iyer", "Iyengar", "Thevar", "Reddy", "Krishnan"]
TRIBAL_NAMES   = ["Birsa", "Sita Munda", "Ratan Oraon", "Mani Soren", "Ganga Mahato",
                   "Phulo Devi", "Jhano Munda", "Arjun Toppo", "Sukri Oraon", "Bandu Soren"]


def _fake_name(village_key: str, rng: random.Random) -> str:
    if village_key == "B":
        return f"{rng.choice(FIRST_NAMES_TA)} {rng.choice(LAST_NAMES_TA)}"
    return f"{rng.choice(FIRST_NAMES_HI)} {rng.choice(LAST_NAMES_HI)}"


def _fake_id_hash(name: str, village: str, seq: int) -> str:
    """
    Standard full SHA-256 hash (64 hex characters) of a synthetic identifier string.
    NEVER stores actual Aadhaar / PAN — only this cryptographic hash is written to records.
    The synthetic ID format: SYNTH-{village}-{seq:06d}-{name} is strictly pseudonymous.
    """
    synthetic_id = f"SYNTH-{village}-{seq:06d}-{name.replace(' ','_')}"
    return hashlib.sha256(synthetic_id.encode()).hexdigest()


                                                                             
                                                      
                                                                             
def _make_polygon(lat: float, lon: float, area_ha: float, rng: random.Random) -> dict:
    """
    Generates a simple rectangular GeoJSON polygon approximating the given area.
    Uses a random orientation offset so parcels don't all align identically.

    1 degree latitude ≈ 111 km → 1 ha ≈ 0.009° latitude side (for a square)
    This is a simplification adequate for prototype spatial checks.
    """
    side_deg_lat = math.sqrt(area_ha / 100) * 0.009                     
    side_deg_lon = side_deg_lat / math.cos(math.radians(lat))

                                                                 
    offset_lat = rng.uniform(-0.08, 0.08)
    offset_lon = rng.uniform(-0.08, 0.08)

                                                          
    jitter_lat = rng.uniform(-0.005, 0.005)
    jitter_lon = rng.uniform(-0.005, 0.005)

    base_lat = lat + offset_lat + jitter_lat
    base_lon = lon + offset_lon + jitter_lon

    coords = [
        [base_lon,                base_lat],
        [base_lon + side_deg_lon, base_lat],
        [base_lon + side_deg_lon, base_lat + side_deg_lat],
        [base_lon,                base_lat + side_deg_lat],
        [base_lon,                base_lat],               
    ]
    return {"type": "Polygon", "coordinates": [coords]}


import pyproj
import shapely.geometry


def _polygon_area_ha(polygon: dict) -> float:
    if not polygon or polygon.get("type") != "Polygon":
        return 0.0
    coords = polygon.get("coordinates", [[]])[0]
    if len(coords) < 4:
        return 0.0
    lons = [c[0] for c in coords]
    avg_lon = sum(lons) / len(lons)
    zone = max(1, min(60, math.floor((avg_lon + 180.0) / 6.0) + 1))
    epsg = f"EPSG:326{zone:02d}"
    try:
        transformer = pyproj.Transformer.from_crs("EPSG:4326", epsg, always_xy=True)
        proj = [transformer.transform(c[0], c[1]) for c in coords]
        return round(shapely.geometry.Polygon(proj).area / 10_000.0, 6)
    except Exception:
        return 0.0           


                                                                             
                                 
                                                                        
                                                                        
                                                                                 
                                                                             
def _ror_text_hindi(owner: str, area: float, unit: str, ulpin: str, encumbrance: str) -> str:
    enc_str = f"ऋण भार: {encumbrance}" if encumbrance else "निर्भार"
    return (
        f"खसरा संख्या / ULPIN: {ulpin} | स्वामी का नाम: {owner} | "
        f"क्षेत्रफल: {area:.3f} {unit} | स्थिति: {enc_str} | "
        f"[OCR-simulated input — prototype scope]"
    )


def _ror_text_english(owner: str, area: float, unit: str, ulpin: str, encumbrance: str) -> str:
    enc_str = f"Encumbrance: {encumbrance}" if encumbrance else "Encumbrance-free"
    return (
        f"Survey No/ULPIN: {ulpin} | Owner: {owner} | "
        f"Extent: {area:.3f} {unit} | {enc_str} | "
        f"[OCR-simulated input — prototype scope]"
    )


def _ror_text_fra(community: str, area: float, claim_type: str, ulpin: str) -> str:
    return (
        f"ULPIN: {ulpin} | Community Entity: {community} | "
        f"FRA Claim Type: {claim_type} | Area: {area:.3f} acres | "
        f"[OCR-simulated input — community forest record — prototype scope]"
    )


                                                                             
                            
                                                                             
_MUTATION_TYPES = ["inheritance", "sale", "gift_deed", "court_decree", "partition"]


def _gen_mutation_history(rng: random.Random, owner: str, num_events: int) -> list[dict]:
    history = []
    base_date = datetime(2000, 1, 1)
    prev_owner = _fake_name("A", rng)                         
    for i in range(num_events):
        days_offset = rng.randint(i * 180, (i + 1) * 365)
        event_date = base_date + timedelta(days=days_offset)
        new_owner = owner if i == num_events - 1 else _fake_name("A", rng)
        history.append({
            "seq": i + 1,
            "date": event_date.strftime("%Y-%m-%d"),
            "event_type": rng.choice(_MUTATION_TYPES),
            "from_owner": prev_owner,
            "to_owner": new_owner,
            "remarks": f"Mutation entry {i+1}. Registered at sub-registrar office.",
        })
        prev_owner = new_owner
    return history


                                                                             
                             
                                                                             
def _gen_individual_parcel(
    seq: int,
    village_key: str,
    vcfg: dict,
    rng: random.Random,
    anomalies: dict,
) -> dict:
    ulpin = f"{vcfg['state_code']}{vcfg['district_code']}{seq:09d}"
    unit = vcfg["primary_unit"]

                                                   
    if rng.random() < 0.10:
        owner_names = [_fake_name(village_key, rng), _fake_name(village_key, rng)]
        shares = [round(rng.uniform(0.3, 0.7), 2)]
        shares.append(round(1.0 - shares[0], 2))
    else:
        owner_names = [_fake_name(village_key, rng)]
        shares = [1.0]

    owners = [
        {
            "name": n,
            "share_fraction": s,
            "id_hash": _fake_id_hash(n, village_key, seq + i * 1000),
        }
        for i, (n, s) in enumerate(zip(owner_names, shares))
    ]
    primary_owner = owner_names[0]

                                                        
    if unit == "bigha":
        area_base = rng.uniform(0.5, 8.0)
    elif unit == "cents":
        area_base = rng.uniform(10.0, 500.0)
    else:         
        area_base = rng.uniform(0.25, 5.0)

    area_ha_true = area_base * UNIT_TO_HECTARES[unit]

                                    
                                                                             
                                                                                  
                                                        
    textual_area = area_base
    if seq in anomalies.get("area_mismatch_seqs", set()):
        mismatch_pct = rng.uniform(0.12, 0.35)                                         
        direction = rng.choice([-1, 1])
        textual_area = area_base * (1 + direction * mismatch_pct)

                                     
    declared_value = round(area_ha_true * rng.uniform(800_000, 2_500_000), 2)        
    income_stated = 0.0
    if seq in anomalies.get("benami_seqs", set()):
                                                                                        
        owners[0]["id_hash"] = anomalies["benami_owner_hash"]
        income_stated = rng.uniform(50_000, 150_000)                              
    else:
        income_stated = rng.uniform(100_000, 2_000_000)

                              
    if rng.random() < 0.20:
        creditor = f"{rng.choice(['SBI','PNB','UCO','Gramin Bank'])} Branch {rng.randint(100,999)}"
        enc_amount = round(declared_value * rng.uniform(0.3, 0.7), 2)
        encumbrance = {"mortgaged": True, "creditor": creditor, "amount_inr": enc_amount}
        enc_str = f"{creditor}, ₹{enc_amount:,.0f}"
    else:
        encumbrance = {"mortgaged": False, "creditor": None, "amount_inr": 0}
        enc_str = ""

                                   
    num_mutations = rng.randint(0, 4)
    mutation_history = _gen_mutation_history(rng, primary_owner, num_mutations)

                                                                              
    geometry = _make_polygon(vcfg["lat_center"], vcfg["lon_center"], area_ha_true, rng)

                                                                  
    if vcfg["record_style"] == "ror_english_template":
        ror_text = _ror_text_english(primary_owner, textual_area, unit, ulpin, enc_str)
    else:
        ror_text = _ror_text_hindi(primary_owner, textual_area, unit, ulpin, enc_str)

    return {
        "ulpin": ulpin,
        "village": vcfg["name"],
        "district": vcfg["district"],
        "state": vcfg["state"],
        "village_key": village_key,
        "schema_type": "individual",
        "owners": owners,
        "area_textual": round(textual_area, 4),
        "area_unit": unit,
        "area_ha_textual": round(textual_area * UNIT_TO_HECTARES[unit], 6),
        "ror_text": ror_text,
        "geometry": geometry,
        "mutation_history": mutation_history,
        "encumbrance": encumbrance,
        "declared_value_inr": declared_value,
        "income_stated_inr": income_stated,
        "anomaly_flags_injected": {                                           
            "area_mismatch": seq in anomalies.get("area_mismatch_seqs", set()),
            "duplicate_claim": seq in anomalies.get("duplicate_seqs", set()),
            "benami_pattern": seq in anomalies.get("benami_seqs", set()),
        },
    }


                                                                             
                                                           
                                                                          
                                                                     
                                                                             
                                                                           
                                                                        
                                                                             
def _gen_community_parcel(
    seq: int,
    vcfg: dict,
    rng: random.Random,
    registered_members: list[dict],
) -> dict:
    ulpin = f"{vcfg['state_code']}{vcfg['district_code']}{seq:09d}"
    area_acres = rng.uniform(2.0, 40.0)
    area_ha = area_acres * UNIT_TO_HECTARES["acres"]

    claim_types = [
        "Community Forest Resource",
        "Habitat Rights",
        "Nistar Rights",
        "Community Land",
    ]
    claim_type = rng.choice(claim_types)

    geometry = _make_polygon(vcfg["lat_center"], vcfg["lon_center"], area_ha, rng)
    ror_text = _ror_text_fra("Dongri Pahad Gram Sabha", area_acres, claim_type, ulpin)

    resource_types = ["timber", "tendu_leaf", "mahua", "sal_seed", "bamboo", "grazing"]
    resources = rng.sample(resource_types, rng.randint(1, 4))

    return {
        "ulpin": ulpin,
        "village": vcfg["name"],
        "district": vcfg["district"],
        "state": vcfg["state"],
        "village_key": "C",
        "schema_type": "community",                                      
        "community_entity": "Dongri Pahad Gram Sabha",
        "fra_claim_type": claim_type,
        "registered_members": registered_members,                                
        "resource_rights": resources,
        "area_textual": round(area_acres, 4),
        "area_unit": "acres",
        "area_ha_textual": round(area_ha, 6),
        "ror_text": ror_text,
        "geometry": geometry,
        "mutation_history": [],                                                          
        "encumbrance": {"mortgaged": False, "creditor": None, "amount_inr": 0},
        "declared_value_inr": 0,                                          
        "income_stated_inr": 0,
        "anomaly_flags_injected": {"area_mismatch": False, "duplicate_claim": False, "benami_pattern": False},
    }


                                                                             
                                              
                                                                             
def _gen_community_members(n: int, rng: random.Random) -> list[dict]:
    """
    Generates registered Gram Sabha members with mock Ethereum-style addresses.
    These addresses are used in the CommunityTenure.sol multi-sig contract.
    All addresses are clearly fake — 0x followed by sequential hex, not real keys.
    Guarantees unique full names across all member IDs.
    """
    members = []
    first_names = [
        "Birsa", "Jhano", "Sona", "Budhu", "Rani", "Kanu", "Sidho", "Phulo",
        "Somra", "Jura", "Ganga", "Etwa", "Mangra", "Budhni", "Manki", "Ramu",
        "Sanika", "Champa", "Biru", "Devi", "Pandu", "Karmi", "Charan", "Maina"
    ]
    clan_names = ["Munda", "Soren", "Hembrom", "Tudu", "Besra", "Kiskoo", "Marandi", "Baski"]

    unique_names = [f"{f} {c}" for f in first_names for c in clan_names]
    rng.shuffle(unique_names)

    for i in range(n):
        name = unique_names[i] if i < len(unique_names) else f"Member {i+1} Munda"
        addr = f"0x{(0xDEAD0000 + i):040x}"
        members.append({
            "member_id": i + 1,
            "name_pseudonym": name,
            "eth_address": addr,
            "id_hash": _fake_id_hash(name, "C", i),
        })
    return members


def _gen_voting_history(
    members: list[dict],
    n_votes: int,
    rng: random.Random,
) -> list[dict]:
    """
    Generates n_votes synthetic governance votes for Dongri Pahad.
    Intentionally biases participation: the first 3 members always vote (elite
    capture pattern), while later members rarely do. This creates a measurable
    Gini coefficient that the Elite-Capture Detection module will flag.

    Why this design: we need realistic inequality in the voting history, not
    uniform participation, to make the Gini calculation demonstrably useful.
    """
    history = []
    base_date = datetime(2022, 1, 1)
    action_types = [
        "Approve timber extraction contract",
        "Lease grazing rights to farmer cooperative",
        "Approve boundary demarcation",
        "Ratify annual resource-use plan",
        "Authorize FRA claim submission",
        "Approve construction of community hall",
        "Reject external mining proposal",
        "Amend resource-sharing rules",
    ]
    for v in range(n_votes):
        days_offset = v * rng.randint(14, 45)
        vote_date = base_date + timedelta(days=days_offset)
        action = rng.choice(action_types)

                                                                                     
        signers = []
        for m in members:
            idx = m["member_id"] - 1
            if idx < 3:
                prob = 0.95                                          
            elif idx < 6:
                prob = 0.50                 
            else:
                prob = 0.15                                             
            if rng.random() < prob:
                signers.append(m["eth_address"])

        outcome = "passed" if len(signers) >= math.ceil(0.6 * len(members)) else "failed"
        history.append({
            "vote_id": v + 1,
            "date": vote_date.strftime("%Y-%m-%d"),
            "action": action,
            "signers": signers,
            "signer_count": len(signers),
            "total_members": len(members),
            "quorum_required": math.ceil(0.6 * len(members)),
            "outcome": outcome,
        })
    return history


                                                                             
                            
                                                                             
def _inject_duplicates(
    parcels: list[dict],
    dup_seqs: set[int],
    rng: random.Random,
) -> list[dict]:
    """
    For each parcel flagged as a duplicate, copy an existing parcel's ULPIN or
    geometry to create a conflicting claim. Two types:
      - ULPIN collision: same 14-digit ID, different owner
      - Spatial overlap: different ULPIN but same coordinates (cadastral collision)
    """
    if not dup_seqs:
        return parcels

                                                                   
    source_pool = [p for p in parcels if not p["anomaly_flags_injected"]["duplicate_claim"]]
    for p in parcels:
        if not p["anomaly_flags_injected"]["duplicate_claim"]:
            continue
        source = rng.choice(source_pool)
        if rng.random() < 0.5:
                             
            p["ulpin"] = source["ulpin"]
            p["duplicate_type"] = "ulpin_collision"
        else:
                                             
            p["geometry"] = source["geometry"]
            p["duplicate_type"] = "spatial_overlap"
        p.setdefault("duplicate_type", "ulpin_collision")

    return parcels


                                                                             
                
                                                                             
def generate(
    village_counts: dict[str, int],
    seed: int,
    output_dir: Path,
) -> dict[str, Any]:
    rng = random.Random(seed)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_parcels: list[dict] = []
    summary: dict[str, Any] = {"seed": seed, "villages": {}}

    for village_key, count in village_counts.items():
        vcfg = VILLAGES[village_key]
        print(f"  Generating {count} parcels for Village {village_key}: {vcfg['name']} ...")

        if not vcfg["individual"]:
                                                                              
                                              
                                                                              
            n_members = 20
            registered_members = _gen_community_members(n_members, rng)
            voting_history = _gen_voting_history(registered_members, 15, rng)

            parcels: list[dict] = []
            for i in range(count):
                p = _gen_community_parcel(
                    seq=i + 1,
                    vcfg=vcfg,
                    rng=rng,
                    registered_members=registered_members,
                )
                parcels.append(p)

            village_data = {
                "village_key": village_key,
                "village_name": vcfg["name"],
                "schema_type": "community",
                "registered_members": registered_members,
                "voting_history": voting_history,
                "parcels": parcels,
            }
            fname = f"parcels_village_{village_key}_community.json"
            (output_dir / fname).write_text(json.dumps(village_data, indent=2, ensure_ascii=False), encoding="utf-8")

            summary["villages"][village_key] = {
                "name": vcfg["name"],
                "schema_type": "community",
                "parcel_count": count,
                "member_count": n_members,
                "voting_events": 15,
                "file": fname,
            }
            all_parcels.extend(parcels)

        else:
                                                                              
                                                               
                                                                              
            total = count
            n_mismatch = round(total * 0.15)
            n_dup = round(total * 0.05)
            n_benami = 8 if village_key == "A" else 0                                               

                                                         
            all_seqs = list(range(1, total + 1))
            rng.shuffle(all_seqs)
            mismatch_seqs = set(all_seqs[:n_mismatch])
            dup_seqs      = set(all_seqs[n_mismatch:n_mismatch + n_dup])
            benami_seqs   = set(all_seqs[n_mismatch + n_dup:n_mismatch + n_dup + n_benami])

                                                                            
            benami_owner_name = "Balram Sahukar"                             
            benami_owner_hash = _fake_id_hash(benami_owner_name, village_key, 9999)

            anomalies = {
                "area_mismatch_seqs": mismatch_seqs,
                "duplicate_seqs": dup_seqs,
                "benami_seqs": benami_seqs,
                "benami_owner_hash": benami_owner_hash,
            }

            parcels = []
            for i, seq in enumerate(range(1, total + 1)):
                p = _gen_individual_parcel(
                    seq=seq,
                    village_key=village_key,
                    vcfg=vcfg,
                    rng=rng,
                    anomalies=anomalies,
                )
                parcels.append(p)

                                                                             
            parcels = _inject_duplicates(parcels, dup_seqs, rng)

            fname_json = f"parcels_village_{village_key}.json"
            fname_csv  = f"parcels_village_{village_key}.csv"

            village_data = {
                "village_key": village_key,
                "village_name": vcfg["name"],
                "schema_type": "individual",
                "parcels": parcels,
            }
            (output_dir / fname_json).write_text(json.dumps(village_data, indent=2, ensure_ascii=False), encoding="utf-8")

                                                                            
            csv_rows = []
            for p in parcels:
                csv_rows.append({
                    "ulpin": p["ulpin"],
                    "village": p["village"],
                    "owner_primary": p["owners"][0]["name"] if p["owners"] else "",
                    "owner_count": len(p["owners"]),
                    "area_textual": p["area_textual"],
                    "area_unit": p["area_unit"],
                    "area_ha_textual": p["area_ha_textual"],
                    "declared_value_inr": p["declared_value_inr"],
                    "income_stated_inr": p["income_stated_inr"],
                    "mortgaged": p["encumbrance"]["mortgaged"],
                    "mutation_events": len(p["mutation_history"]),
                    "injected_area_mismatch": p["anomaly_flags_injected"]["area_mismatch"],
                    "injected_duplicate": p["anomaly_flags_injected"]["duplicate_claim"],
                    "injected_benami": p["anomaly_flags_injected"]["benami_pattern"],
                })
            with open(output_dir / fname_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
                writer.writeheader()
                writer.writerows(csv_rows)

            summary["villages"][village_key] = {
                "name": vcfg["name"],
                "schema_type": "individual",
                "parcel_count": count,
                "injected_mismatches": n_mismatch,
                "injected_duplicates": n_dup,
                "injected_benami": n_benami,
                "files": [fname_json, fname_csv],
            }
            all_parcels.extend(parcels)

    summary["total_parcels"] = len(all_parcels)

                          
    (output_dir / "dataset_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"\n  Total parcels generated: {summary['total_parcels']}")
    print(f"  Output written to: {output_dir.resolve()}")
    return summary


                                                                             
                
                                                                             
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bhoomi Setu — Synthetic Land Records Dataset Generator"
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--village-a", type=int, default=200, help="Parcels for Rampur Khurd (UP)")
    parser.add_argument("--village-b", type=int, default=200, help="Parcels for Vellore Nagar (TN)")
    parser.add_argument("--village-c", type=int, default=100, help="Parcels for Dongri Pahad (JH, community)")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "data",
        help="Output directory for generated data files",
    )
    args = parser.parse_args()

    total = args.village_a + args.village_b + args.village_c
    print(f"\nBhoomi Setu — Synthetic Dataset Generator")
    print(f"  Seed: {args.seed}")
    print(f"  Villages: A={args.village_a}, B={args.village_b}, C={args.village_c}  (Total: {total})")
    print(f"  Output: {args.output_dir}\n")

    summary = generate(
        village_counts={"A": args.village_a, "B": args.village_b, "C": args.village_c},
        seed=args.seed,
        output_dir=args.output_dir,
    )

    print("\nDataset Summary:")
    for vk, vs in summary["villages"].items():
        anomaly_str = ""
        if vs["schema_type"] == "individual":
            anomaly_str = (
                f"  mismatches={vs['injected_mismatches']},"
                f" duplicates={vs['injected_duplicates']},"
                f" benami={vs['injected_benami']}"
            )
        print(f"  Village {vk}: {vs['name']} [{vs['schema_type']}] — {vs['parcel_count']} parcels{anomaly_str}")

    print(f"\nTotal: {summary['total_parcels']} parcels across {len(summary['villages'])} villages.")


if __name__ == "__main__":
    main()
