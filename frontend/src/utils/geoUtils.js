/**
 * geoUtils.js — Pure GIS Geospatial utilities for Bhoomi Setu
 * 
 * Provides coordinate format conversion, centroid extraction, and styling rules.
 * Pure JavaScript with zero React dependencies for easy unit testing.
 */

/**
 * Converts GeoJSON polygon coordinates [[lon, lat], ...] to Leaflet [[lat, lon], ...]
 * @param {Object} geometry GeoJSON Polygon geometry object
 * @returns {Array<[number, number]>} Array of [latitude, longitude] pairs for Leaflet
 */
export function geoJsonToLeafletCoords(geometry) {
  if (!geometry || !geometry.coordinates || !geometry.coordinates[0]) {
    return [];
  }
  return geometry.coordinates[0].map(([lon, lat]) => [lat, lon]);
}

/**
 * Computes geographic centroid [average_latitude, average_longitude] of a polygon
 * @param {Array<[number, number]>} coords Array of Leaflet [lat, lon] coordinates
 * @returns {[number, number]} Centroid [lat, lon]
 */
export function getPolygonCenter(coords) {
  if (!coords || coords.length === 0) return [20.5937, 78.9629]; // India geographic center
  const lats = coords.map(c => c[0]);
  const lons = coords.map(c => c[1]);
  const avgLat = lats.reduce((a, b) => a + b, 0) / lats.length;
  const avgLon = lons.reduce((a, b) => a + b, 0) / lons.length;
  return [avgLat, avgLon];
}

/**
 * Determines GIS Polygon styling according to Mirror Confidence Score & Community status
 * @param {Object} parcel Parcel data object
 * @param {boolean} isSelected Whether the parcel is currently selected
 * @returns {Object} Leaflet pathOptions styling dictionary
 */
export function getParcelStyle(parcel, isSelected) {
  const isCommunity = parcel.schema_type === 'community' || parcel.village_key === 'C' || parcel.village === 'Dongri Pahad';
  const score = parcel.mirror_result?.mirror_score ?? 100;

  if (isCommunity) {
    return {
      color: isSelected ? '#c084fc' : '#9333ea', // vibrant purple
      fillColor: isSelected ? '#a855f7' : '#7e22ce',
      fillOpacity: isSelected ? 0.7 : 0.45,
      weight: isSelected ? 3.5 : 2,
      dashArray: '6, 6', // distinct dashed border for collective community tenure
    };
  }

  // Individual parcels color-coded by Mirror Score
  if (score >= 85) {
    // Green: High confidence (sealing eligible)
    return {
      color: isSelected ? '#4ade80' : '#16a34a',
      fillColor: isSelected ? '#22c55e' : '#15803d',
      fillOpacity: isSelected ? 0.75 : 0.45,
      weight: isSelected ? 3.5 : 1.8,
    };
  } else if (score >= 70) {
    // Yellow / Amber: Moderate discrepancy (needs review)
    return {
      color: isSelected ? '#fde047' : '#ca8a04',
      fillColor: isSelected ? '#eab308' : '#a16207',
      fillOpacity: isSelected ? 0.75 : 0.5,
      weight: isSelected ? 3.5 : 2,
    };
  } else {
    // Red: Severe discrepancy / duplicate / collision
    return {
      color: isSelected ? '#f87171' : '#dc2626',
      fillColor: isSelected ? '#ef4444' : '#b91c1c',
      fillOpacity: isSelected ? 0.8 : 0.55,
      weight: isSelected ? 3.5 : 2.2,
    };
  }
}
