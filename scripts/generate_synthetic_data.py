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

# ---------------------------------------------------------------------------
# UNIT CONVERSION TABLE (to hectares)
# Why this table: India uses multiple traditional area units across states.
# This is exactly the kind of cross-state inconsistency SIH26014 calls out.
# ---------------------------------------------------------------------------
UNIT_TO_HECTARES: dict[str, float] = {
    "hectares": 1.0,
    "acres": 0.404686,
    "bigha": 0.2529,        # 1 UP bigha = 0.2529 ha (varies by state; UP used here)
    "biswa": 0.012645,      # 1 biswa = 1/20 bigha (UP)
    "cents": 0.00404686,    # 1 cent = 1/100 acre
    "grounds": 0.02230,     # 1 ground (TN) ≈ 222.97 sq m = 0.0223 ha
    "guntha": 0.01012,      # 1 guntha = 1/40 acre
    "marla": 0.002529,      # 1 marla (Punjab) = 1/160 bigha (approx)
}

# ---------------------------------------------------------------------------
# VILLAGE CONFIGURATION
# ---------------------------------------------------------------------------
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
        "individual": False,   # COMMUNITY OWNERSHIP — different schema entirely
    },
}

# ---------------------------------------------------------------------------
# FAKE NAME POOLS (clearly synthetic — no real person's name)
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# POLYGON GENERATOR (simple rectangular approximation)
# ---------------------------------------------------------------------------
def _make_polygon(lat: float, lon: float, area_ha: float, rng: random.Random) -> dict:
    """
    Generates a simple rectangular GeoJSON polygon approximating the given area.
    Uses a random orientation offset so parcels don't all align identically.

    1 degree latitude ≈ 111 km → 1 ha ≈ 0.009° latitude side (for a square)
    This is a simplification adequate for prototype spatial checks.
    """
    side_deg_lat = math.sqrt(area_ha / 100) * 0.009   # rough conversion
    side_deg_lon = side_deg_lat / math.cos(math.radians(lat))

    # Random offset from village center so parcels are spread out
    offset_lat = rng.uniform(-0.08, 0.08)
    offset_lon = rng.uniform(-0.08, 0.08)

    # Tiny perturbation so each parcel has unique location
    jitter_lat = rng.uniform(-0.005, 0.005)
    jitter_lon = rng.uniform(-0.005, 0.005)

    base_lat = lat + offset_lat + jitter_lat
    base_lon = lon + offset_lon + jitter_lon

    coords = [
        [base_lon,                base_lat],
        [base_lon + side_deg_lon, base_lat],
        [base_lon + side_deg_lon, base_lat + side_deg_lat],
        [base_lon,                base_lat + side_deg_lat],
        [base_lon,                base_lat],   # close ring
    ]
    return {"type": "Polygon", "coordinates": [coords]}


def _polygon_area_ha(polygon: dict) -> float:
    """
    Shoelace formula for approximate polygon area in hectares.
    Adequate for small parcels; a full prototype would use pyproj/GeoPandas.
    Formula: A = |Σ(x_i*(y_{i+1} - y_{i-1}))| / 2  (in degree²)
    1 degree² at ~20°N ≈ 10,850 km² → 1,085,000,000 ha (scale factor below)
    """
    coords = polygon["coordinates"][0][:-1]  # drop closing point
    n = len(coords)
    area_deg2 = 0.0
    for i in range(n):
        x1, y1 = coords[i]
        x2, y2 = coords[(i + 1) % n]
        area_deg2 += (x1 * y2 - x2 * y1)
    area_deg2 = abs(area_deg2) / 2.0

    # Convert degree² to hectares (approximate at ~20°N latitude)
    # 1° lat ≈ 111,000 m; 1° lon ≈ 111,000 * cos(lat) m
    # Using a fixed mid-India latitude of 20°N for prototype simplicity
    lat_m_per_deg = 111_000.0
    lon_m_per_deg = 111_000.0 * math.cos(math.radians(20))
    area_m2 = area_deg2 * lat_m_per_deg * lon_m_per_deg
    return area_m2 / 10_000.0  # m² → ha


# ---------------------------------------------------------------------------
# RECORD-OF-RIGHTS TEXT TEMPLATES
# Simulates what OCR-extracted text from a physical RoR would look like.
# In production, this is an OCR pipeline output; in this prototype it is
# structured text generated to match the GeoJSON data (with injected mismatches).
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# MUTATION HISTORY GENERATOR
# ---------------------------------------------------------------------------
_MUTATION_TYPES = ["inheritance", "sale", "gift_deed", "court_decree", "partition"]


def _gen_mutation_history(rng: random.Random, owner: str, num_events: int) -> list[dict]:
    history = []
    base_date = datetime(2000, 1, 1)
    prev_owner = _fake_name("A", rng)  # arbitrary prior owner
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


# ---------------------------------------------------------------------------
# INDIVIDUAL PARCEL GENERATOR
# ---------------------------------------------------------------------------
def _gen_individual_parcel(
    seq: int,
    village_key: str,
    vcfg: dict,
    rng: random.Random,
    anomalies: dict,
) -> dict:
    ulpin = f"{vcfg['state_code']}{vcfg['district_code']}{seq:09d}"
    unit = vcfg["primary_unit"]

    # Decide ownership (10% chance of co-ownership)
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

    # Area in primary unit (realistic range per village)
    if unit == "bigha":
        area_base = rng.uniform(0.5, 8.0)
    elif unit == "cents":
        area_base = rng.uniform(10.0, 500.0)
    else:  # acres
        area_base = rng.uniform(0.25, 5.0)

    area_ha_true = area_base * UNIT_TO_HECTARES[unit]

    # --- ANOMALY: AREA MISMATCH ---
    # Inject a discrepancy between the textual RoR area and the polygon area.
    # This simulates what happens when a scanned deed uses a different measurement
    # than the spatial survey — very common in practice.
    textual_area = area_base
    if seq in anomalies.get("area_mismatch_seqs", set()):
        mismatch_pct = rng.uniform(0.12, 0.35)  # 12–35% mismatch (all > 10% threshold)
        direction = rng.choice([-1, 1])
        textual_area = area_base * (1 + direction * mismatch_pct)

    # --- ANOMALY: BENAMI PATTERN ---
    declared_value = round(area_ha_true * rng.uniform(800_000, 2_500_000), 2)  # ₹/ha
    income_stated = 0.0
    if seq in anomalies.get("benami_seqs", set()):
        # Same hash (reused owner) will be detected by Mirror Engine across many parcels
        owners[0]["id_hash"] = anomalies["benami_owner_hash"]
        income_stated = rng.uniform(50_000, 150_000)   # low income vs. high asset
    else:
        income_stated = rng.uniform(100_000, 2_000_000)

    # Encumbrance (20% chance)
    if rng.random() < 0.20:
        creditor = f"{rng.choice(['SBI','PNB','UCO','Gramin Bank'])} Branch {rng.randint(100,999)}"
        enc_amount = round(declared_value * rng.uniform(0.3, 0.7), 2)
        encumbrance = {"mortgaged": True, "creditor": creditor, "amount_inr": enc_amount}
        enc_str = f"{creditor}, ₹{enc_amount:,.0f}"
    else:
        encumbrance = {"mortgaged": False, "creditor": None, "amount_inr": 0}
        enc_str = ""

    # Mutation history (0–4 events)
    num_mutations = rng.randint(0, 4)
    mutation_history = _gen_mutation_history(rng, primary_owner, num_mutations)

    # Geometry — use *true* area for the polygon; mismatch is only in the text
    geometry = _make_polygon(vcfg["lat_center"], vcfg["lon_center"], area_ha_true, rng)

    # RoR text uses *textual* area (which may differ from polygon)
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
        "anomaly_flags_injected": {   # ground truth for testing Mirror Engine
            "area_mismatch": seq in anomalies.get("area_mismatch_seqs", set()),
            "duplicate_claim": seq in anomalies.get("duplicate_seqs", set()),
            "benami_pattern": seq in anomalies.get("benami_seqs", set()),
        },
    }


# ---------------------------------------------------------------------------
# COMMUNITY PARCEL GENERATOR (Dongri Pahad — FRA Village C)
# Why a separate schema: India's Forest Rights Act (FRA) creates COMMUNITY
# forest resource rights — the parcel is NOT owned by any individual.
# Every prior academic solution models land as if it were individually owned.
# This schema gap is one of the two India-specific structural problems this
# project exists to address (see Priority 2b — Community Tenure Ledger).
# ---------------------------------------------------------------------------
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
        "schema_type": "community",  # NOT 'individual' — distinct schema
        "community_entity": "Dongri Pahad Gram Sabha",
        "fra_claim_type": claim_type,
        "registered_members": registered_members,   # full list — governance unit
        "resource_rights": resources,
        "area_textual": round(area_acres, 4),
        "area_unit": "acres",
        "area_ha_textual": round(area_ha, 6),
        "ror_text": ror_text,
        "geometry": geometry,
        "mutation_history": [],   # community land doesn't have individual mutation chain
        "encumbrance": {"mortgaged": False, "creditor": None, "amount_inr": 0},
        "declared_value_inr": 0,  # community land not individually valued
        "income_stated_inr": 0,
        "anomaly_flags_injected": {"area_mismatch": False, "duplicate_claim": False, "benami_pattern": False},
    }


# ---------------------------------------------------------------------------
# COMMUNITY MEMBERS + VOTING HISTORY GENERATOR
# ---------------------------------------------------------------------------
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

        # Elite-capture bias: first 3 always vote; others with decreasing probability
        signers = []
        for m in members:
            idx = m["member_id"] - 1
            if idx < 3:
                prob = 0.95    # "elite" members — almost always vote
            elif idx < 6:
                prob = 0.50    # middle tier
            else:
                prob = 0.15    # marginalised members rarely participate
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


# ---------------------------------------------------------------------------
# DUPLICATE ANOMALY INJECTOR
# ---------------------------------------------------------------------------
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

    # Pick source parcels to clone from (not themselves duplicates)
    source_pool = [p for p in parcels if not p["anomaly_flags_injected"]["duplicate_claim"]]
    for p in parcels:
        if not p["anomaly_flags_injected"]["duplicate_claim"]:
            continue
        source = rng.choice(source_pool)
        if rng.random() < 0.5:
            # ULPIN collision
            p["ulpin"] = source["ulpin"]
            p["duplicate_type"] = "ulpin_collision"
        else:
            # Spatial overlap — copy geometry
            p["geometry"] = source["geometry"]
            p["duplicate_type"] = "spatial_overlap"
        p.setdefault("duplicate_type", "ulpin_collision")

    return parcels


# ---------------------------------------------------------------------------
# MAIN GENERATOR
# ---------------------------------------------------------------------------
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
            # ----------------------------------------------------------------
            # COMMUNITY VILLAGE (Dongri Pahad)
            # ----------------------------------------------------------------
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
            # ----------------------------------------------------------------
            # INDIVIDUAL VILLAGE (Rampur Khurd / Vellore Nagar)
            # ----------------------------------------------------------------
            total = count
            n_mismatch = round(total * 0.15)
            n_dup = round(total * 0.05)
            n_benami = 8 if village_key == "A" else 0  # 8 parcels for benami syndicate in Village A

            # Pick which sequential IDs get which anomaly
            all_seqs = list(range(1, total + 1))
            rng.shuffle(all_seqs)
            mismatch_seqs = set(all_seqs[:n_mismatch])
            dup_seqs      = set(all_seqs[n_mismatch:n_mismatch + n_dup])
            benami_seqs   = set(all_seqs[n_mismatch + n_dup:n_mismatch + n_dup + n_benami])

            # Benami owner — same hash across all benami parcels, low income
            benami_owner_name = "Balram Sahukar"   # fictional character name
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

            # Inject duplicate geometry/ULPIN after all parcels are generated
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

            # Write CSV (flat view — geometry as WKT string for tabular use)
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

    # Write master summary
    (output_dir / "dataset_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"\n  Total parcels generated: {summary['total_parcels']}")
    print(f"  Output written to: {output_dir.resolve()}")
    return summary


# ---------------------------------------------------------------------------
# CLI ENTRYPOINT
# ---------------------------------------------------------------------------
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
