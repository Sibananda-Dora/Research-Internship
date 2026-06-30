import React, { useState, useMemo, useCallback, useRef, useEffect } from 'react';
import { MapContainer, TileLayer, GeoJSON, ZoomControl, Marker, Popup, useMapEvents, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { odishaGeoJSON } from '../data/odishaGeoJSON';

const STATUS_COLORS = {
  healthy: '#10b981',
  stress: '#f59e0b',
  failure: '#ef4444',
  info: '#06b6d4'
};

const TILE_LAYERS = {
  satellite: {
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: '&copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
    label: 'Satellite'
  },
  osm: {
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    label: 'Street Map'
  }
};

const coordMarkerIcon = L.divIcon({
  className: 'coord-marker-icon',
  html: `<div style="
    width: 32px; height: 32px;
    background: radial-gradient(circle, #06b6d4 40%, rgba(6,182,212,0.2) 70%);
    border: 3px solid #fff;
    border-radius: 50%;
    box-shadow: 0 0 20px rgba(6,182,212,0.8), 0 0 60px rgba(6,182,212,0.2);
    animation: coord-pulse 2s ease-in-out infinite;
  "></div>`,
  iconSize: [32, 32],
  iconAnchor: [16, 16]
});

function pointInPolygon(lat, lng, coords) {
  let inside = false;
  const rings = coords[0] && Array.isArray(coords[0][0])
    ? coords
    : [coords];
  for (const ring of rings) {
    const pts = ring[0];
    for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
      const xi = pts[i][0], yi = pts[i][1];
      const xj = pts[j][0], yj = pts[j][1];
      if ((yi > lng) !== (yj > lng) && lat < (xj - xi) * (lng - yi) / (yj - yi) + xi) {
        inside = !inside;
      }
    }
  }
  return inside;
}

function findDistrictAtPoint(latlng, geoData) {
  if (!geoData?.features) return null;
  for (const f of geoData.features) {
    const coords = f.geometry.coordinates;
    if (pointInPolygon(latlng.lat, latlng.lng, coords)) {
      return f.properties.name;
    }
  }
  return null;
}

function MapClickHandler({ enabled, onCoordinateSelect, onSelectDistrict, geoData }) {
  useMapEvents({
    click(e) {
      if (enabled) {
        onCoordinateSelect({
          lat: parseFloat(e.latlng.lat.toFixed(4)),
          lng: parseFloat(e.latlng.lng.toFixed(4))
        });
      } else if (onSelectDistrict && geoData) {
        const name = findDistrictAtPoint(e.latlng, geoData);
        if (name) onSelectDistrict(name);
      }
    }
  });
  return null;
}

function FlyToDistrict({ selectedDistrict, geoData }) {
  const map = useMap();
  useEffect(() => {
    if (!selectedDistrict || !geoData?.features) return;
    const feature = geoData.features.find(
      f => f.properties.name?.toLowerCase() === selectedDistrict.toLowerCase()
    );
    if (feature) {
      const layer = L.geoJSON(feature);
      const bounds = layer.getBounds();
      if (bounds.isValid()) {
        map.flyToBounds(bounds, { padding: [40, 40], maxZoom: 10, duration: 0.8 });
      }
    }
  }, [selectedDistrict, geoData, map]);
  return null;
}

function FlyToCoordinate({ coordinate }) {
  const map = useMap();
  useEffect(() => {
    if (!coordinate) return;
    map.flyTo([coordinate.lat, coordinate.lng], 16, { duration: 0.8 });
  }, [coordinate, map]);
  return null;
}

function NominatimSearch({ onResult }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [open, setOpen] = useState(false);
  const timerRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    const handle = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handle);
    return () => document.removeEventListener('mousedown', handle);
  }, []);

  const search = useCallback((val) => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (!val || val.length < 3) {
      setResults([]);
      setOpen(false);
      return;
    }
    timerRef.current = setTimeout(async () => {
      try {
        const resp = await fetch(
          `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(val)}+Odisha&format=json&limit=5&countrycodes=IN`
        );
        const data = await resp.json();
        setResults(data);
        setOpen(data.length > 0);
      } catch {
        setResults([]);
      }
    }, 400);
  }, []);

  const select = useCallback((item) => {
    onResult({ lat: parseFloat(item.lat), lng: parseFloat(item.lon), label: item.display_name });
    setQuery(item.display_name.split(',')[0]);
    setOpen(false);
    setResults([]);
  }, [onResult]);

  return (
    <div ref={containerRef} style={{ position: 'relative', width: '100%' }}>
      <div style={{
        display: 'flex', gap: '6px', background: 'rgba(17,19,24,0.85)',
        backdropFilter: 'blur(8px)', borderRadius: '10px',
        border: '1px solid rgba(255,255,255,0.12)', padding: '6px 10px'
      }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" strokeWidth="2" style={{ flexShrink: 0, marginTop: '4px' }}>
          <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" />
        </svg>
        <input
          value={query}
          onChange={(e) => { setQuery(e.target.value); search(e.target.value); }}
          placeholder="Search village or district..."
          style={{
            flex: 1, background: 'transparent', border: 'none', color: '#f3f4f6',
            outline: 'none', fontSize: '0.85rem', fontFamily: 'Inter, sans-serif'
          }}
        />
      </div>
      {open && (
        <div style={{
          position: 'absolute', top: '100%', left: 0, right: 0, marginTop: '4px',
          background: 'rgba(17,19,24,0.95)', backdropFilter: 'blur(8px)',
          borderRadius: '10px', border: '1px solid rgba(255,255,255,0.1)',
          zIndex: 1000, overflow: 'hidden'
        }}>
          {results.map((item, i) => (
            <div key={i} onClick={() => select(item)} style={{
              padding: '8px 12px', cursor: 'pointer', fontSize: '0.8rem',
              color: '#d1d5db', borderBottom: i < results.length - 1 ? '1px solid rgba(255,255,255,0.05)' : 'none',
              transition: 'background 0.15s'
            }}
              onMouseEnter={(e) => e.target.style.background = 'rgba(6,182,212,0.1)'}
              onMouseLeave={(e) => e.target.style.background = 'transparent'}
            >
              {item.display_name.split(',').slice(0, 3).join(', ')}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function OdishaGISMap({ 
  selectedDistrict, 
  onSelectDistrict, 
  districtStatus = {},
  coordinateMode = false,
  selectedCoordinate = null,
  onCoordinateSelect = () => {},
  onToggleCoordinateMode = () => {}
}) {
  const [tileLayer, setTileLayer] = useState('satellite');
  const geoJsonRef = useRef(null);
  
  const ODISHA_CENTER = [20.5, 84.4];
  const DEFAULT_ZOOM = 8;

  const getStyle = useCallback((feature) => {
    const name = feature.properties.name;
    const status = districtStatus[name] || 'info';
    const color = STATUS_COLORS[status];
    const isSelected = selectedDistrict?.toLowerCase() === name?.toLowerCase();
    return {
      fillColor: color,
      fillOpacity: coordinateMode ? 0.12 : (isSelected ? 0.55 : 0.25),
      color: isSelected && !coordinateMode ? '#ffffff' : 'rgba(255, 255, 255, 0.45)',
      weight: isSelected && !coordinateMode ? 3 : 1.5,
      className: 'district-polygon'
    };
  }, [selectedDistrict, districtStatus, coordinateMode]);

  const onEachFeature = useCallback((feature, layer) => {
    const name = feature.properties.name;
    const status = districtStatus[name] || 'info';
    const color = STATUS_COLORS[status];
    layer.bindTooltip(
      `<div style="background:#111318;color:#fff;padding:4px 8px;border:1px solid rgba(255,255,255,0.1);border-radius:4px;">
        <strong>${name}</strong>
        <div style="color:${color};font-size:0.8rem;margin-top:2px;">
          Status: ${status.toUpperCase()}
        </div>
      </div>`,
      { direction: 'top', offset: [0, -10], opacity: 0.95 }
    );
    layer.on('mouseover', () => {
      layer.setStyle({ fillOpacity: 0.5, weight: 2.5, color: '#ffffff' });
      layer.bringToFront();
    });
    layer.on('mouseout', () => {
      const isSelected = selectedDistrict?.toLowerCase() === name?.toLowerCase();
      layer.setStyle({
        fillOpacity: isSelected ? 0.55 : 0.25,
        weight: isSelected ? 3 : 1.5,
        color: isSelected ? '#ffffff' : 'rgba(255, 255, 255, 0.45)'
      });
    });
  }, [selectedDistrict, districtStatus]);

  const geoJsonKey = useMemo(() => {
    return `${selectedDistrict}-${coordinateMode}-${tileLayer}-${JSON.stringify(districtStatus)}`;
  }, [selectedDistrict, districtStatus, coordinateMode, tileLayer]);

  const currentTile = TILE_LAYERS[tileLayer];

  const handleNominatimResult = useCallback((coord) => {
    onCoordinateSelect(coord);
  }, [onCoordinateSelect]);

  if (!odishaGeoJSON?.features) {
    return (
      <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p style={{ color: 'var(--text-muted)' }}>Loading GIS data...</p>
      </div>
    );
  }

  return (
    <div className="map-container-inner" style={{ width: '100%', height: '100%', position: 'relative' }}>
      {/* Top toolbar */}
      <div style={{
        position: 'absolute', top: '12px', left: '12px', right: '12px',
        display: 'flex', gap: '8px', alignItems: 'center', zIndex: 500
      }}>
        <div style={{ flex: 1, maxWidth: '360px' }}>
          <NominatimSearch onResult={handleNominatimResult} />
        </div>
        <div style={{ display: 'flex', gap: '4px', background: 'rgba(17,19,24,0.85)', backdropFilter: 'blur(8px)', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.12)', padding: '4px' }}>
          {Object.entries(TILE_LAYERS).map(([key, layer]) => (
            <button key={key} onClick={() => setTileLayer(key)}
              style={{
                padding: '6px 12px', fontSize: '0.75rem', fontFamily: 'Inter, sans-serif',
                background: tileLayer === key ? 'rgba(6,182,212,0.2)' : 'transparent',
                color: tileLayer === key ? '#06b6d4' : '#9ca3af',
                border: tileLayer === key ? '1px solid rgba(6,182,212,0.3)' : '1px solid transparent',
                borderRadius: '8px', cursor: 'pointer', transition: 'all 0.15s',
                fontWeight: 500
              }}
            >{layer.label}</button>
          ))}
        </div>
        <button onClick={onToggleCoordinateMode}
          style={{
            display: 'flex', alignItems: 'center', gap: '6px',
            padding: '6px 12px', fontSize: '0.75rem', fontFamily: 'Inter, sans-serif',
            background: coordinateMode ? 'rgba(6,182,212,0.2)' : 'rgba(17,19,24,0.85)',
            color: coordinateMode ? '#06b6d4' : '#9ca3af',
            border: coordinateMode ? '1px solid rgba(6,182,212,0.3)' : '1px solid rgba(255,255,255,0.12)',
            borderRadius: '10px', cursor: 'pointer', transition: 'all 0.15s',
            backdropFilter: 'blur(8px)', fontWeight: 500, whiteSpace: 'nowrap'
          }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 22s-8-4.5-8-11.8A8 8 0 0112 2a8 8 0 018 8.2c0 7.3-8 11.8-8 11.8z" />
            <circle cx="12" cy="10" r="3" />
          </svg>
          {coordinateMode ? 'Done Pinning' : 'Pin Location'}
        </button>
      </div>

      {/* Coordinate info badge */}
      {selectedCoordinate && (
        <div style={{
          position: 'absolute', bottom: '90px', left: '50%', transform: 'translateX(-50%)',
          background: 'rgba(17,19,24,0.9)', backdropFilter: 'blur(12px)',
          border: '1px solid rgba(255,255,255,0.12)', borderRadius: '14px',
          padding: '10px 18px', display: 'flex', gap: '16px', alignItems: 'center',
          zIndex: 500, boxShadow: '0 4px 24px rgba(0,0,0,0.5)'
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '0.65rem', color: '#9ca3af', fontWeight: 600 }}>LAT</div>
            <div style={{ fontSize: '1rem', color: '#f3f4f6', fontWeight: 600, fontFamily: 'JetBrains Mono, monospace' }}>
              {selectedCoordinate.lat.toFixed(4)}°
            </div>
          </div>
          <div style={{ width: '1px', height: '24px', background: 'rgba(255,255,255,0.1)' }} />
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '0.65rem', color: '#9ca3af', fontWeight: 600 }}>LNG</div>
            <div style={{ fontSize: '1rem', color: '#f3f4f6', fontWeight: 600, fontFamily: 'JetBrains Mono, monospace' }}>
              {selectedCoordinate.lng.toFixed(4)}°
            </div>
          </div>
          <div style={{ width: '1px', height: '24px', background: 'rgba(255,255,255,0.1)' }} />
          <div>
            <div style={{ fontSize: '0.65rem', color: '#9ca3af', fontWeight: 600 }}>PINNED</div>
            <div style={{ fontSize: '0.85rem', color: '#06b6d4', fontWeight: 500 }}>Ready for prediction</div>
          </div>
        </div>
      )}

      <MapContainer 
        center={ODISHA_CENTER} 
        zoom={DEFAULT_ZOOM} 
        zoomControl={false}
        scrollWheelZoom={true}
        style={{ width: '100%', height: '100%', cursor: coordinateMode ? 'crosshair' : 'grab' }}
      >
        <TileLayer
          key={tileLayer}
          attribution={currentTile.attribution}
          url={currentTile.url}
        />
        <ZoomControl position="bottomright" />
        
        <GeoJSON
          key={geoJsonKey}
          ref={geoJsonRef}
          data={odishaGeoJSON}
          style={getStyle}
          onEachFeature={onEachFeature}
        />
        
        <MapClickHandler 
          enabled={coordinateMode} 
          onCoordinateSelect={onCoordinateSelect} 
          onSelectDistrict={onSelectDistrict}
          geoData={odishaGeoJSON}
        />

        {selectedCoordinate && (
          <Marker 
            position={[selectedCoordinate.lat, selectedCoordinate.lng]}
            icon={coordMarkerIcon}
          >
            <Popup>
              <div style={{ color: '#111', fontFamily: 'Inter, sans-serif', fontSize: '0.85rem', minWidth: '140px' }}>
                <strong style={{ color: '#06b6d4' }}>Your Selected Point</strong>
                <div style={{ marginTop: '6px', fontFamily: 'monospace' }}>
                  Lat: {selectedCoordinate.lat.toFixed(4)}<br/>
                  Lng: {selectedCoordinate.lng.toFixed(4)}
                </div>
                <div style={{ marginTop: '6px', fontSize: '0.75rem', color: '#666' }}>
                  A prediction will be run for the nearest district
                </div>
              </div>
            </Popup>
          </Marker>
        )}
        
        {!coordinateMode && (
          <FlyToDistrict selectedDistrict={selectedDistrict} geoData={odishaGeoJSON} />
        )}
        {coordinateMode && selectedCoordinate && (
          <FlyToCoordinate coordinate={selectedCoordinate} />
        )}
      </MapContainer>
    </div>
  );
}
