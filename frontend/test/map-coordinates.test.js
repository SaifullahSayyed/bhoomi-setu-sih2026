import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  geoJsonToLeafletCoords,
  getPolygonCenter,
  getParcelStyle,
} from '../src/utils/geoUtils.js';
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DATA_DIR = path.resolve(__dirname, '../../data');
const EXPECTED_VILLAGE_CENTERS = {
  A: {
    name: 'Rampur Khurd',
    district: 'Pratapgarh',
    state: 'Uttar Pradesh',
    expectedLat: 25.892,
    expectedLon: 81.981,
    toleranceDeg: 0.15, 
  },
  B: {
    name: 'Vellore Nagar',
    district: 'Vellore',
    state: 'Tamil Nadu',
    expectedLat: 12.916,
    expectedLon: 79.132,
    toleranceDeg: 0.15,
  },
  C: {
    name: 'Dongri Pahad',
    district: 'Khunti',
    state: 'Jharkhand',
    expectedLat: 23.072,
    expectedLon: 85.278,
    toleranceDeg: 0.15,
  },
};
describe('GIS Coordinate Mapping & Leaflet Real-World Placement', () => {
  test('GeoJSON [lon, lat] correctly inverts to Leaflet [lat, lon] format', () => {
    const mockGeoJson = {
      type: 'Polygon',
      coordinates: [[
        [81.9810, 25.8920],
        [81.9830, 25.8920],
        [81.9830, 25.8940],
        [81.9810, 25.8940],
        [81.9810, 25.8920],
      ]],
    };
    const leafletCoords = geoJsonToLeafletCoords(mockGeoJson);
    assert.equal(leafletCoords.length, 5, 'Should preserve all 5 polygon vertices');
    const [firstLat, firstLon] = leafletCoords[0];
    assert.equal(firstLat, 25.8920, 'Latitude must be at index 0 for Leaflet');
    assert.equal(firstLon, 81.9810, 'Longitude must be at index 1 for Leaflet');
    const [centerLat, centerLon] = getPolygonCenter(leafletCoords);
    assert.ok(Math.abs(centerLat - 25.8930) < 0.001, 'Center latitude must match polygon midpoint');
    assert.ok(Math.abs(centerLon - 81.9820) < 0.001, 'Center longitude must match polygon midpoint');
  });
  test('Village A (Rampur Khurd, UP) parcel renders in Pratapgarh, UP', () => {
    const rawData = JSON.parse(
      fs.readFileSync(path.join(DATA_DIR, 'parcels_village_A.json'), 'utf-8')
    );
    const parcel = rawData.parcels[0];
    assert.ok(parcel, 'Village A parcel 0 should exist');
    const leafletCoords = geoJsonToLeafletCoords(parcel.geometry);
    const [lat, lon] = getPolygonCenter(leafletCoords);
    const cfg = EXPECTED_VILLAGE_CENTERS.A;
    assert.ok(
      Math.abs(lat - cfg.expectedLat) < cfg.toleranceDeg,
      `Village A parcel latitude ${lat}° must be near ${cfg.expectedLat}° (Pratapgarh, UP)`
    );
    assert.ok(
      Math.abs(lon - cfg.expectedLon) < cfg.toleranceDeg,
      `Village A parcel longitude ${lon}° must be near ${cfg.expectedLon}° (Pratapgarh, UP)`
    );
    assert.ok(lat >= 8.0 && lat <= 37.0, 'Latitude must be within India bounds');
    assert.ok(lon >= 68.0 && lon <= 97.0, 'Longitude must be within India bounds');
  });
  test('Village B (Vellore Nagar, TN) parcel renders in Vellore, Tamil Nadu', () => {
    const rawData = JSON.parse(
      fs.readFileSync(path.join(DATA_DIR, 'parcels_village_B.json'), 'utf-8')
    );
    const parcel = rawData.parcels[0];
    assert.ok(parcel, 'Village B parcel 0 should exist');
    const leafletCoords = geoJsonToLeafletCoords(parcel.geometry);
    const [lat, lon] = getPolygonCenter(leafletCoords);
    const cfg = EXPECTED_VILLAGE_CENTERS.B;
    assert.ok(
      Math.abs(lat - cfg.expectedLat) < cfg.toleranceDeg,
      `Village B parcel latitude ${lat}° must be near ${cfg.expectedLat}° (Vellore, TN)`
    );
    assert.ok(
      Math.abs(lon - cfg.expectedLon) < cfg.toleranceDeg,
      `Village B parcel longitude ${lon}° must be near ${cfg.expectedLon}° (Vellore, TN)`
    );
  });
  test('Village C (Dongri Pahad, JH) community parcel renders in Khunti, Jharkhand with distinct FRA styling', () => {
    const rawData = JSON.parse(
      fs.readFileSync(path.join(DATA_DIR, 'parcels_village_C_community.json'), 'utf-8')
    );
    const parcel = rawData.parcels[0];
    assert.ok(parcel, 'Village C parcel 0 should exist');
    const leafletCoords = geoJsonToLeafletCoords(parcel.geometry);
    const [lat, lon] = getPolygonCenter(leafletCoords);
    const cfg = EXPECTED_VILLAGE_CENTERS.C;
    assert.ok(
      Math.abs(lat - cfg.expectedLat) < cfg.toleranceDeg,
      `Village C parcel latitude ${lat}° must be near ${cfg.expectedLat}° (Khunti, JH)`
    );
    assert.ok(
      Math.abs(lon - cfg.expectedLon) < cfg.toleranceDeg,
      `Village C parcel longitude ${lon}° must be near ${cfg.expectedLon}° (Khunti, JH)`
    );
    const style = getParcelStyle(parcel, false);
    assert.equal(style.dashArray, '6, 6', 'Community land must render with dashed perimeter');
    assert.ok(style.fillColor.includes('7e22ce') || style.fillColor.includes('a855f7') || style.color.includes('9333ea'), 'Community land must render in purple spectrum');
  });
  test('Color-coding correctly categorizes by Mirror Confidence Score', () => {
    const highConfParcel = { schema_type: 'individual', mirror_result: { mirror_score: 92 } };
    const midConfParcel  = { schema_type: 'individual', mirror_result: { mirror_score: 75 } };
    const lowConfParcel  = { schema_type: 'individual', mirror_result: { mirror_score: 45 } };
    const highStyle = getParcelStyle(highConfParcel, false);
    const midStyle  = getParcelStyle(midConfParcel, false);
    const lowStyle  = getParcelStyle(lowConfParcel, false);
    assert.ok(highStyle.color === '#16a34a' && highStyle.fillColor === '#15803d', 'Score 92 must be green spectrum');
    assert.ok(midStyle.color === '#ca8a04' && midStyle.fillColor === '#a16207', 'Score 75 must be yellow spectrum');
    assert.ok(lowStyle.color === '#dc2626' && lowStyle.fillColor === '#b91c1c', 'Score 45 must be red spectrum');
  });
});
