# GIS Map Coordinate Real-World Placement Verification
**Bhoomi Setu — SIH26014 Verification Guide**

---

## 🗺️ Automated & Manual Verification Overview

This document provides both the automated test commands and the visual, manual verification steps to confirm that every land parcel renders at its **precise real-world geographic coordinates** in India on the Leaflet map (not floating in the ocean or flipped due to coordinate inversion).

---

## 1. Automated Test Suite

Run the built-in Node.js geospatial test suite:

```bash
cd bhoomi-setu/frontend
npm test
# Or: node --test test/map-coordinates.test.js
```

### What this test verifies:
1. **Coordinate Format Inversion:** Confirms that GeoJSON `[longitude, latitude]` arrays are accurately converted to Leaflet `[latitude, longitude]` without inversion errors (which would otherwise place India in the Indian Ocean).
2. **Village A (Rampur Khurd, UP):** Confirms centroid lands at **Latitude $\approx 25.892^\circ\text{N}$, Longitude $\approx 81.981^\circ\text{E}$** (Pratapgarh District, Uttar Pradesh).
3. **Village B (Vellore Nagar, TN):** Confirms centroid lands at **Latitude $\approx 12.916^\circ\text{N}$, Longitude $\approx 79.132^\circ\text{E}$** (Vellore District, Tamil Nadu).
4. **Village C (Dongri Pahad, JH):** Confirms centroid lands at **Latitude $\approx 23.072^\circ\text{N}$, Longitude $\approx 85.278^\circ\text{E}$** (Khunti Tribal Belt, Jharkhand).
5. **Color & Styling Verification:**
   - Score $\ge 85$: Emerald Green fill (`#15803d`).
   - Score $70 - 84$: Amber Yellow fill (`#a16207`).
   - Score $< 70$: Crimson Red fill (`#b91c1c`).
   - Community Village: Purple fill (`#7e22ce`) + Dashed stroke (`dashArray: '6, 6'`).

---

## 2. Step-by-Step Manual Visual Verification

To visually inspect parcels on the live OpenStreetMap base layer:

### Step 1: Start Backend and Frontend
```bash
# Terminal 1: Backend
cd bhoomi-setu/backend && uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd bhoomi-setu/frontend && npm run dev
```
Open `http://localhost:5173` in your browser.

### Step 2: Verify Sub-Registrar GIS Dashboard
1. On the **Sub-Registrar Dashboard**, ensure **"GIS Map + List"** view mode is active.
2. Select **"Rampur Khurd (UP - Bigha)"** from the Village dropdown:
   - Observe the map center directly over eastern Uttar Pradesh near Prayagraj/Pratapgarh.
   - Click parcel `UP231000000001` (Green) — observe polygon coordinates matching the local cadastral plot.
   - Click parcel `UP231000000002` (Yellow/Red) — observe the area discrepancy warning badge.
3. Switch Village dropdown to **"Vellore Nagar (TN - Cents)"**:
   - Observe map smoothly pan and zoom to northern Tamil Nadu near Vellore.
4. Switch Village dropdown to **"Dongri Pahad (JH - Community)"**:
   - Observe map zoom into the forested highlands of Khunti, Jharkhand.
   - Observe the **purple dashed boundary** denoting collective Forest Rights Act (FRA) Gram Sabha land.

### Step 3: Verify Citizen View Single-Parcel Cadastral Plot
1. Click the **Citizen Land Status** tab.
2. Search `UP231000000001` — observe the map zoom directly into the parcel's cadastral boundary with an active pin and polygon overlay.
3. Search `JH117000000001` — observe the purple community parcel render over Khunti forest land.
