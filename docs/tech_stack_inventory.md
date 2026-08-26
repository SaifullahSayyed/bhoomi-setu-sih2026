# Bhoomi Setu — Technical Stack Inventory
**Generated:** August 26, 2026
**Method:** Every version confirmed by running actual import commands and package-lock.json inspection. All import/require statements cross-checked in source code.

---

## 1. Programming Languages

| Language | Role in Bhoomi Setu |
| :--- | :--- |
| **Python 3.14.3** | Backend REST API, Mirror Engine scoring logic, synthetic dataset generation, all benchmark and QA scripts. |
| **Solidity ^0.8.20** | Three on-chain smart contracts (CurtainLedger, AssurancePool, CommunityTenure) running on the Hardhat local EVM. |
| **JavaScript (CommonJS)** | Hardhat config, contract deployment script (scripts/deploy.js), and Hardhat test suite (contracts/test/). |
| **JavaScript/JSX (ES Module)** | React 18 frontend — all views, components, utilities, and the GIS coordinate test suite. |

---

## 2. Backend — Python

### backend/requirements.txt (Core — always installed)

| Package | Pinned in File | Actual Installed | What it does in Bhoomi Setu |
| :--- | :--- | :--- | :--- |
| fastapi | ==0.115.0 | 0.139.0 | REST API framework serving all /parcels/, /seal/, /premium/, /community/, /bank/, /shapefile/ endpoints. |
| uvicorn[standard] | ==0.30.6 | 0.51.0 | ASGI server that runs backend/main.py on http://127.0.0.1:8000. |
| pydantic | ==2.8.2 | 2.13.4 | Request body validation (SealRequest) and structured MirrorResult / MirrorConfig models. |
| web3 | ==7.2.0 | 7.16.0 | Python bridge to the Hardhat local chain; used by web3_bridge.py. Falls back to simulation mode when node is offline. |
| python-multipart | ==0.0.9 | (installed) | Required by FastAPI for multipart/form-data. Not directly used in current endpoints but in FastAPI dependency tree. |
| httpx | ==0.27.2 | 0.28.1 | HTTP client used in web3_bridge.py for simulation-mode responses and in test scripts. |
| shapely | >=2.0.0 | 2.1.2 | Polygon intersection and geometry operations in polygons_overlap() in mirror_engine.py; also used in shapefile_ingest.py. |
| pyproj | >=3.6.0 | 3.7.2 | UTM reprojection in polygon_area_ha() — dynamically selects EPSG:32642-32646 for geodetically accurate hectare area. |

> **Note on pinned vs installed:** The requirements.txt pins are lower bounds from the initial build. Higher installed versions were resolved at install time. No breaking API changes were encountered.

---

### backend/requirements-geo-extended.txt (Optional — Extended Capability / Architecture Demo)

| Package | Pinned in File | Actual Installed | What it does in Bhoomi Setu |
| :--- | :--- | :--- | :--- |
| geopandas | >=1.0.0 | 1.1.4 | Used in backend/shapefile_ingest.py via gpd.read_file() to read .shp files, auto-detect and reproject CRS to EPSG:4326. Also used in scripts/benchmark_spatial_indexing.py for GeoDataFrame.sindex.query (R-Tree spatial index). |
| pyogrio | >=0.9.0 | 0.13.0 | GeoPandas's I/O backend for .shp file reading. Called internally by GeoPandas; not directly imported in Bhoomi Setu source code. |
| pyshp | >=3.0.0 | 3.1.6 | Used in scripts/generate_mock_shapefile.py to write synthetic SVAMITVA drone survey shapefiles (.shp/.dbf/.shx/.prj) via shapefile.Writer. |

**GDAL and Fiona:** Neither gdal nor fiona appear in any requirements file or any import statement anywhere in the codebase. They are NOT used. pyogrio is the I/O engine, not Fiona.

---

## 3. Blockchain — Solidity / Smart Contracts

### Compiler
- **Solidity:** ^0.8.20, compiled with optimizer enabled (runs: 200) via Hardhat.

### Contract Files (contracts/contracts/)

| File | Role |
| :--- | :--- |
| CurtainLedger.sol | Immutable land title registry. Exposes sealParcel() (first-time sealing, requires Mirror Score >= 85) and proposeMutation() (ownership transfer). Stores off-chain data CID, owner identity hash, and Mirror Score on-chain. |
| AssurancePool.sol | Risk-indexed insurance pool. Implements premiumAmount = BASE_RATE x declaredValue x multiplier(score) on-chain. Handles payPremium(), fileClaim(), and processPayout() (30% of pool per claim). |
| CommunityTenure.sol | Multi-signature governance contract for Forest Rights Act community land. Supports proposeAction(), signAction() by Gram Sabha members, and submitOfflineBatch() for offline quorum aggregation. 60% quorum required. |

### JavaScript Toolchain (contracts/package.json + package-lock.json)

| Package | Installed Version | Role |
| :--- | :--- | :--- |
| hardhat | 2.29.1 | EVM development environment. Runs local blockchain node on http://127.0.0.1:8545 (chainId 1337, 25 accounts pre-funded with 10,000 ETH each). |
| @nomicfoundation/hardhat-toolbox | 5.0.0 | Meta-package bundling Ethers.js, Chai, Mocha, Hardhat network helpers, and coverage tooling. |
| ethers | 6.17.0 | JavaScript library for contract interaction and ABI encoding in the test suite and scripts/deploy.js. |
| chai | 4.5.0 | Assertion library (expect(...).to.equal(...) style) used in all 21 Hardhat tests. |
| mocha | 11.8.0 | Test runner that Hardhat uses to execute contracts/test/*.js. |

**Hardhat config specifics:** Optimizer enabled with 200 runs. Local network chainId 1337. 25 test accounts. Artifacts in ./artifacts, cache in ./cache.

---

## 4. Frontend — JavaScript / React

### frontend/package.json Dependencies

| Package | Installed Version | Type | Role |
| :--- | :--- | :--- | :--- |
| react | 18.3.1 | Runtime | Core UI library; all views are React functional components with hooks. |
| react-dom | 18.3.1 | Runtime | DOM rendering — mounts the root React app in index.html. |
| leaflet | 1.9.4 | Runtime | Base interactive map library — tile layer, polygon rendering, zoom/pan. |
| react-leaflet | 4.2.1 | Runtime | React wrapper for Leaflet; provides MapContainer, Polygon, TileLayer, and Tooltip components. |
| lucide-react | 0.439.0 | Runtime | Icon set used throughout the dashboard UI (alert, shield, map-pin, building icons). |
| vite | 5.4.21 | Dev | Build tool and dev server. Builds 1,613 modules in ~27s with the React plugin. |
| @vitejs/plugin-react | 4.3.1 | Dev | Vite plugin enabling JSX transform and React Fast Refresh in dev mode. |
| tailwindcss | 3.4.19 | Dev | Utility-first CSS framework for all UI styling (no custom CSS files). |
| postcss | 8.4.45 | Dev | Required by Tailwind for CSS processing in the Vite pipeline. |
| autoprefixer | 10.4.20 | Dev | PostCSS plugin for cross-browser vendor prefixing (part of Tailwind build setup). |
| @types/react | 18.3.5 | Dev | TypeScript type definitions for React (for editor support; project uses plain JSX, not TypeScript). |
| @types/react-dom | 18.3.0 | Dev | TypeScript type definitions for ReactDOM. |

**Note on i18next:** i18next does NOT appear in package.json. Internationalisation (English + Hindi bilingual strings) is implemented via a hand-rolled translation dictionary in frontend/src/i18n/translations.js using plain useState locale switching — no external i18n library.

### Vite Configuration (vite.config.js)
Non-default settings:
- server.port: 5173 — explicitly pinned.
- server.host: true — exposes dev server on 0.0.0.0 (LAN-accessible).
- Plugin: @vitejs/plugin-react only. No custom aliases, no proxy, no SSR config.

---

## 5. Data & Geospatial Formats

### Data Formats

| Format | Where Used |
| :--- | :--- |
| **JSON** | Primary data store for all 500 synthetic parcels (data/parcels_village_A.json, parcels_village_B.json, parcels_village_C_community.json). Off-chain parcel records in data/off_chain_store/bs<CID>.json. Contract deployments in contracts/deployments.json. |
| **GeoJSON (Polygon)** | Parcel boundary geometries embedded inside each parcel JSON object — {"type":"Polygon","coordinates":[[[lon,lat],...]]}. GeoJSON [lon,lat] order is inverted to Leaflet [lat,lon] order via geoUtils.js. |
| **Esri Shapefile (.shp/.dbf/.shx/.prj)** | Used only in the extended-capability SVAMITVA shapefile demo. Generated by scripts/generate_mock_shapefile.py (via pyshp). Ingested by backend/shapefile_ingest.py (via geopandas + pyogrio). Stored in data/mock_gov_export/. |

### Coordinate Reference Systems

| CRS | Where Applied |
| :--- | :--- |
| **EPSG:4326 (WGS84)** | All parcel GeoJSON geometries (storage, display, GeoJSON standard). Leaflet renders in this CRS. Shapefile output CRS after reprojection. |
| **EPSG:32642-32646 (UTM zones 42N-46N)** | Geodetically accurate area calculation in polygon_area_ha() in mirror_engine.py. UTM zone selected dynamically from parcel centroid longitude via utm_zone_from_lon(). Covers all three villages: UP ~82E (Zone 42N), Tamil Nadu ~79E (Zone 44N), Jharkhand ~85E (Zone 45N). SVAMITVA mock shapefile generated natively in UTM Zone 44N. |

---

## 6. Testing Tools

### Backend — Python

| Tool | Version | What is Tested |
| :--- | :--- | :--- |
| pytest | 8.4.2 | 25 unit tests in tests/test_mirror_engine.py covering: unit conversion, area parsing (Hindi/English RoR), geodetic polygon area, Gini coefficient, MirrorEngine.score_parcel() (clean, mismatch, no-mutation, duplicate ULPIN, benami, floor-at-zero, spatial overlap), sealing threshold boundary, AssurancePool premium math, SchemaHarmonizer encumbrance parsing. |

### Smart Contracts — JavaScript (Mocha/Chai via Hardhat)

| Tool | Version | What is Tested |
| :--- | :--- | :--- |
| Mocha | 11.8.0 | 21 tests in contracts/test/ covering CurtainLedger (seal, score-gate, double-seal prevention, mutation, threshold update, admin access), AssurancePool (premium formula, pool balance, claim filing, payout, access control), CommunityTenure (member registration, batch registration, action proposal, individual voting, quorum auto-execution, offline batch submission, double-vote prevention). |
| Chai | 4.5.0 | Assertion library: expect(...).to.be.revertedWith(...), .to.emit(...), .to.equal(...). |

### Frontend — JavaScript (Node.js built-in test runner)

| Tool | Version | What is Tested |
| :--- | :--- | :--- |
| node:test + node:assert/strict | Built into Node.js 24.13.1 (no external library) | 5 tests in frontend/test/map-coordinates.test.js: GeoJSON [lon,lat] to Leaflet [lat,lon] inversion, real-world placement of all 3 villages within 0.15 degree tolerance, FRA community parcel purple dashed styling, Mirror Score colour-coding (green/yellow/red). Run via: node --test test/map-coordinates.test.js |

---

## 7. Dev Tools & Environment

| Component | Version | Notes |
| :--- | :--- | :--- |
| Python | 3.14.3 | Single environment for backend, scripts, and tests. |
| Node.js | 24.13.1 | Used for both frontend (Vite/React) and contracts (Hardhat). |
| npm | 11.8.0 | Package manager for contracts/ and frontend/. No Yarn or pnpm. |
| pip | System pip (Python 3.14) | Package manager for backend. No poetry, no uv. |
| Platform | Windows (PowerShell) | .bat launchers use %~dp0 for absolute directory resolution. |
| Full version manifest | docs/environment_snapshot.md | Pinned pip freeze and npm ls output produced at audit time. |

---

## 8. One-Paragraph Plain-English Summary

Bhoomi Setu is built in three layers that work together. The backend is written in Python using FastAPI, a modern web framework, and handles all land-record analysis: it runs each parcel through the Mirror Engine — a scoring system that checks for textual mismatches between paper records and satellite-measured plot sizes, duplicate title claims, and suspicious ownership patterns — and produces a 0-to-100 confidence score using geodetically accurate area calculations via the open-source Shapely and pyproj libraries. The blockchain layer consists of three smart contracts written in Solidity and deployed on a local Ethereum test network managed by Hardhat: one contract seals verified land titles on-chain with tamper-proof timestamps, a second calculates and collects risk-adjusted insurance premiums scaled by each parcel's confidence score, and a third manages multi-signature community governance for Forest Rights Act collective land in Jharkhand. The frontend is a React 18 single-page application bundled with Vite, styled with Tailwind CSS, and features a live interactive map powered by Leaflet that renders all 500 parcels at their real geographic coordinates across Uttar Pradesh, Tamil Nadu, and Jharkhand — colour-coded green, yellow, or red by Mirror Score. An optional extended capability, clearly labelled as a beta architecture demo, can additionally ingest government-format Esri Shapefiles from SVAMITVA drone surveys using GeoPandas.

---

*All versions verified by running python -c "import X; print(X.__version__)" and node -e "require('X/package.json').version" on August 26, 2026. Source file cross-references confirmed by Select-String import scanning across backend/, scripts/, and frontend/.*
