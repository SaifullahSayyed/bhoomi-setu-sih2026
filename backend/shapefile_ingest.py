import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

try:
    import geopandas as gpd
    import shapely.geometry
    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False

from mirror_engine import UNIT_TO_HECTARES
from schema_harmonizer import SchemaHarmonizer


def is_shapefile_support_available() -> bool:
    return GEOPANDAS_AVAILABLE


def ingest_shapefile(shapefile_path: str) -> dict[str, Any]:
    if not is_shapefile_support_available():
        return {
            "success": False,
            "status": "unavailable",
            "message": "Extended geospatial capability (GeoPandas/pyogrio) is not installed in the active environment. Install backend/requirements-geo-extended.txt to enable Shapefile ingestion.",
            "parcels": [],
            "count": 0,
        }

    path = Path(shapefile_path)
    if not path.exists():
        return {
            "success": False,
            "status": "not_found",
            "message": f"Shapefile not found at: {shapefile_path}",
            "parcels": [],
            "count": 0,
        }

    try:
        gdf = gpd.read_file(str(path))
        if gdf.crs is None:
            gdf = gdf.set_crs("EPSG:4326")
        elif gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs("EPSG:4326")

        harmonizer = SchemaHarmonizer()
        parcels = []

        for idx, row in gdf.iterrows():
            raw_dict = {k: str(v) for k, v in row.items() if k != "geometry"}
            harmonized = harmonizer.harmonize_record(raw_dict, "Government Shapefile Export")

            khasra_no = raw_dict.get("KHASRA_NO") or raw_dict.get("khasra") or f"P-{idx+1:03d}"
            owner_name = harmonized.get("primary_claimant") or "Recorded Landholder"
            area_val = harmonized.get("original_area") or 1.0
            unit = harmonized.get("original_unit") or "acres"
            area_ha = area_val * UNIT_TO_HECTARES.get(unit, 0.404686)
            encumbrance_flag = harmonized.get("encumbrance_flag", False)
            tenure_type = harmonized.get("tenure_type", "individual")

            synth_id = f"GOV-SHP-{idx+1:04d}-{owner_name.replace(' ', '_')}"
            id_hash = hashlib.sha256(synth_id.encode()).hexdigest()
            ulpin = f"GV99{idx+1:010d}"

            geom_geojson = shapely.geometry.mapping(row.geometry)

            ror_text = (
                f"खसरा / Survey No: {khasra_no} | धारक का नाम: {owner_name} | "
                f"क्षेत्रफल: {area_val:.3f} {unit} | "
                f"ऋण भार: {'बंधक / Active Loan' if encumbrance_flag else 'निर्भार'} | "
                f"[SVAMITVA Government Shapefile Ingested Record]"
            )

            declared_value = round(area_ha * 1_500_000, 2)

            parcel_record = {
                "ulpin": ulpin,
                "khasra_no": khasra_no,
                "village": "Govt Survey Import (SVAMITVA)",
                "state": "National GIS Grid",
                "schema_type": tenure_type,
                "owners": [
                    {
                        "name": owner_name,
                        "share_fraction": 1.0,
                        "id_hash": id_hash,
                    }
                ],
                "area_textual": area_val,
                "area_unit": unit,
                "area_ha_textual": round(area_ha, 4),
                "geometry": geom_geojson,
                "ror_text": ror_text,
                "mutation_history": [
                    {
                        "seq": 1,
                        "date": "2024-01-15",
                        "event_type": "svamitva_survey_demarcation",
                        "from_owner": "Survey of India (Abadi/Cadastral)",
                        "to_owner": owner_name,
                        "remarks": "Official SVAMITVA drone survey adjudication.",
                    }
                ],
                "encumbrance": {
                    "mortgaged": encumbrance_flag,
                    "details": "Institutional Credit Facility" if encumbrance_flag else "None",
                },
                "declared_value_inr": declared_value,
                "source_format": "Esri Shapefile (.shp/.dbf/.shx/SVAMITVA)",
            }
            parcels.append(parcel_record)

        return {
            "success": True,
            "status": "ready",
            "message": f"Successfully ingested {len(parcels)} parcels from shapefile with CRS reprojected to EPSG:4326.",
            "source_crs": str(gdf.crs),
            "count": len(parcels),
            "parcels": parcels,
        }

    except Exception as e:
        return {
            "success": False,
            "status": "error",
            "message": f"Error ingesting shapefile: {str(e)}",
            "parcels": [],
            "count": 0,
        }
