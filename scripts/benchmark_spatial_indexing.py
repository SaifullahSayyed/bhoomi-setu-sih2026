import json
import math
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from mirror_engine import polygons_overlap

try:
    import geopandas as gpd
    import shapely.geometry
    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False


def load_all_parcels():
    data_dir = REPO_ROOT / "data"
    all_parcels = []
    for fname in ["parcels_village_A.json", "parcels_village_B.json", "parcels_village_C_community.json"]:
        p = data_dir / fname
        if p.exists():
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
                all_parcels.extend(d.get("parcels", []))
    return all_parcels


def benchmark_pairwise(parcels, iterations=10):
    n = len(parcels)
    start_time = time.perf_counter()
    overlaps_found = 0

    for _ in range(iterations):
        count = 0
        for i in range(n):
            g1 = parcels[i].get("geometry", {})
            u1 = parcels[i].get("ulpin")
            for j in range(i + 1, n):
                g2 = parcels[j].get("geometry", {})
                u2 = parcels[j].get("ulpin")
                if u1 != u2 and polygons_overlap(g1, g2):
                    count += 1
        overlaps_found = count

    total_time = time.perf_counter() - start_time
    avg_time_ms = (total_time / iterations) * 1000.0
    return avg_time_ms, overlaps_found


def benchmark_geopandas_sindex(parcels, iterations=10):
    if not GEOPANDAS_AVAILABLE:
        return 0.0, 0, "GeoPandas not installed"

    records = []
    geoms = []
    for p in parcels:
        g = p.get("geometry", {})
        if g.get("type") == "Polygon":
            shape = shapely.geometry.shape(g)
            geoms.append(shape)
            records.append({"ulpin": p.get("ulpin")})

    gdf = gpd.GeoDataFrame(records, geometry=geoms, crs="EPSG:4326")

    start_time = time.perf_counter()
    overlaps_found = 0

    for _ in range(iterations):
        tree = gdf.sindex
        left, right = tree.query(gdf.geometry, predicate="intersects")
        mask = left < right
        overlaps_found = int(mask.sum())

    total_time = time.perf_counter() - start_time
    avg_time_ms = (total_time / iterations) * 1000.0
    return avg_time_ms, overlaps_found, "OK"


def run_benchmark():
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parcels = load_all_parcels()
    print("=" * 65)
    print(" BHOOMI SETU — SPATIAL OVERLAP DETECTION SCALE BENCHMARK")
    print("=" * 65)
    print(f"Total Parcels in Benchmark: {len(parcels)}")

    print("\n1. Running Pairwise Overlap Check (Iterative Bounding-Box/Shapely)...")
    pairwise_ms, pairwise_overlaps = benchmark_pairwise(parcels, iterations=5)
    print(f"   Pairwise Avg Latency   : {pairwise_ms:.2f} ms")
    print(f"   Pairwise Overlaps Found: {pairwise_overlaps}")

    if GEOPANDAS_AVAILABLE:
        print("\n2. Running GeoPandas Spatial R-Tree Index (sindex.query vectorized)...")
        gpd_ms, gpd_overlaps, _ = benchmark_geopandas_sindex(parcels, iterations=5)
        print(f"   GeoPandas sindex Latency: {gpd_ms:.2f} ms")
        print(f"   GeoPandas Overlaps Found: {gpd_overlaps}")

        speedup = pairwise_ms / gpd_ms if gpd_ms > 0 else 1.0
        print(f"\n⚡ Vectorized Spatial Indexing Speedup: {speedup:.2f}x faster")
    else:
        print("\nGeoPandas not installed; skipping sindex benchmark.")

    print("=" * 65)


if __name__ == "__main__":
    run_benchmark()
