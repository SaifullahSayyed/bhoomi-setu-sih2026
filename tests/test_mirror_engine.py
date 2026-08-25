"""
test_mirror_engine.py — Pytest Suite for Mirror Engine
======================================================
Run: pytest tests/ -v

Tests cover:
  - Unit conversion
  - RoR area text parsing
  - Area mismatch detection
  - Gini coefficient formula (exact — this is the critical calculation)
  - Score assembly logic
  - Community governance health labels
"""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from mirror_engine import (
    MirrorEngine,
    MirrorConfig,
    gini_coefficient,
    governance_health_label,
    parse_ror_area,
    polygon_area_ha,
    UNIT_TO_HECTARES,
    normalise_unit,
)


                                                                             
                 
                                                                             

def test_unit_to_hectares_bigha():
    assert abs(UNIT_TO_HECTARES["bigha"] - 0.2529) < 1e-6


def test_unit_to_hectares_cents():
    assert abs(UNIT_TO_HECTARES["cents"] - 0.00404686) < 1e-8


def test_normalise_unit_alias():
    assert normalise_unit("bighas") == "bigha"
    assert normalise_unit("acre") == "acres"
    assert normalise_unit("hect") == "hectares"


                                                                             
              
                                                                             

def test_parse_ror_hindi_area():
    text = "ULPIN: UP001 | स्वामी: राम | क्षेत्रफल: 2.500 bigha | निर्भार | [OCR-simulated]"
    val, unit = parse_ror_area(text)
    assert val is not None
    assert abs(val - 2.5) < 1e-6
    assert unit == "bigha"


def test_parse_ror_english_area():
    text = "Survey No: TN001 | Owner: Murugan | Extent: 125.000 cents | Encumbrance-free"
    val, unit = parse_ror_area(text)
    assert val is not None
    assert abs(val - 125.0) < 1e-6
    assert unit == "cents"


def test_parse_ror_missing_area():
    text = "Survey No: TN001 | Owner: Murugan | No area field present"
    val, unit = parse_ror_area(text)
    assert val is None
    assert unit is None


                                                                             
                          
                                                                             

def test_polygon_area_known_square():
    """
    A 0.009° × 0.009° square at ~20°N should be approximately 1 ha.
    (0.009° lat × 111000 m/°) × (0.009° lon × 111000*cos(20°) m/°) ≈ 10000 m² = 1 ha
    """
    lat, lon = 20.0, 78.0
    side = 0.0009                                                      
    polygon = {
        "type": "Polygon",
        "coordinates": [[
            [lon,        lat],
            [lon + side, lat],
            [lon + side, lat + side],
            [lon,        lat + side],
            [lon,        lat],
        ]]
    }
    area = polygon_area_ha(polygon)
                                                        
    assert 0.8 < area < 1.2, f"Expected ~1 ha, got {area:.4f} ha"


def test_polygon_area_invalid():
    assert polygon_area_ha({}) == 0.0
    assert polygon_area_ha({"type": "Point", "coordinates": [0, 0]}) == 0.0


                                                                             
                                        
                                                                             

def test_gini_perfect_equality():
    """All members participate equally → G = 0"""
    values = [5.0] * 10
    g = gini_coefficient(values)
    assert g == 0.0, f"Expected 0.0, got {g}"


def test_gini_perfect_inequality():
    """One member holds all participation → G approaches 1"""
    values = [0.0] * 9 + [100.0]
    g = gini_coefficient(values)
                                                                                     
    assert abs(g - 0.9) < 0.001, f"Expected ~0.9, got {g}"


def test_gini_known_example():
    """
    For values [1,2,3,4,5] (n=5, sorted):
    Σ(i*x_i) = 1*1 + 2*2 + 3*3 + 4*4 + 5*5 = 1+4+9+16+25 = 55
    Σx_i = 15
    G = (2*55)/(5*15) - (5+1)/5 = 110/75 - 1.2 = 1.4667 - 1.2 = 0.2667
    """
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    g = gini_coefficient(values)
    expected = 0.2667
    assert abs(g - expected) < 0.001, f"Expected ~{expected}, got {g}"


def test_gini_empty():
    assert gini_coefficient([]) == 0.0


def test_gini_all_zeros():
    """All-zero participation — G = 0 (no one participates, no inequality)"""
    g = gini_coefficient([0.0, 0.0, 0.0, 0.0])
    assert g == 0.0


def test_gini_two_values_unequal():
    """[0, 10]: n=2, Σ(i*xi) = 1*0 + 2*10 = 20, Σxi=10, G = 40/20 - 3/2 = 2 - 1.5 = 0.5"""
    g = gini_coefficient([0.0, 10.0])
    assert abs(g - 0.5) < 0.001


                                                                             
                          
                                                                             

def test_health_healthy():
    result = governance_health_label(0.15)
    assert result["status"] == "healthy"


def test_health_warning():
    result = governance_health_label(0.40)
    assert result["status"] == "warning"


def test_health_alert():
    result = governance_health_label(0.65)
    assert result["status"] == "alert"


                                                                             
                                     
                                                                             

def _make_parcel(
    ulpin="UP001",
    area_text=1.0,
    unit="bigha",
    area_ha_polygon=0.2529,
    num_mutations=2,
    owners=None,
    schema_type="individual",
):
    if owners is None:
        owners = [{"name": "Test Owner", "id_hash": "abc123", "share_fraction": 1.0}]
    geo_side = math.sqrt(area_ha_polygon / 100) * 0.009
    lat, lon = 25.0, 81.0
    geometry = {
        "type": "Polygon",
        "coordinates": [[
            [lon, lat], [lon + geo_side, lat], [lon + geo_side, lat + geo_side],
            [lon, lat + geo_side], [lon, lat]
        ]]
    }
    mutations = [{"seq": i, "date": "2020-01-01", "event_type": "sale",
                  "from_owner": "A", "to_owner": "B", "remarks": ""} for i in range(num_mutations)]
    ror = f"ULPIN: {ulpin} | क्षेत्रफल: {area_text:.3f} {unit} | निर्भार | [OCR-simulated]"
    return {
        "ulpin": ulpin,
        "village": "TestVillage",
        "state": "UP",
        "schema_type": schema_type,
        "owners": owners,
        "area_textual": area_text,
        "area_unit": unit,
        "area_ha_textual": area_text * UNIT_TO_HECTARES.get(unit, 1.0),
        "ror_text": ror,
        "geometry": geometry,
        "mutation_history": mutations,
        "encumbrance": {"mortgaged": False},
        "declared_value_inr": 500_000,
        "income_stated_inr": 300_000,
    }


def test_score_clean_parcel():
    """A clean parcel with matching text/spatial area should score 100."""
    engine = MirrorEngine()
    parcel = _make_parcel(area_text=1.0, unit="bigha", area_ha_polygon=0.2529)
    engine.build_index([parcel])
    result = engine.score_parcel(parcel)
    assert result.mirror_score == 100
    assert result.flags == []
    assert result.sealing_eligible is True


def test_score_area_mismatch_deduction():
    """Textual area 30% larger than polygon → -30 deduction."""
    engine = MirrorEngine()
                                                                 
    parcel = _make_parcel(area_text=1.3, unit="bigha", area_ha_polygon=0.2529)
    engine.build_index([parcel])
    result = engine.score_parcel(parcel)
    assert result.mirror_score == 70            
    assert any("textual_area_mismatch" in f for f in result.flags)


def test_score_no_mutations_deduction():
    """No mutation history → -15 deduction."""
    engine = MirrorEngine()
    parcel = _make_parcel(num_mutations=0)
    engine.build_index([parcel])
    result = engine.score_parcel(parcel)
    assert result.mirror_score == 85            
    assert any("no_mutation_history" in f for f in result.flags)


def test_score_duplicate_ulpin():
    """Two parcels with same ULPIN → duplicate flag → -40 on both."""
    engine = MirrorEngine()
    p1 = _make_parcel(ulpin="UP001", area_text=1.0, num_mutations=2)
    p2 = _make_parcel(ulpin="UP001", area_text=1.0, num_mutations=2)               
    p2["owners"] = [{"name": "Different Owner", "id_hash": "def456", "share_fraction": 1.0}]
    engine.build_index([p1, p2])
    r1 = engine.score_parcel(p1)
    assert any("duplicate_ulpin" in f for f in r1.flags)
    assert r1.mirror_score <= 60                


def test_score_benami_flag():
    """Owner appearing on 6+ high-value parcels → benami flag → -15."""
    engine = MirrorEngine(MirrorConfig(benami_parcel_threshold=3, benami_value_threshold=100_000))
    shared_hash = "benami_hash_001"
    parcels = []
    for i in range(5):
        p = _make_parcel(ulpin=f"UP{i:03d}", num_mutations=1)
        p["owners"] = [{"name": "Balram Sahukar", "id_hash": shared_hash, "share_fraction": 1.0}]
        p["declared_value_inr"] = 500_000                   
        parcels.append(p)
    engine.build_index(parcels)
    result = engine.score_parcel(parcels[0])
    assert any("owner_pattern_flag" in f for f in result.flags)
    assert result.mirror_score <= 85                


def test_sealing_eligible_boundary():
    """Score exactly 85 = eligible; score 84 = not eligible."""
    config = MirrorConfig(sealing_threshold=85)
    engine = MirrorEngine(config)

                                                                    
    p85 = _make_parcel(num_mutations=0)
    engine.build_index([p85])
    r85 = engine.score_parcel(p85)
    assert r85.mirror_score == 85
    assert r85.sealing_eligible is True

                                                                            
    p55 = _make_parcel(area_text=1.5, unit="bigha", area_ha_polygon=0.2529, num_mutations=0)
    engine.build_index([p55])
    r55 = engine.score_parcel(p55)
    assert r55.mirror_score <= 70
    assert r55.sealing_eligible is False


def test_score_floored_at_zero_with_multiple_deductions():
    """
    When multiple severe flags trigger simultaneously (e.g. area mismatch -30,
    duplicate claim -40, benami -15, no mutation -15 = total deduction 100),
    or if deductions sum to over 100, the Mirror Confidence Score is strictly
    clamped at 0 (max(0, 100 - total_deduction)) and never goes negative.
    """
                                                           
    engine = MirrorEngine(MirrorConfig(benami_parcel_threshold=1, benami_value_threshold=10_000))
    shared_hash = "super_benami_hash"
    p1 = _make_parcel(
        ulpin="UP_COLLISION",
        area_text=2.5,                       
        unit="bigha",
        area_ha_polygon=0.2529,
        num_mutations=0,                      
    )
    p1["owners"] = [{"name": "Balram Sahukar", "id_hash": shared_hash, "share_fraction": 1.0}]
    p1["declared_value_inr"] = 1_000_000                

    p2 = _make_parcel(ulpin="UP_COLLISION", num_mutations=0)                                   
    p2["owners"] = [{"name": "Different Owner", "id_hash": shared_hash, "share_fraction": 1.0}]
    p2["declared_value_inr"] = 1_000_000

    engine.build_index([p1, p2])
    result = engine.score_parcel(p1)

                                                             
    assert result.mirror_score == 0
    assert len(result.flags) >= 4
    assert result.sealing_eligible is False

                                                                                        
    oversized_config = MirrorConfig(
        deduct_area_mismatch=60,
        deduct_duplicate=60,
        deduct_benami=30,
    )
    oversized_engine = MirrorEngine(oversized_config)
    oversized_engine.build_index([p1, p2])
    result_oversized = oversized_engine.score_parcel(p1)
    assert result_oversized.mirror_score == 0, f"Expected 0 (floored), got {result_oversized.mirror_score}"
    assert result_oversized.mirror_score >= 0


def test_schema_harmonizer_encumbrance_parsing():
    """
    Verifies that raw encumbrance text is accurately interpreted:
    - 'Kisan Credit Card SBI ₹75,000' -> encumbrance_flag: True
    - 'Nil' or 'Encumbrance-free' or 'निर्भार' -> encumbrance_flag: False
    """
    from schema_harmonizer import SchemaHarmonizer

    harmonizer = SchemaHarmonizer()

                           
    up_record = {
        "khasra_no": "231/4",
        "khatedar_naam": "Ram Swaroop Yadav",
        "kshetrafal_bigha": "3.50",
        "rinn_vivaran": "Kisan Credit Card SBI ₹75,000",
    }
    canon_up = harmonizer.harmonize_record(up_record, "Uttar Pradesh")
    assert canon_up["encumbrance_flag"] is True, "Kisan Credit Card must be flagged as active encumbrance"
    assert canon_up["primary_claimant"] == "Ram Swaroop Yadav"
    assert canon_up["area_hectares"] > 0

                                
    tn_record = {
        "survey_no": "42/1B",
        "pattadar_name": "S. Muruganandam",
        "extent_cents": "145.0",
        "encumbrance_status": "Nil",
    }
    canon_tn = harmonizer.harmonize_record(tn_record, "Tamil Nadu")
    assert canon_tn["encumbrance_flag"] is False, "'Nil' encumbrance must produce False"


