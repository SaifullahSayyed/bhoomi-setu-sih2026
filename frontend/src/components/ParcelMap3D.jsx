import React, { useEffect, useRef, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { 
  Box, 
  Layers, 
  RotateCw, 
  ZoomIn, 
  ZoomOut, 
  Sliders, 
  AlertTriangle, 
  CheckCircle2, 
  HelpCircle, 
  ShieldAlert,
  Compass,
  Maximize2
} from 'lucide-react';

const VILLAGE_PRESETS = {
  ALL: { name: 'All Regions (India Overview)', center: [82.5, 20.5], zoom: 4.8, pitch: 45, bearing: 0 },
  A: { name: 'Village A — Rampur Khurd (UP)', center: [81.9825, 25.8930], zoom: 15.3, pitch: 60, bearing: -25 },
  B: { name: 'Village B — Vellore Nagar (TN)', center: [79.1325, 12.9165], zoom: 15.3, pitch: 60, bearing: 35 },
  C: { name: 'Village C — Dongri Pahad (JH - FRA)', center: [85.2780, 23.0725], zoom: 15.0, pitch: 55, bearing: 15 },
};

const BASEMAP_STYLE = {
  version: 8,
  sources: {
    'carto-voyager': {
      type: 'raster',
      tiles: [
        'https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
        'https://b.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
        'https://c.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png'
      ],
      tileSize: 256,
      attribution: '&copy; <a href="https://carto.com/">CARTO</a>, &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }
  },
  layers: [
    {
      id: 'background',
      type: 'background',
      paint: { 'background-color': '#0f172a' }
    },
    {
      id: 'carto-voyager-layer',
      type: 'raster',
      source: 'carto-voyager',
      minzoom: 0,
      maxzoom: 20,
      paint: {
        'raster-opacity': 0.85,
        'raster-contrast': 0.1
      }
    }
  ]
};

export default function ParcelMap3D({ parcels = [], apiBase }) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const [selectedVillage, setSelectedVillage] = useState('A');
  const [heightScale, setHeightScale] = useState(12);
  const [selectedParcel, setSelectedParcel] = useState(null);
  const [isMapReady, setIsMapReady] = useState(false);
  const [loadError, setLoadError] = useState(null);

  const getParcelColor = (score, schemaType) => {
    if (schemaType === 'community') return '#9333ea';
    if (score >= 85) return '#16a34a';
    if (score >= 70) return '#eab308';
    return '#dc2626';
  };

  const getParcelHeight = (score, schemaType, scale) => {
    if (schemaType === 'community') return 12;
    const rawRisk = Math.max(0, 100 - (score ?? 100));
    return Math.max(4, rawRisk * scale + 4);
  };

  const toGeoJSON = (parcelList, scale) => {
    return {
      type: 'FeatureCollection',
      features: parcelList
        .filter(p => p.geometry && p.geometry.coordinates)
        .map(p => {
          const score = p.mirror_result?.mirror_score ?? 100;
          const schemaType = p.schema_type || 'individual';
          const height = getParcelHeight(score, schemaType, scale);
          const color = getParcelColor(score, schemaType);
          const flags = p.mirror_result?.flags || [];

          return {
            type: 'Feature',
            geometry: p.geometry,
            properties: {
              ulpin: p.ulpin,
              village: p.village || 'Unknown',
              schema_type: schemaType,
              mirror_score: score,
              height: height,
              base_height: 0,
              color: color,
              owner_name: p.owners?.[0]?.name || p.owner_name || 'Anonymous Owner',
              declared_area_ha: p.ror_data?.stated_area_ha || p.declared_area_ha || 0,
              flags_count: flags.length,
              flags_str: flags.join(' | ') || 'None (Clean Title)',
              sealing_eligible: score >= 85,
              raw_parcel: JSON.stringify(p)
            }
          };
        })
    };
  };

  useEffect(() => {
    if (!mapContainerRef.current) return;

    try {
      const canvas = document.createElement('canvas');
      const hasWebGL = Boolean(window.WebGLRenderingContext && (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')));
      if (!hasWebGL) {
        setLoadError('WebGL 3D rendering is not supported by your browser or hardware acceleration is disabled.');
        return;
      }

      const initialPreset = VILLAGE_PRESETS[selectedVillage] || VILLAGE_PRESETS.A;

      const map = new maplibregl.Map({
        container: mapContainerRef.current,
        style: BASEMAP_STYLE,
        center: initialPreset.center,
        zoom: initialPreset.zoom,
        pitch: initialPreset.pitch,
        bearing: initialPreset.bearing,
        antialias: true,
        maxPitch: 75
      });

      map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right');

      map.on('load', () => {
        try {
          const geojsonData = toGeoJSON(parcels, heightScale);

          map.addSource('parcels-3d-source', {
            type: 'geojson',
            data: geojsonData
          });

          map.addLayer({
            id: 'parcels-3d-extrusion',
            type: 'fill-extrusion',
            source: 'parcels-3d-source',
            paint: {
              'fill-extrusion-color': ['get', 'color'],
              'fill-extrusion-height': ['get', 'height'],
              'fill-extrusion-base': ['get', 'base_height'],
              'fill-extrusion-opacity': 0.88
            }
          });

          map.on('click', 'parcels-3d-extrusion', (e) => {
            if (e.features && e.features.length > 0) {
              const props = e.features[0].properties;
              try {
                const fullParcel = JSON.parse(props.raw_parcel);
                setSelectedParcel(fullParcel);
              } catch {
                setSelectedParcel({
                  ulpin: props.ulpin,
                  village: props.village,
                  schema_type: props.schema_type,
                  mirror_result: {
                    mirror_score: props.mirror_score,
                    flags: props.flags_str === 'None (Clean Title)' ? [] : props.flags_str.split(' | ')
                  }
                });
              }
            }
          });

          map.on('mouseenter', 'parcels-3d-extrusion', () => {
            map.getCanvas().style.cursor = 'pointer';
          });
          map.on('mouseleave', 'parcels-3d-extrusion', () => {
            map.getCanvas().style.cursor = '';
          });

          mapInstanceRef.current = map;
          setIsMapReady(true);
        } catch (err) {
          console.error('Error adding 3D extrusion layer:', err);
          setLoadError('Failed to initialize 3D extrusion layer: ' + err.message);
        }
      });

      map.on('error', (e) => {
        if (e && e.error && e.error.message && !e.error.message.includes('tile')) {
          console.warn('MapLibre internal notice:', e.error);
        }
      });

      return () => {
        map.remove();
        mapInstanceRef.current = null;
      };
    } catch (err) {
      console.error('MapLibre init failure:', err);
      setLoadError('MapLibre GL failed to initialize: ' + err.message);
    }
  }, []);

  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !isMapReady) return;

    const source = map.getSource('parcels-3d-source');
    if (source) {
      source.setData(toGeoJSON(parcels, heightScale));
    }
  }, [parcels, heightScale, isMapReady]);

  const flyToVillage = (key) => {
    setSelectedVillage(key);
    const map = mapInstanceRef.current;
    if (!map) return;

    const preset = VILLAGE_PRESETS[key];
    if (preset) {
      map.flyTo({
        center: preset.center,
        zoom: preset.zoom,
        pitch: preset.pitch,
        bearing: preset.bearing,
        duration: 1800,
        essential: true
      });
    }
  };

  const resetCamera = () => {
    const map = mapInstanceRef.current;
    if (!map) return;
    const preset = VILLAGE_PRESETS[selectedVillage] || VILLAGE_PRESETS.A;
    map.flyTo({
      center: preset.center,
      zoom: preset.zoom,
      pitch: preset.pitch,
      bearing: preset.bearing,
      duration: 1200
    });
  };

  if (loadError) {
    return (
      <div className="bg-slate-900/90 border border-amber-800/80 rounded-2xl p-8 text-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-amber-500/20 text-amber-400 flex items-center justify-center mx-auto">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <div className="max-w-md mx-auto space-y-2">
          <h4 className="text-base font-bold text-slate-100">3D Cadastral Visualization Unavailable</h4>
          <p className="text-xs text-slate-400">{loadError}</p>
          <div className="text-[11px] text-amber-300/80 bg-amber-950/40 p-2.5 rounded-lg border border-amber-900/60 font-mono">
            🛡️ <strong>Graceful Degradation:</strong> The core 2D Leaflet cadastral map, Mirror Engine reconciliation, and on-chain blockchain sealing remain 100% operational.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 3D Map Top Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-950/80 p-3.5 rounded-xl border border-slate-800 text-xs">
        {/* Village Camera Presets */}
        <div className="flex items-center gap-2">
          <span className="text-slate-400 font-semibold flex items-center gap-1.5">
            <Compass className="w-3.5 h-3.5 text-cyan-400" /> Focus Village:
          </span>
          <div className="flex flex-wrap gap-1">
            {Object.entries(VILLAGE_PRESETS).map(([k, v]) => (
              <button
                key={k}
                onClick={() => flyToVillage(k)}
                className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition flex items-center gap-1 ${
                  selectedVillage === k
                    ? 'bg-cyan-600 text-white shadow'
                    : 'bg-slate-900 text-slate-300 hover:bg-slate-800 border border-slate-800'
                }`}
              >
                {k === 'ALL' ? 'All' : `Village ${k}`}
              </button>
            ))}
          </div>
        </div>

        {/* Height Extrusion Slider */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-slate-300 font-medium">
            <Sliders className="w-3.5 h-3.5 text-purple-400" />
            <span>3D Risk Height Multiplier:</span>
            <span className="font-mono text-purple-300 font-bold bg-purple-950/60 px-2 py-0.5 rounded border border-purple-800">
              {heightScale}x
            </span>
          </div>
          <input
            type="range"
            min="4"
            max="30"
            step="2"
            value={heightScale}
            onChange={(e) => setHeightScale(Number(e.target.value))}
            className="w-28 accent-purple-500 cursor-pointer"
            title="Adjust vertical risk extrusion scale"
          />

          <button
            onClick={resetCamera}
            className="p-1.5 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded-lg border border-slate-800 transition"
            title="Reset Camera Angle"
          >
            <RotateCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* 3D Map Viewport */}
      <div className="relative w-full h-[520px] rounded-2xl overflow-hidden border border-slate-800 shadow-2xl bg-slate-950">
        <div ref={mapContainerRef} className="w-full h-full" />

        {/* Floating Legend / Height Formula Badge */}
        <div className="absolute top-3 left-3 bg-slate-950/90 backdrop-blur border border-slate-800/90 p-3 rounded-xl shadow-xl text-xs space-y-2 max-w-xs z-10">
          <div className="flex items-center gap-2 font-bold text-slate-200 border-b border-slate-800 pb-1.5">
            <Box className="w-4 h-4 text-cyan-400" />
            <span>3D Risk Elevation Mapping</span>
          </div>

          <div className="space-y-1 text-[11px]">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-emerald-300">
                <span className="w-2.5 h-2.5 rounded bg-emerald-500"></span> Flat Plinth (0–18m)
              </span>
              <span className="font-mono text-slate-400">Score 85–100 (Clean)</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-amber-300">
                <span className="w-2.5 h-2.5 rounded bg-yellow-500"></span> Moderate (180–360m)
              </span>
              <span className="font-mono text-slate-400">Score 70–84 (Minor)</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-rose-300">
                <span className="w-2.5 h-2.5 rounded bg-rose-500"></span> High Tower (&gt;360m)
              </span>
              <span className="font-mono text-slate-400">Score &lt;70 (Severe)</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-purple-300">
                <span className="w-2.5 h-2.5 rounded bg-purple-500"></span> Neutral Base (12m)
              </span>
              <span className="font-mono text-slate-400">FRA Community Land</span>
            </div>
          </div>

          <div className="text-[10px] font-mono text-slate-400 border-t border-slate-800 pt-1.5">
            Formula: <code className="text-cyan-300">H = (100 − Score) × {heightScale}m</code>
          </div>
        </div>

        {/* Floating Quick Hint */}
        <div className="absolute bottom-3 left-3 bg-slate-950/80 backdrop-blur border border-slate-800 px-3 py-1.5 rounded-lg text-[11px] text-slate-400 flex items-center gap-2 z-10">
          <span>💡 <strong>Tip:</strong> Right-click + drag to tilt & rotate 3D view | Left-click parcel to inspect</span>
        </div>

        {/* Selected Parcel Inspector Overlay */}
        {selectedParcel && (
          <div className="absolute bottom-3 right-3 bg-slate-900/95 backdrop-blur border border-slate-700 p-4 rounded-xl shadow-2xl max-w-sm w-full space-y-3 z-10 text-xs animate-in fade-in slide-in-from-bottom-3 duration-200">
            <div className="flex items-start justify-between border-b border-slate-800 pb-2">
              <div>
                <div className="font-mono text-sm font-bold text-cyan-300">{selectedParcel.ulpin}</div>
                <div className="text-[11px] text-slate-400">{selectedParcel.village} • {selectedParcel.schema_type === 'community' ? 'FRA Collective' : 'Individual'}</div>
              </div>
              <button 
                onClick={() => setSelectedParcel(null)}
                className="text-slate-400 hover:text-white text-base leading-none p-1"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800">
                <span className="text-slate-400 block">Mirror Score</span>
                <span className={`text-base font-bold ${
                  (selectedParcel.mirror_result?.mirror_score ?? 100) >= 85 ? 'text-emerald-400' :
                  (selectedParcel.mirror_result?.mirror_score ?? 100) >= 70 ? 'text-amber-400' : 'text-rose-400'
                }`}>
                  {selectedParcel.mirror_result?.mirror_score ?? 100} / 100
                </span>
              </div>

              <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800">
                <span className="text-slate-400 block">3D Risk Height</span>
                <span className="text-base font-mono font-bold text-purple-300">
                  {getParcelHeight(selectedParcel.mirror_result?.mirror_score ?? 100, selectedParcel.schema_type, heightScale)}m
                </span>
              </div>
            </div>

            <div className="space-y-1">
              <span className="text-[10px] text-slate-400 uppercase font-semibold">Detected Flags:</span>
              {(!selectedParcel.mirror_result?.flags || selectedParcel.mirror_result.flags.length === 0) ? (
                <div className="text-emerald-400 flex items-center gap-1 text-[11px] font-medium">
                  <CheckCircle2 className="w-3.5 h-3.5" /> No discrepancies. Clean Title.
                </div>
              ) : (
                <ul className="space-y-1 text-rose-300 text-[11px]">
                  {selectedParcel.mirror_result.flags.map((f, i) => (
                    <li key={i} className="flex items-start gap-1.5 bg-rose-950/40 p-1.5 rounded border border-rose-900/60">
                      <ShieldAlert className="w-3.5 h-3.5 text-rose-400 shrink-0 mt-0.5" />
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
