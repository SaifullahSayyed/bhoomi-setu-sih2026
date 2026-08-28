# Bhoomi Setu — 3D Cadastral Risk Terrain Visualization Report
**Date:** August 28, 2026  
**Status:** 🟡 **Architecture Demo / Beta Visualization** (Isolated Client-Side Module)  
**Problem Statement:** SIH26014 — Ministry of Rural Development, Department of Land Resources (India)

---

## 1. Executive Summary

As part of Bhoomi Setu's Priority 4 Architecture Demonstrations, we have introduced a **3D Cadastral Risk Terrain Visualization** rendered with **MapLibre GL JS**. 

This feature transforms flat 2D cadastral polygons into a dynamic, interactive 3D risk topography where the vertical extrusion of each land parcel directly reflects its title discrepancy risk. Clean, high-confidence parcels sit flat on the terrain, while high-risk parcels (encumbered, mismatched area, duplicate claims) visually rise into prominent elevated towers.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        3D RISK TERRAIN ELEVATION                       │
│                                                                        │
│   Score 30 (Severe Flag)     ▲  Height = 844m (Red Tower)              │
│   Score 70 (Area Mismatch)   ▲  Height = 364m (Yellow Block)           │
│   Score 100 (Clean Title)    ─  Height = 4m   (Flat Green Plinth)      │
│   FRA Community Land         ─  Height = 12m  (Flat Purple Plinth)     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Architectural Design & Zero-Risk Isolation

To uphold the project's strict reliability constraints ahead of the September 5 deadline:

1. **Zero Core Pipeline Modifications:**
   - `ParcelMap.jsx` (2D Leaflet map), `mirror_engine.py`, `backend/`, and all smart contracts were **left 100% untouched**.
   - No new backend API endpoints were created; the 3D map consumes the standard `GET /parcels/?limit=500` JSON payload.
2. **Library Choice — MapLibre GL JS:**
   - **Why MapLibre?** Fork of Mapbox GL JS with full native support for hardware-accelerated WebGL `fill-extrusion` polygon layers.
   - **Zero API Keys & Zero Signups:** Uses free CARTO Voyager and OpenStreetMap raster basemaps without requiring any proprietary access tokens or external subscriptions.
   - **Compared to Alternatives:** Avoided Mapbox GL JS (requires account/token) and CesiumJS (heavy globe runtime with excessive bundle weight and implementation risk).
3. **Dedicated Sub-Tab Location:**
   - Placed as a sub-tab inside `ArchitectureDemoView.jsx` labeled 🟡 **Architecture Demo / Beta Visualization**, keeping it cleanly grouped with other research POCs (GNN, Schema Harmonizer, Shapefile Ingest).

---

## 3. Mathematical Height Mapping Formula

Each parcel's extrusion height $H$ is computed dynamically in meters:

$$\text{Extrusion Height } H = \max\Big(4,\, (100 - \text{MirrorScore}) \times \text{HeightScale} + 4\Big)$$

Where:
- $\text{MirrorScore} \in [0, 100]$ is computed by Bhoomi Setu's Mirror Engine.
- $\text{HeightScale}$ is a tunable constant (default $= 12$, adjustable via real-time UI slider from $4\times$ to $30\times$).
- A baseline floor of $+4\text{m}$ ensures even clean parcels remain selectable and rendered above the ground tile layer.
- **FRA Community Parcels:** Rendered at a constant flat plinth of $12\text{m}$ with signature purple/violet styling (`#9333ea`), reflecting their collective governance under `CommunityTenure.sol`.

### Color Coding Matrix:
| Title Status | Mirror Score Range | 3D Extrusion Height ($12\times$) | Hex Color | Visual Classification |
| :--- | :--- | :--- | :--- | :--- |
| **Clean Sealing Ready** | $85 - 100$ | $4\text{m} - 184\text{m}$ | `#16a34a` (Green) | Flat / Ground-level plinth |
| **Minor Discrepancy** | $70 - 84$ | $196\text{m} - 364\text{m}$ | `#eab308` (Yellow) | Moderate elevated block |
| **Severe Discrepancy** | $< 70$ | $376\text{m} - 1204\text{m}$ | `#dc2626` (Red) | Prominent elevated spire |
| **FRA Collective Land** | N/A (Multi-Sig) | $12\text{m}$ (Fixed) | `#9333ea` (Purple) | Distinct neutral plinth |

---

## 4. Benchmark Verification on Pilot Parcels

We verified the height and color output on 4 representative parcels from the active 500-parcel dataset:

```
=== 3D RISK TERRAIN HEIGHT MAPPING AUDIT ===
1. Clean Parcel (Score 100) : ULPIN=UP231000000001 | Height=4m   | Color=Green  (#16a34a) | Flat Plinth
2. Moderate Risk (Score 70)  : ULPIN=UP231000000006 | Height=364m | Color=Yellow (#eab308) | Medium Rise (Area Mismatch)
3. Severe Risk (Score 55)    : ULPIN=UP231000000003 | Height=544m | Color=Red    (#dc2626) | High Tower (Area + No Mutation)
4. FRA Community Parcel      : ULPIN=JH117000000001 | Height=12m  | Color=Purple (#9333ea) | Neutral Base Plinth
```

---

## 5. Graceful Degradation & Error Isolation

The 3D component is wrapped inside a dedicated React `Map3DErrorBoundary` within `ArchitectureDemoView.jsx`:

1. **WebGL Detection:** On initialization, `ParcelMap3D.jsx` tests for WebGL context availability. If hardware acceleration is disabled, it displays a non-blocking informational fallback banner.
2. **Network Resilience:** If raster map tiles fail to load, the 3D polygon mesh continues to render over the default slate-950 canvas.
3. **Core Independence:** Any failure inside the 3D viewport is trapped inside the demo panel; the 2D Leaflet map, Sub-Registrar dashboard, and on-chain sealing actions remain 100% operational.

---

## 6. Pitch Deck & Presentation Guide

### Key Camera Presets Built into the UI:
1. **Focus Village A — Rampur Khurd (UP):**  
   - Coordinates: `[81.9825°E, 25.8930°N]`, Zoom: `15.3`, Pitch: `60°`, Bearing: `-25°`.  
   - *Visual highlights:* Cluster of clean green ground plots punctuated by prominent yellow area-mismatch spires and red duplicate-claim towers.
2. **Focus Village B — Vellore Nagar (TN):**  
   - Coordinates: `[79.1325°E, 12.9165°N]`, Zoom: `15.3`, Pitch: `60°`, Bearing: `35°`.  
   - *Visual highlights:* Southern agrarian layout with isolated high-risk dispute clusters.
3. **Focus Village C — Dongri Pahad (JH):**  
   - Coordinates: `[85.2780°E, 23.0725°N]`, Zoom: `15.0`, Pitch: `55°`, Bearing: `15°`.  
   - *Visual highlights:* Uniform purple plinth illustrating Forest Rights Act collective tenure.

### Pitch Narration Snippet (15 seconds):
> *"Beyond 2D tabular inspection, Bhoomi Setu provides a 3D Risk Terrain view. We map discrepancy risk directly to physical elevation: clean titles stay grounded on the terrain, while high-risk parcels visually rise into red risk spires. An auditor or bank officer can identify problematic cadastral zones across an entire district in a single glance."*

---

## 7. Cumulative Test Suite Verification

```
========================================================================================
  CUMULATIVE TEST VERIFICATION AFTER 3D MAP INTEGRATION
========================================================================================
  1. Python Backend Pytest Suite   : 25 / 25 PASSED (2.52s)
  2. Hardhat Smart Contracts Suite : 21 / 21 PASSED (2.00s)
  3. Frontend GIS Test Suite       : 5 / 5 PASSED (16.7ms)
  4. Vite Production Build         : 1,617 modules compiled cleanly in 7.47s
========================================================================================
  TOTAL PASS RATE: 51 / 51 (100%)
  REGRESSIONS INTRODUCED: 0
========================================================================================
```
