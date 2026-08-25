import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Polygon, Popup, Tooltip, useMap } from 'react-leaflet';
import { geoJsonToLeafletCoords, getPolygonCenter, getParcelStyle } from '../utils/geoUtils.js';
function MapRecenter({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (center && center[0] && center[1]) {
      map.setView(center, zoom || 15);
    }
  }, [center, zoom, map]);
  return null;
}
export { geoJsonToLeafletCoords, getPolygonCenter, getParcelStyle };
export default function ParcelMap({
  parcels = [],
  selectedParcel = null,
  onSelectParcel = null,
  height = '400px',
  villageName = 'All',
}) {
  let center = [20.5937, 78.9629];
  let zoom = 14;
  if (selectedParcel?.geometry) {
    const coords = geoJsonToLeafletCoords(selectedParcel.geometry);
    if (coords.length > 0) {
      center = getPolygonCenter(coords);
      zoom = 16;
    }
  } else if (parcels.length > 0 && parcels[0]?.geometry) {
    const coords = geoJsonToLeafletCoords(parcels[0].geometry);
    if (coords.length > 0) {
      center = getPolygonCenter(coords);
      zoom = 14;
    }
  } else {
    if (villageName === 'Rampur Khurd') center = [25.892, 81.981];
    else if (villageName === 'Vellore Nagar') center = [12.916, 79.132];
    else if (villageName === 'Dongri Pahad') center = [23.072, 85.278];
  }
  return (
    <div className="relative rounded-xl overflow-hidden border border-slate-800 shadow-2xl bg-slate-950">
      {}
      <div className="absolute top-3 right-3 z-[1000] bg-slate-900/90 backdrop-blur border border-slate-700/80 rounded-lg p-2.5 text-[11px] shadow-lg space-y-1.5 pointer-events-auto">
        <div className="font-bold text-slate-200 border-b border-slate-800 pb-1 flex items-center justify-between gap-2">
          <span>GIS Cadastral Layer</span>
          <span className="text-[9px] text-emerald-400 font-mono">OpenStreetMap</span>
        </div>
        <div className="space-y-1 font-medium">
          <div className="flex items-center gap-1.5 text-slate-300">
            <span className="w-3 h-3 rounded-sm bg-emerald-500 border border-emerald-400 inline-block" />
            <span>Score ≥ 85 (Sealable)</span>
          </div>
          <div className="flex items-center gap-1.5 text-slate-300">
            <span className="w-3 h-3 rounded-sm bg-amber-500 border border-amber-400 inline-block" />
            <span>Score 70–84 (Mismatch)</span>
          </div>
          <div className="flex items-center gap-1.5 text-slate-300">
            <span className="w-3 h-3 rounded-sm bg-rose-500 border border-rose-400 inline-block" />
            <span>Score &lt; 70 (Critical)</span>
          </div>
          <div className="flex items-center gap-1.5 text-slate-300 border-t border-slate-800/80 pt-1">
            <span className="w-3 h-3 rounded-sm bg-purple-500 border border-purple-300 border-dashed inline-block" />
            <span>FRA Community Land</span>
          </div>
        </div>
      </div>
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height, width: '100%' }}
        className="z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapRecenter center={center} zoom={zoom} />
        {parcels.map((parcel) => {
          if (!parcel.geometry) return null;
          const coords = geoJsonToLeafletCoords(parcel.geometry);
          if (coords.length === 0) return null;
          const isSelected = selectedParcel?.ulpin === parcel.ulpin;
          const style = getParcelStyle(parcel, isSelected);
          const score = parcel.mirror_result?.mirror_score ?? 100;
          const isCommunity = parcel.schema_type === 'community';
          return (
            <Polygon
              key={parcel.ulpin + (isSelected ? '-selected' : '')}
              positions={coords}
              pathOptions={style}
              eventHandlers={{
                click: () => {
                  if (onSelectParcel) onSelectParcel(parcel);
                },
              }}
            >
              <Tooltip sticky>
                <div className="text-xs p-1">
                  <div className="font-bold font-mono text-slate-900">{parcel.ulpin}</div>
                  <div className="text-slate-700 font-semibold">{isCommunity ? parcel.community_entity : parcel.owners?.[0]?.name}</div>
                  <div className="text-slate-600 text-[10px]">
                    Extent: {parcel.area_textual} {parcel.area_unit} ({parcel.mirror_result?.computed_area_ha || 0} Ha)
                  </div>
                  <div className={`font-bold text-[11px] mt-0.5 ${score >= 85 ? 'text-emerald-700' : score >= 70 ? 'text-amber-700' : 'text-red-700'}`}>
                    Mirror Score: {score} / 100
                  </div>
                  {isCommunity && (
                    <div className="text-[10px] text-purple-800 font-bold mt-0.5">
                      ★ Forest Rights Act (Gram Sabha)
                    </div>
                  )}
                </div>
              </Tooltip>
              <Popup>
                <div className="text-xs p-1 space-y-1">
                  <div className="font-bold font-mono text-slate-900">{parcel.ulpin}</div>
                  <div className="text-slate-700 font-semibold">
                    {isCommunity ? parcel.community_entity : parcel.owners?.map(o => o.name).join(', ')}
                  </div>
                  <div className="text-slate-600">
                    Stated Area: <strong>{parcel.area_textual} {parcel.area_unit}</strong>
                  </div>
                  <div className="text-slate-600">
                    Computed Area: <strong>{parcel.mirror_result?.computed_area_ha} Ha</strong>
                  </div>
                  <div className="text-slate-800 font-bold">
                    Mirror Score: <span className={score >= 85 ? 'text-emerald-600' : 'text-red-600'}>{score}/100</span>
                  </div>
                  {parcel.mirror_result?.flags?.length > 0 && (
                    <div className="text-[10px] text-red-600 font-medium">
                      Flags: {parcel.mirror_result.flags.join(', ')}
                    </div>
                  )}
                </div>
              </Popup>
            </Polygon>
          );
        })}
      </MapContainer>
    </div>
  );
}
