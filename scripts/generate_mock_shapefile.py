import math
import os
import random
from pathlib import Path

try:
    import geopandas as gpd
    import shapely.geometry
    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False

REPO_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = REPO_ROOT / "data" / "mock_gov_export"


def generate_mock_shapefile(num_parcels: int = 25, crs_epsg: str = "EPSG:32644") -> str:
    if not GEOPANDAS_AVAILABLE:
        raise RuntimeError("geopandas is required to generate mock shapefiles. Install via requirements-geo-extended.txt")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_shp_path = OUTPUT_DIR / "svamitva_drone_survey_parcels.shp"

    rng = random.Random(42)
    base_easting = 400_000.0   # UTM Zone 44N easting in meters
    base_northing = 2_850_000.0 # UTM Zone 44N northing in meters (~25.8°N)

    sample_owners = [
        "Ram Swaroop Yadav", "Ganga Prasad Mishra", "Sunita Devi", "Kallu Ram",
        "S. Muruganandam", "K. Rajagopal", "V. Selvam", "P. Annamalai",
        "Devi Besra", "Mangra Munda", "Jhano Soren", "Budhu Besra",
        "Arjun Toppo", "Sukri Oraon", "Rajeshwar Singh", "Prem Chand Verma",
        "Maheshwari Devi", "Rameshwar Bind", "Tribhuvan Nath", "Dhanpat Sah"
    ]

    records = []
    geometries = []

    cols = 5
    for i in range(num_parcels):
        row = i // cols
        col = i % cols
        x_min = base_easting + col * 80.0 + rng.uniform(-5.0, 5.0)
        y_min = base_northing + row * 80.0 + rng.uniform(-5.0, 5.0)
        width = rng.uniform(40.0, 70.0)
        height = rng.uniform(40.0, 70.0)

        poly = shapely.geometry.Polygon([
            (x_min, y_min),
            (x_min + width, y_min),
            (x_min + width, y_min + height),
            (x_min, y_min + height),
            (x_min, y_min),
        ])
        geometries.append(poly)

        area_sqm = poly.area
        area_acre = round(area_sqm / 4046.86, 3)
        owner = sample_owners[i % len(sample_owners)]
        village_code = "UP-PRT-001" if i < 15 else ("TN-VLR-002" if i < 20 else "JH-KHT-003")
        encumbrance = "KCC Loan SBI 75000" if i % 5 == 1 else "Nil"

        records.append({
            "KHASRA_NO": f"{100 + (i // 2)}/{(i % 2) + 1}",
            "OWNER_NAME": owner,
            "AREA_ACRE": area_acre,
            "VILLAGE_CD": village_code,
            "SURVEY_YR": 2026,
            "ENCUMB_ST": encumbrance,
            "LAND_TYPE": "Agricultural" if i < 22 else "Community Forest",
        })

    gdf = gpd.GeoDataFrame(records, geometry=geometries, crs=crs_epsg)
    gdf.to_file(str(out_shp_path))
    print(f"Generated mock government shapefile with {len(gdf)} parcels at: {out_shp_path}")
    return str(out_shp_path)


if __name__ == "__main__":
    generate_mock_shapefile()
