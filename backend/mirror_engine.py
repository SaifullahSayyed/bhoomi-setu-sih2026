"""
mirror_engine.py — Bhoomi Setu Mirror Engine
=============================================
Priority 1b | Status: Working Prototype

PURPOSE
-------
Implements the "Mirror" Torrens principle: ensures the land register accurately
reflects ground reality BEFORE any record is trusted or sealed on-chain.

For each parcel, the Mirror Engine:
  1. Parses the textual RoR entry to extract area + unit
  2. Normalises both textual and spatial areas to hectares
  3. Flags area mismatches, duplicate claims, and benami-style patterns
  4. Also computes the Gini coefficient for community governance health (Priority 2b)
  5. Emits a Mirror Confidence Score (0–100) with a human-readable flag list

WHY THIS EXISTS BEFORE BLOCKCHAIN
----------------------------------
India's land titles are legally "presumptive," not "conclusive." Registration
records a transaction but does not guarantee ownership. Sealing an incorrect
record on-chain makes the error permanent. The Mirror Engine resolves this:
only a record that passes reconciliation earns a high enough score to be sealed.

SCORE CALCULATION (deductions from 100)
----------------------------------------
  -30  : area mismatch (textual RoR vs. polygon area > tolerance)
  -40  : duplicate claim (same ULPIN or overlapping geometry)
  -15  : benami-style owner-pattern flag
  -15  : missing mutation history (no chain of title)
  +0   : no adjustments for clean records (ceiling is 100)
  Min  : 0 (clamped)
"""

import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import pyproj
import shapely.geometry

UNIT_TO_HECTARES: dict[str, float] = {
    "hectares": 1.0,
    "ha": 1.0,
    "acres": 0.404686,
    "acre": 0.404686,
    "bigha": 0.2529,
    "biswa": 0.012645,
    "cents": 0.00404686,
    "cent": 0.00404686,
    "grounds": 0.02230,
    "ground": 0.02230,
    "guntha": 0.01012,
    "marla": 0.002529,
    "sq_meters": 0.0001,
    "sqm": 0.0001,
}

                                                                  
UNIT_ALIASES: dict[str, str] = {
    "biga": "bigha",
    "bigas": "bigha",
    "bighas": "bigha",
    "बिघा": "bigha",
    "cent": "cents",
    "sents": "cents",
    "acre": "acres",
    "एकड़": "acres",
    "hectare": "hectares",
    "hect": "hectares",
}


def normalise_unit(raw: str) -> str:
    raw = raw.strip().lower().replace(".", "")
    return UNIT_ALIASES.get(raw, raw)


                                                                             
                                                             
                                                                             
@dataclass
class MirrorConfig:
    area_tolerance: float = 0.10                                                 
    benami_parcel_threshold: int = 4                                                                             
    benami_value_threshold: float = 250_000.0                                
    sealing_threshold: int = 85                                                     

                      
    deduct_area_mismatch: int = 30
    deduct_duplicate: int = 40
    deduct_benami: int = 15
    deduct_no_mutation_history: int = 15


                                                                             
                                                                    
                                                                         
                                            
                                                                             
def utm_zone_from_lon(lon: float) -> int:
    zone = math.floor((lon + 180.0) / 6.0) + 1
    return max(1, min(60, zone))


def polygon_area_ha(geometry: dict) -> float:
    if not geometry or geometry.get("type") != "Polygon":
        return 0.0
    coords = geometry.get("coordinates")
    if not coords or not coords[0]:
        return 0.0
    ring = coords[0]
    if len(ring) < 4:
        return 0.0

    lons = [c[0] for c in ring]
    avg_lon = sum(lons) / len(lons)
    zone = utm_zone_from_lon(avg_lon)
    epsg_code = f"EPSG:326{zone:02d}"

    try:
        transformer = pyproj.Transformer.from_crs("EPSG:4326", epsg_code, always_xy=True)
        projected_coords = [transformer.transform(c[0], c[1]) for c in ring]
        poly = shapely.geometry.Polygon(projected_coords)
        area_sqm = poly.area
        return round(area_sqm / 10_000.0, 6)
    except Exception:
        return 0.0


def polygons_overlap(g1: dict, g2: dict, tolerance_ha: float = 0.01) -> bool:
    if not g1 or not g2 or g1.get("type") != "Polygon" or g2.get("type") != "Polygon":
        return False

    c1 = g1.get("coordinates", [[]])[0]
    c2 = g2.get("coordinates", [[]])[0]
    if len(c1) < 4 or len(c2) < 4:
        return False

    lons1 = [pt[0] for pt in c1]
    lats1 = [pt[1] for pt in c1]
    lons2 = [pt[0] for pt in c2]
    lats2 = [pt[1] for pt in c2]

    minx1, maxx1 = min(lons1), max(lons1)
    miny1, maxy1 = min(lats1), max(lats1)
    minx2, maxx2 = min(lons2), max(lons2)
    miny2, maxy2 = min(lats2), max(lats2)

    tol = 0.0001
    if not (minx1 < maxx2 + tol and maxx1 > minx2 - tol and
            miny1 < maxy2 + tol and maxy1 > miny2 - tol):
        return False

    try:
        p1 = shapely.geometry.shape(g1)
        p2 = shapely.geometry.shape(g2)
        return bool(p1.intersects(p2) and (p1.intersection(p2).area > 0 or p1.equals(p2)))
    except Exception:
        return True


                                                                             
                                   
                                                                             
_AREA_PATTERN = re.compile(
    r"(?:area|extent|क्षेत्रफल|kshetrafal)[:\s]*"
    r"([\d,]+(?:\.\d+)?)"                                               
    r"\s*"
    r"([a-zA-Z\u0900-\u097F]+)",                                          
    re.IGNORECASE | re.UNICODE,
)


def parse_ror_area(ror_text: str) -> tuple[float | None, str | None]:
    """
    Extracts area value and unit from a textual RoR entry.

    Returns (area_value, unit_string) or (None, None) if unparseable.

    NOTE: This is a regex-based parser operating on already-structured text.
    The prototype does NOT perform OCR on scanned handwriting images — the
    'ror_text' field in the dataset represents the *output* of an OCR pipeline,
    which is already in ASCII/Unicode text form. This is clearly documented
    as a prototype simplification. A production system would use a trained
    OCR model (e.g., Tesseract + a fine-tuned language model for RoR layout).
    """
    match = _AREA_PATTERN.search(ror_text)
    if not match:
        return None, None
    raw_value = match.group(1).replace(",", "")
    raw_unit = match.group(2).strip()
    try:
        return float(raw_value), normalise_unit(raw_unit)
    except ValueError:
        return None, None


                                                                             
                                                                                      
                                                                             
def gini_coefficient(values: list[float]) -> float:
    """
    Computes the Gini coefficient over a list of values.

    Formula: G = (2 × Σ(i × x_i)) / (n × Σx_i) - (n+1)/n
    where x_i are values sorted in ascending order, i is the 1-based rank index.

    G = 0.0 → perfect equality (all values identical)
    G = 1.0 → perfect inequality (one value holds everything)

    This is the EXACT formula specified in the project design — not an
    approximation. Used for Elite-Capture Detection in Priority 2b.
    """
    n = len(values)
    if n == 0:
        return 0.0
    sorted_vals = sorted(values)
    total = sum(sorted_vals)
    if total == 0:
        return 0.0                                                

    weighted_sum = sum((i + 1) * x for i, x in enumerate(sorted_vals))                                         
    g = (2 * weighted_sum) / (n * total) - (n + 1) / n
    return round(max(0.0, min(1.0, g)), 4)                                        


def governance_health_label(gini: float) -> dict[str, str]:
    """Translates a Gini value into a human-readable governance health status."""
    if gini < 0.30:
        return {"status": "healthy", "label": "✅ Governance Health: Healthy", "color": "green"}
    elif gini < 0.50:
        return {"status": "warning", "label": "⚠️ Warning: Moderate concentration", "color": "yellow"}
    else:
        return {"status": "alert", "label": "🔴 Alert: Voting power concentrated", "color": "red"}


                                                                             
                        
                                                                             
@dataclass
class MirrorResult:
    ulpin: str
    mirror_score: int
    flags: list[str]
    scoring_breakdown: dict[str, int]
    computed_area_ha: float
    textual_area_ha: float | None
    area_discrepancy_pct: float | None
    sealing_eligible: bool
    schema_type: str                                

    def to_dict(self) -> dict:
        return {
            "ulpin": self.ulpin,
            "mirror_score": self.mirror_score,
            "flags": self.flags,
            "scoring_breakdown": self.scoring_breakdown,
            "computed_area_ha": round(self.computed_area_ha, 6),
            "textual_area_ha": round(self.textual_area_ha, 6) if self.textual_area_ha else None,
            "area_discrepancy_pct": round(self.area_discrepancy_pct, 2) if self.area_discrepancy_pct else None,
            "sealing_eligible": self.sealing_eligible,
            "schema_type": self.schema_type,
        }


                                                                             
                          
                                                                             
class MirrorEngine:
    def __init__(self, config: MirrorConfig | None = None) -> None:
        self.config = config or MirrorConfig()

                                                                     
        self._ulpin_index: dict[str, list[str]] = {}                                               
        self._geometry_index: list[tuple[str, dict]] = []                      
        self._owner_index: dict[str, list[str]] = {}                              
        self._value_index: dict[str, float] = {}                                   

                                                                             
                                                                                  
                                                                             
    def build_index(self, parcels: list[dict]) -> None:
        """
        Builds lookup indexes for ULPIN duplicates, spatial overlaps, and
        owner-pattern (benami) detection. Call once on the full dataset
        before scoring individual parcels.
        """
        self._ulpin_index = {}
        self._geometry_index = []
        self._owner_index = {}
        self._value_index = {}

        for p in parcels:
            ulpin = p["ulpin"]

                         
            self._ulpin_index.setdefault(ulpin, []).append(ulpin)

                                                 
            if "geometry" in p:
                self._geometry_index.append((ulpin, p["geometry"]))

                                                 
            if p.get("schema_type") == "individual":
                for owner in p.get("owners", []):
                    h = owner.get("id_hash", "")
                    if h:
                        self._owner_index.setdefault(h, []).append(ulpin)
                self._value_index[ulpin] = p.get("declared_value_inr", 0)

                                                                             
                           
                                                                             
    def score_parcel(self, parcel: dict) -> MirrorResult:
        ulpin = parcel["ulpin"]
        schema = parcel.get("schema_type", "individual")
        flags: list[str] = []
        deductions: dict[str, int] = {}

                                                                           
                                                                                 
        if schema == "community":
            return self._score_community(parcel, flags, deductions)

                                                                            
                                    
                                                                            
        ror_text = parcel.get("ror_text", "")
        text_val, text_unit = parse_ror_area(ror_text)

        textual_ha: float | None = None
        if text_val is not None and text_unit in UNIT_TO_HECTARES:
            textual_ha = text_val * UNIT_TO_HECTARES[text_unit]
        elif text_val is None:
            flags.append("ror_parse_failed: could not extract area from text")

                                                                            
                                                    
                                                                            
        geometry = parcel.get("geometry", {})
        spatial_ha = polygon_area_ha(geometry)

                                                                            
                                     
                                                                            
        discrepancy_pct: float | None = None
        if textual_ha and spatial_ha > 0:
            discrepancy_pct = abs(textual_ha - spatial_ha) / spatial_ha
            if discrepancy_pct > self.config.area_tolerance:
                pct_str = f"{discrepancy_pct * 100:.1f}%"
                flags.append(f"textual_area_mismatch: {pct_str}")
                deductions["area_mismatch"] = self.config.deduct_area_mismatch

                                                                            
                                                       
                                                                            
        dup_ulpins = self._ulpin_index.get(ulpin, [])
        if len(dup_ulpins) > 1:
            flags.append(f"duplicate_ulpin_detected: {len(dup_ulpins)} records share this ULPIN")
            deductions["duplicate_claim"] = self.config.deduct_duplicate
        else:
                                                      
            for other_ulpin, other_geom in self._geometry_index:
                if other_ulpin != ulpin and polygons_overlap(geometry, other_geom):
                    flags.append(f"spatial_overlap_detected: overlaps with {other_ulpin}")
                    deductions.setdefault("duplicate_claim", self.config.deduct_duplicate)
                    break

                                                                            
                                             
                                                                            
        for owner in parcel.get("owners", []):
            h = owner.get("id_hash", "")
            owner_ulpins = self._owner_index.get(h, [])
            high_value_count = sum(
                1 for u in owner_ulpins
                if self._value_index.get(u, 0) >= self.config.benami_value_threshold
            )
            if high_value_count >= self.config.benami_parcel_threshold:
                flags.append(
                    f"owner_pattern_flag: owner appears on {high_value_count} "
                    f"high-value parcels (≥₹{self.config.benami_value_threshold:,.0f})"
                )
                deductions["benami_pattern"] = self.config.deduct_benami
                break                        

                                                                            
                                               
                                                                            
        if not parcel.get("mutation_history"):
            flags.append("no_mutation_history: no chain of title recorded")
            deductions["no_mutation_history"] = self.config.deduct_no_mutation_history

                                                                            
                                
                                                                            
        total_deduction = sum(deductions.values())
        score = max(0, 100 - total_deduction)

        scoring_breakdown = {
            "base_score": 100,
            **{f"deduct_{k}": -v for k, v in deductions.items()},
            "final_score": score,
        }

        return MirrorResult(
            ulpin=ulpin,
            mirror_score=score,
            flags=flags,
            scoring_breakdown=scoring_breakdown,
            computed_area_ha=spatial_ha,
            textual_area_ha=textual_ha,
            area_discrepancy_pct=discrepancy_pct * 100 if discrepancy_pct else None,
            sealing_eligible=score >= self.config.sealing_threshold,
            schema_type="individual",
        )

    def _score_community(
        self, parcel: dict, flags: list[str], deductions: dict[str, int]
    ) -> MirrorResult:
        """
        Community parcel scoring. Checks:
          - FRA claim type present
          - Registered members list non-empty
          - RoR text parseable
          - Geometry present
        Community parcels are not individually owned and cannot be sealed with
        an individual owner hash — they use the CommunityTenure contract instead.
        """
        ulpin = parcel["ulpin"]
        if not parcel.get("fra_claim_type"):
            flags.append("missing_fra_claim_type")
            deductions["missing_claim"] = 20
        if not parcel.get("registered_members"):
            flags.append("missing_registered_members")
            deductions["missing_members"] = 20
        geometry = parcel.get("geometry", {})
        spatial_ha = polygon_area_ha(geometry)
        if spatial_ha == 0:
            flags.append("invalid_geometry")
            deductions["invalid_geometry"] = 15

        score = max(0, 100 - sum(deductions.values()))
        return MirrorResult(
            ulpin=ulpin,
            mirror_score=score,
            flags=flags,
            scoring_breakdown={"base_score": 100, **{f"deduct_{k}": -v for k, v in deductions.items()}, "final_score": score},
            computed_area_ha=spatial_ha,
            textual_area_ha=None,
            area_discrepancy_pct=None,
            sealing_eligible=False,                                                            
            schema_type="community",
        )

                                                                             
                                               
                                                                             
    def compute_community_gini(self, voting_history: list[dict], members: list[dict]) -> dict:
        """
        Computes the Gini coefficient of voting participation across community members.
        Used for Elite-Capture Detection in Priority 2b.

        Returns the Gini value, health label, and per-member participation stats.
        """
        member_addresses = {m["eth_address"] for m in members}
        participation: dict[str, int] = {addr: 0 for addr in member_addresses}

        for vote in voting_history:
            for signer in vote.get("signers", []):
                if signer in participation:
                    participation[signer] += 1

        counts = list(participation.values())
        g = gini_coefficient(counts)
        health = governance_health_label(g)

        return {
            "gini_coefficient": g,
            "health_status": health["status"],
            "health_label": health["label"],
            "health_color": health["color"],
            "total_votes": len(voting_history),
            "member_count": len(members),
            "participation_counts": {
                m["name_pseudonym"]: participation.get(m["eth_address"], 0)
                for m in members
            },
        }

                                                                             
                   
                                                                             
    def score_all(self, parcels: list[dict]) -> dict[str, Any]:
        """
        Scores all parcels. Builds index first, then scores each parcel.
        Returns a summary dict plus per-parcel results.
        """
        self.build_index(parcels)
        results = [self.score_parcel(p) for p in parcels]
        result_dicts = [r.to_dict() for r in results]

        individual = [r for r in results if r.schema_type == "individual"]
        scores = [r.mirror_score for r in individual]

        return {
            "total_parcels": len(results),
            "individual_parcels": len(individual),
            "community_parcels": len(results) - len(individual),
            "eligible_for_sealing": sum(1 for r in individual if r.sealing_eligible),
            "avg_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "flag_counts": _count_flags(results),
            "results": result_dicts,
        }


def _count_flags(results: list[MirrorResult]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in results:
        for f in r.flags:
            key = f.split(":")[0].strip()
            counts[key] = counts.get(key, 0) + 1
    return counts


                                                                             
                                                   
                                                                             
_engine_singleton: MirrorEngine | None = None


def get_engine() -> MirrorEngine:
    global _engine_singleton
    if _engine_singleton is None:
        _engine_singleton = MirrorEngine()
    return _engine_singleton
