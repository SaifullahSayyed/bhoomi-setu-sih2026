"""
schema_harmonizer.py — Bhoomi Setu Adaptive Schema Harmonizer
=============================================================
Priority 4c | Status: Architecture Demo (Proof of Concept)

PURPOSE
-------
Demonstrates adaptive schema mapping across three distinct Indian state
record formats (UP, TN, JH) into a canonical unified schema.

DISCLAIMER & HONEST LABELING
----------------------------
This is a small proof-of-concept demonstration across 3 mock state formats,
NOT a claim of full cross-state generalization. Real-world cross-state
harmonization involves hundreds of dialectal variations, distinct revenue
codes, and complex tenure systems.

MOCK STATE FORMATS
------------------
  1. UP Format (Bhoomi UP / Bhulekh style):
     Fields: khasra_no, khatedar_naam, kshetrafal_bigha, fasli_varsh, rinn_vivaran

  2. TN Format (Tamil Nadu e-Services style):
     Fields: survey_no, pattadar_name, extent_cents, taluk_code, encumbrance_status

  3. JH Format (Jharbhoomi / FRA Community style):
     Fields: plot_id, samiti_naam, raqba_decimal_acre, kanoon_dhara, sansadhan_adhikar

CANONICAL TARGET SCHEMA
-----------------------
  - ulpin (unique parcel identifier)
  - jurisdiction (state, district)
  - primary_claimant (individual name or community entity)
  - area_hectares (normalized numeric value)
  - original_unit (bigha, cents, acres)
  - encumbrance_flag (boolean)
  - tenure_type (individual vs. community)
"""

import re
from typing import Any

# ---------------------------------------------------------------------------
# HEURISTIC FIELD MAPPINGS
# ---------------------------------------------------------------------------
FIELD_PATTERNS = {
    "identifier": [r"khasra", r"survey", r"plot", r"ulpin", r"khata"],
    "claimant": [r"khatedar", r"pattadar", r"owner", r"samiti", r"naam", r"name"],
    "area": [r"kshetrafal", r"extent", r"raqba", r"area", r"rakba"],
    "encumbrance": [r"rinn", r"encumbrance", r"mortgage", r"dharana", r"vivaran"],
    "tenure_type": [r"kanoon", r"fra", r"dhara", r"community", r"adhikar"],
}

from mirror_engine import UNIT_TO_HECTARES

# Alias to maintain internal compatibility while sharing single source of truth
UNIT_FACTORS = UNIT_TO_HECTARES


class SchemaHarmonizer:
    """
    Toy adaptive schema harmonization engine (Priority 4c POC).
    Uses regex heuristics and value distributions to map diverse state schemas.
    """

    def infer_field_role(self, field_name: str) -> str:
        f_lower = field_name.lower()
        for role, patterns in FIELD_PATTERNS.items():
            if any(re.search(p, f_lower) for p in patterns):
                return role
        return "unmapped"

    def detect_unit_from_field(self, field_name: str, sample_val: Any) -> tuple[str, float]:
        f_lower = field_name.lower()
        if "bigha" in f_lower:
            return "bigha", UNIT_FACTORS["bigha"]
        if "cent" in f_lower:
            return "cents", UNIT_FACTORS["cents"]
        if "acre" in f_lower or "decimal" in f_lower:
            return "acres", UNIT_FACTORS["acres"]

        # Heuristic based on numeric magnitude if numeric
        try:
            val = float(sample_val)
            if val > 50:  # typically cents or sq meters
                return "cents", UNIT_FACTORS["cents"]
            elif val < 10:  # typically bigha or acres
                return "acres", UNIT_FACTORS["acres"]
        except (ValueError, TypeError):
            pass

        return "hectares", 1.0

    def harmonize_record(self, raw_record: dict, state_origin: str) -> dict:
        """
        Harmonizes a single raw record from a state format to canonical format.
        """
        canonical: dict[str, Any] = {
            "source_state": state_origin,
            "ulpin": "UNKNOWN",
            "primary_claimant": "Unknown",
            "area_hectares": 0.0,
            "original_area": 0.0,
            "original_unit": "unknown",
            "encumbrance_flag": False,
            "tenure_type": "individual",
            "raw_fields_mapped": {},
            "status_note": "Proof-of-concept harmonization demo (Priority 4c)",
        }

        for k, v in raw_record.items():
            role = self.infer_field_role(k)
            canonical["raw_fields_mapped"][k] = role

            if role == "identifier":
                canonical["ulpin"] = f"{state_origin[:2].upper()}-{str(v)}"
            elif role == "claimant":
                canonical["primary_claimant"] = str(v)
            elif role == "area":
                try:
                    num_val = float(v)
                    unit_name, factor = self.detect_unit_from_field(k, num_val)
                    canonical["original_area"] = num_val
                    canonical["original_unit"] = unit_name
                    canonical["area_hectares"] = round(num_val * factor, 4)
                except (ValueError, TypeError):
                    pass
            elif role == "encumbrance":
                v_str = str(v).lower().strip()
                # Negative indicator keywords meaning encumbrance-free
                is_free = (
                    v_str in ["nil", "none", "0", "false", "na", "n/a", "no", "null", ""]
                    or "nirbhar" in v_str
                    or "free" in v_str
                    or "shunya" in v_str
                    or "koi nahi" in v_str
                )
                # Positive indicators of active debt, loan, creditor, or monetary charge
                has_charge = (
                    "rinn" in v_str
                    or "mortgage" in v_str
                    or "yes" in v_str
                    or "active" in v_str
                    or "kcc" in v_str
                    or "kisan" in v_str
                    or "card" in v_str
                    or "bank" in v_str
                    or "sbi" in v_str
                    or "pnb" in v_str
                    or "loan" in v_str
                    or "₹" in v_str
                    or "rs" in v_str
                    or any(c.isdigit() for c in v_str)
                )
                canonical["encumbrance_flag"] = (not is_free) and (has_charge or len(v_str) > 3)
            elif role == "tenure_type":
                v_str = str(v).lower()
                if "fra" in v_str or "samiti" in v_str or "gram" in v_str or "adhikar" in v_str:
                    canonical["tenure_type"] = "community"

        return canonical


# ---------------------------------------------------------------------------
# TOY DATASETS FOR DEMONSTRATION
# ---------------------------------------------------------------------------
SAMPLE_STATE_RECORDS = {
    "Uttar Pradesh (Bhulekh)": {
        "khasra_no": "231/4",
        "khatedar_naam": "Ram Swaroop Yadav",
        "kshetrafal_bigha": "3.50",
        "fasli_varsh": "1430",
        "rinn_vivaran": "Kisan Credit Card SBI ₹75,000",
    },
    "Tamil Nadu (e-Services)": {
        "survey_no": "42/1B",
        "pattadar_name": "S. Muruganandam",
        "extent_cents": "145.0",
        "taluk_code": "VLR-04",
        "encumbrance_status": "Nil",
    },
    "Jharkhand (Jharbhoomi FRA)": {
        "plot_id": "117/CFR",
        "samiti_naam": "Dongri Pahad Gram Sabha CFR Samiti",
        "raqba_decimal_acre": "18.25",
        "kanoon_dhara": "FRA 2006 Section 3(1)(i)",
        "sansadhan_adhikar": "Minor Forest Produce (Tendu/Mahua)",
    },
}


def run_demo() -> list[dict]:
    harmonizer = SchemaHarmonizer()
    results = []
    for state, record in SAMPLE_STATE_RECORDS.items():
        harmonized = harmonizer.harmonize_record(record, state)
        results.append({
            "state_source": state,
            "raw_input": record,
            "harmonized_canonical": harmonized,
        })
    return results
