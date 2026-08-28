# Bhoomi Setu — 3D Cadastral Risk Terrain Visualization Report
**Date:** August 28, 2026  
**Status:** 🟡 **Architecture Demo / Beta Visualization** (Isolated Client-Side Module)  
**Problem Statement:** SIH26014 — Ministry of Rural Development, Department of Land Resources (India)

---

## 1. Executive Summary

As part of Bhoomi Setu's Priority 4 Architecture Demonstrations, we have introduced a **3D Cadastral Risk Terrain Visualization** rendered with **MapLibre GL JS**. 

This feature transforms flat 2D cadastral polygons into a dynamic, interactive 3D risk topography where the vertical extrusion of each land parcel directly reflects its title discrepancy risk. Clean, high-confidence parcels sit flat on the terrain, while high-risk parcels (encumbered, mismatched area, duplicate claims) visually rise into solid, readable elevated blocks.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        3D RISK TERRAIN ELEVATION                       │
│                                                                        │
│   Score 55 (Severe Flag)     ▲  Height = 114m (Red Block)              │
│   Score 70 (Area Mismatch)   ▲  Height = 77m  (Yellow Block)           │
│   Score 100 (Clean Title)    ─  Height = 2m   (Flat Green Plinth)      │
│   FRA Community Land         ─  Height = 8m   (Flat Purple Plinth)     │
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

## 3. Visual Proportionality & Height Scaling Calibration

### 🔍 Visual Analysis: 12× vs. 2.5×
A standard rural agricultural parcel of $0.25\text{ to }1.0\text{ hectare}$ has a ground footprint of approximately $50\text{m} \times 50\text{m}$ to $100\text{m} \times 100\text{m}$.
- **At $12\times$ Scaling:** A parcel with score 55 extruded to $544\text{m}$ height ($>10:1$ aspect ratio), creating hyper-extended, thin needles/spikes that obscured neighboring plots and caused visual clutter.
- **Calibrated $2.5\times$ Scaling (Current Default):** A parcel with score 55 extrudes to $114\text{m}$ height ($\approx 1.5:1$ to $2:1$ aspect ratio), producing solid, highly readable 3D volumetric building-block shapes that fit naturally into the cadastral layout.

### Dynamic Height Formula:
$$\text{Extrusion Height } H = \max\Big(2,\, (100 - \text{MirrorScore}) \times \text{HeightScale} + 2\Big)$$

Where:
- $\text{MirrorScore} \in [0, 100]$ is computed by Bhoomi Setu's Mirror Engine.
- $\text{HeightScale}$ is set to **$2.5\times$** by default (tunable in real time from $0.5\times$ to $8.0\times$ via the UI slider).
- Baseline floor $= +2\text{m}$ for clean plots.
- **FRA Community Parcels:** Rendered at a flat plinth of $8\text{m}$ with signature purple styling (`#9333ea`).

### Color & Height Matrix:
| Title Status | Mirror Score Range | 3D Extrusion Height ($2.5\times$) | Hex Color | Visual Classification |
| :--- | :--- | :--- | :--- | :--- |
| **Clean Sealing Ready** | $85 - 100$ | $2\text{m} - 39.5\text{m}$ | `#16a34a` (Green) | Flat / Ground-level plinth |
| **Minor Discrepancy** | $70 - 84$ | $42\text{m} - 77\text{m}$ | `#eab308` (Yellow) | Moderate elevated block |
| **Severe Discrepancy** | $< 70$ | $79.5\text{m} - 252\text{m}$ | `#dc2626` (Red) | Prominent elevated block |
| **FRA Collective Land** | N/A (Multi-Sig) | $8\text{m}$ (Fixed) | `#9333ea` (Purple) | Distinct neutral plinth |

---

## 4. Benchmark Verification on Pilot Parcels

We verified the height and color output on representative parcels from the active 500-parcel dataset:

```
=== 3D RISK TERRAIN HEIGHT MAPPING AUDIT ===
1. Clean Parcel (Score 100) : ULPIN=UP231000000001 | Height=2m   | Color=Green  (#16a34a) | Flat Ground Plinth
2. Minor Risk (Score 85)     : ULPIN=UP231000000011 | Height=39.5m| Color=Green  (#16a34a) | Low Stepped Block
3. Moderate Risk (Score 70)  : ULPIN=UP231000000006 | Height=77m  | Color=Yellow (#eab308) | Medium Block (Area Mismatch)
4. Severe Risk (Score 55)    : ULPIN=UP231000000003 | Height=114.5m| Color=Red   (#dc2626) | Elevated Risk Block (Composite)
5. FRA Community Parcel      : ULPIN=JH117000000001 | Height=8m   | Color=Purple (#9333ea) | Neutral Flat Plateau
```

---

## 5. Induced-Failure Test & Graceful Degradation Audit

To prove true isolation, we executed an **induced runtime failure test**:

### 🧪 Test Procedure:
1. Injected an artificial WebGL exception (`throw new Error("Simulated WebGL Driver Failure: Hardware acceleration unavailable on target device.")`) directly into `ParcelMap3D.jsx`'s initialization lifecycle.
2. Executed test suite (`npm test`) and production build (`npm run build`).
3. **Observed Fallback Behavior:**
   - The 3D tab cleanly intercepted the error via `Map3DErrorBoundary` and rendered a structured informational card:
     ```
     [⚠️ 3D Cadastral Visualization Unavailable]
     Simulated WebGL Driver Failure: Hardware acceleration unavailable on target device.
     🛡️ Graceful Degradation: The core 2D Leaflet cadastral map, Mirror Engine reconciliation,
     and on-chain blockchain sealing remain 100% operational.
     ```
   - The rest of the Architecture Demo tabs (GNN, Schema Harmonizer, Shapefile Ingest) and all four core application views operated with **0 errors**.
4. Restored clean WebGL context check $\rightarrow$ verified normal 3D rendering resumed immediately.

---

## 6. Pitch Deck & Presentation Visual Guide

### Recommended Screenshots & Visual Angles for Pitch Deck:

#### 📸 Slide Screenshot 1: Rampur Khurd (UP) — Cadastral Discrepancy Topography
- **Preset Camera:** Focus Village A (`[81.9825°E, 25.8930°N]`, Zoom: `15.3`, Pitch: `60°`, Bearing: `-25°`).
- **Visual Subject:** A cluster of flat green titles punctuated by distinct yellow area-mismatch blocks and red duplicate-claim volumes.
- **Slide Caption:** *"Spatial Risk Elevation: Verified deeds stay flat; flagged titles rise into solid elevated blocks."*

#### 📸 Slide Screenshot 2: Vellore Nagar (TN) — Agricultural Cadastral Zoning
- **Preset Camera:** Focus Village B (`[79.1325°E, 12.9165°N]`, Zoom: `15.3`, Pitch: `60°`, Bearing: `35°`).
- **Visual Subject:** South-Indian agrarian parcel grid showing localized risk clusters amidst clean farmland.
- **Slide Caption:** *"District-Scale Audit: Rapid visual identification of title anomalies across 200 parcels in seconds."*

#### 📸 Slide Screenshot 3: Dongri Pahad (JH) — Forest Rights Act Collective Plinth
- **Preset Camera:** Focus Village C (`[85.2780°E, 23.0725°N]`, Zoom: `15.0`, Pitch: `55°`, Bearing: `15°`).
- **Visual Subject:** Uniform purple plateau illustrating community-governed land tenure under Gram Sabha multi-sig.
- **Slide Caption:** *"FRA Community Representation: Flat purple plateau reflects shared collective ownership without individual scoring distortion."*

---

## 7. Cumulative Regression Run

```
========================================================================================
  CUMULATIVE TEST VERIFICATION AFTER 3D MAP CALIBRATION
========================================================================================
  1. Python Backend Pytest Suite   : 25 / 25 PASSED (2.52s)
  2. Hardhat Smart Contracts Suite : 21 / 21 PASSED (2.00s)
  3. Frontend GIS Test Suite       : 5 / 5 PASSED (15.3ms)
  4. Vite Production Build         : 1,617 modules compiled cleanly in 7.47s
========================================================================================
  TOTAL PASS RATE: 51 / 51 (100%)
  REGRESSIONS INTRODUCED: 0
========================================================================================
```
