export function geoJsonToLeafletCoords(geometry) {
  if (!geometry || !geometry.coordinates || !geometry.coordinates[0]) {
    return [];
  }
  return geometry.coordinates[0].map(([lon, lat]) => [lat, lon]);
}
export function getPolygonCenter(coords) {
  if (!coords || coords.length === 0) return [20.5937, 78.9629]; 
  const lats = coords.map(c => c[0]);
  const lons = coords.map(c => c[1]);
  const avgLat = lats.reduce((a, b) => a + b, 0) / lats.length;
  const avgLon = lons.reduce((a, b) => a + b, 0) / lons.length;
  return [avgLat, avgLon];
}
export function getParcelStyle(parcel, isSelected) {
  const isCommunity = parcel.schema_type === 'community' || parcel.village_key === 'C' || parcel.village === 'Dongri Pahad';
  const score = parcel.mirror_result?.mirror_score ?? 100;
  if (isCommunity) {
    return {
      color: isSelected ? '#c084fc' : '#9333ea', 
      fillColor: isSelected ? '#a855f7' : '#7e22ce',
      fillOpacity: isSelected ? 0.7 : 0.45,
      weight: isSelected ? 3.5 : 2,
      dashArray: '6, 6', 
    };
  }
  if (score >= 85) {
    return {
      color: isSelected ? '#4ade80' : '#16a34a',
      fillColor: isSelected ? '#22c55e' : '#15803d',
      fillOpacity: isSelected ? 0.75 : 0.45,
      weight: isSelected ? 3.5 : 1.8,
    };
  } else if (score >= 70) {
    return {
      color: isSelected ? '#fde047' : '#ca8a04',
      fillColor: isSelected ? '#eab308' : '#a16207',
      fillOpacity: isSelected ? 0.75 : 0.5,
      weight: isSelected ? 3.5 : 2,
    };
  } else {
    return {
      color: isSelected ? '#f87171' : '#dc2626',
      fillColor: isSelected ? '#ef4444' : '#b91c1c',
      fillOpacity: isSelected ? 0.8 : 0.55,
      weight: isSelected ? 3.5 : 2.2,
    };
  }
}
