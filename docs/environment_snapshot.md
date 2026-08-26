# Bhoomi Setu — Environment Snapshot & Dependency Version Freeze
**Date:** August 26, 2026  
**System Architecture:** Windows-11-10.0.26200-SP0 (x86_64)  
**Git Commit HEAD:** `a0d1b06110b7d1fd921a7c581548efa7e8e8644a`  
**Node.js Version:** `v24.13.1` (NPM: `11.8.0`)  
**Python Version:** `3.14.3` (tags/v3.14.3:323c59a)

---

## 1. 🐍 Python Core Dependencies (`backend/requirements.txt`)

| Package | Pinned Working Version | Purpose |
| :--- | :--- | :--- |
| `fastapi` | `0.139.0` | High-performance asynchronous REST API backend |
| `uvicorn` | `0.51.0` | ASGI production web server |
| `pydantic` | `2.13.4` | Data validation & settings management |
| `web3` | `7.16.0` | Ethereum JSON-RPC blockchain bridge |
| `shapely` | `2.1.2` | Planar geometric operations & metric polygon area calculation |
| `pyproj` | `3.7.2` | Cartographic projections & per-parcel UTM transformation (`EPSG:4326` $\rightarrow$ `EPSG:326XX`) |
| `httpx` | `0.28.1` | HTTP async client & API integration testing |
| `pytest` | `8.4.2` | Test runner framework |

---

## 2. 🗺️ Python Extended Geospatial Dependencies (`backend/requirements-geo-extended.txt`)

| Package | Pinned Working Version | Purpose |
| :--- | :--- | :--- |
| `geopandas` | `1.1.4` | Geospatial DataFrames & vectorized spatial operations |
| `pyogrio` | `0.13.0` | Bundled C-GDAL/GEOS I/O engine for Esri Shapefile reading & writing |
| `pyshp` | `3.1.6` | Pure-Python Shapefile fallback reader/writer |

---

## 3. ⛓️ Smart Contracts Node Dependencies (`contracts/package.json`)

| Package | Installed Version | Purpose |
| :--- | :--- | :--- |
| `hardhat` | `2.29.1` | EVM smart contract compilation, deployment & local node |
| `@nomicfoundation/hardhat-toolbox` | `5.0.0` | Ethers.js v6, Mocha, Chai, Hardhat Network helpers |
| `ethers` | `6.13.5` | Ethereum wallet & smart contract interaction library |

---

## 4. 💻 Frontend Node Dependencies (`frontend/package.json`)

| Package | Installed Version | Purpose |
| :--- | :--- | :--- |
| `react` | `18.3.1` | UI component library |
| `react-dom` | `18.3.1` | React DOM renderer |
| `vite` | `5.4.21` | Frontend build tool & HMR dev server |
| `leaflet` | `1.9.4` | OpenStreetMap interactive cadastral GIS mapping engine |
| `react-leaflet` | `4.2.1` | React bindings for Leaflet maps |
| `tailwindcss` | `3.4.19` | Utility-first CSS styling framework |
| `lucide-react` | `0.439.0` | Minimalist UI vector icons |
| `postcss` | `8.5.26` | CSS transformation pipeline |
| `autoprefixer` | `10.5.4` | Vendor prefix parser |

---

## 5. 🛡️ Verification Signature
All 25 pytest unit tests, 21 Hardhat smart contract tests, and 5 frontend GIS tests pass identically against this exact dependency manifest.
