import React, { useState, useMemo, useRef, useCallback } from 'react';
import { odishaGeoJSON } from '../data/odishaGeoJSON';

/**
 * Minimal Mercator projection for Odisha's bounding box.
 * Converts [longitude, latitude] to SVG [x, y] pixel coordinates.
 */
const ODISHA_BOUNDS = {
  minLon: 81.3, maxLon: 87.6,
  minLat: 17.7, maxLat: 22.6
};
const SVG_WIDTH = 600;
const SVG_HEIGHT = 520;
const PADDING = 20;

function projectPoint(lon, lat) {
  const x = PADDING + ((lon - ODISHA_BOUNDS.minLon) / (ODISHA_BOUNDS.maxLon - ODISHA_BOUNDS.minLon)) * (SVG_WIDTH - 2 * PADDING);
  // Invert Y axis since SVG Y grows downward but lat grows upward
  const y = PADDING + ((ODISHA_BOUNDS.maxLat - lat) / (ODISHA_BOUNDS.maxLat - ODISHA_BOUNDS.minLat)) * (SVG_HEIGHT - 2 * PADDING);
  return [x, y];
}

/**
 * Converts a GeoJSON coordinate ring to an SVG path "d" string.
 */
function ringToPath(ring) {
  return ring.map(([lon, lat], i) => {
    const [x, y] = projectPoint(lon, lat);
    return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ') + ' Z';
}

/**
 * Converts an entire GeoJSON geometry (Polygon or MultiPolygon) to SVG path "d".
 */
function geometryToPath(geometry) {
  if (!geometry) return '';
  if (geometry.type === 'Polygon') {
    // Only use the outer ring (index 0), skip holes
    return ringToPath(geometry.coordinates[0]);
  }
  if (geometry.type === 'MultiPolygon') {
    return geometry.coordinates
      .map(polygon => ringToPath(polygon[0]))
      .join(' ');
  }
  return '';
}

/**
 * Computes the centroid of a GeoJSON geometry for label placement.
 */
function computeCentroid(geometry) {
  if (!geometry) return [0, 0];
  let coords = [];
  if (geometry.type === 'Polygon') {
    coords = geometry.coordinates[0];
  } else if (geometry.type === 'MultiPolygon') {
    // Use the largest polygon for centroid
    let maxLen = 0;
    geometry.coordinates.forEach(poly => {
      if (poly[0].length > maxLen) {
        maxLen = poly[0].length;
        coords = poly[0];
      }
    });
  }
  if (coords.length === 0) return [SVG_WIDTH / 2, SVG_HEIGHT / 2];
  
  let sumX = 0, sumY = 0;
  coords.forEach(([lon, lat]) => {
    const [x, y] = projectPoint(lon, lat);
    sumX += x;
    sumY += y;
  });
  return [sumX / coords.length, sumY / coords.length];
}

const STATUS_COLORS = {
  healthy: 'rgba(16, 185, 129, 0.18)',
  stress: 'rgba(245, 158, 11, 0.18)',
  failure: 'rgba(239, 68, 68, 0.18)',
  info: 'rgba(6, 182, 212, 0.12)'
};

const STATUS_HOVER_COLORS = {
  healthy: 'rgba(16, 185, 129, 0.40)',
  stress: 'rgba(245, 158, 11, 0.40)',
  failure: 'rgba(239, 68, 68, 0.40)',
  info: 'rgba(6, 182, 212, 0.30)'
};

const LEGEND_ITEMS = [
  { label: 'Healthy', color: '#10b981' },
  { label: 'Stress', color: '#f59e0b' },
  { label: 'Failure', color: '#ef4444' },
  { label: 'Selected', color: '#06b6d4' }
];

export default function OdishaSVGMap({ 
  selectedDistrict, 
  onSelectDistrict, 
  districtStatus = {} 
}) {
  const [hoveredDistrict, setHoveredDistrict] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const wrapperRef = useRef(null);

  // Pre-compute paths and centroids
  const districtData = useMemo(() => {
    if (!odishaGeoJSON?.features) return [];
    return odishaGeoJSON.features.map(feature => {
      const name = feature.properties.name;
      const pathD = geometryToPath(feature.geometry);
      const centroid = computeCentroid(feature.geometry);
      return { name, pathD, centroid };
    });
  }, []);

  const handleMouseMove = useCallback((e) => {
    if (!wrapperRef.current) return;
    const rect = wrapperRef.current.getBoundingClientRect();
    setTooltipPos({
      x: e.clientX - rect.left + 12,
      y: e.clientY - rect.top - 8
    });
  }, []);

  if (!odishaGeoJSON?.features || districtData.length === 0) {
    return (
      <div className="odisha-svg-wrapper" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p style={{ color: 'var(--text-muted)' }}>Loading map data...</p>
      </div>
    );
  }

  return (
    <div 
      className="odisha-svg-wrapper" 
      ref={wrapperRef}
      onMouseMove={handleMouseMove}
      style={{ position: 'relative' }}
    >
      <svg 
        viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
        className="odisha-svg-map"
        role="img"
        aria-label="Map of Odisha Districts"
      >
        {/* Background gradient */}
        <defs>
          <radialGradient id="bg-glow" cx="50%" cy="40%" r="60%">
            <stop offset="0%" stopColor="rgba(6, 182, 212, 0.04)" />
            <stop offset="100%" stopColor="rgba(0, 0, 0, 0)" />
          </radialGradient>
        </defs>
        <rect width={SVG_WIDTH} height={SVG_HEIGHT} fill="url(#bg-glow)" />
        
        {/* District polygons */}
        <g>
          {districtData.map(({ name, pathD }) => {
            const status = districtStatus[name] || 'info';
            const isSelected = selectedDistrict?.toLowerCase() === name.toLowerCase();
            const isHovered = hoveredDistrict === name;
            
            return (
              <path
                key={name}
                id={`district-${name.toLowerCase().replace(/\s+/g, '-')}`}
                d={pathD}
                className={`district-path status-${status} ${isSelected ? 'selected' : ''}`}
                style={{
                  fill: isSelected 
                    ? 'rgba(6, 182, 212, 0.30)' 
                    : isHovered 
                      ? STATUS_HOVER_COLORS[status] 
                      : STATUS_COLORS[status]
                }}
                onClick={() => onSelectDistrict(name)}
                onMouseEnter={() => setHoveredDistrict(name)}
                onMouseLeave={() => setHoveredDistrict(null)}
              />
            );
          })}
        </g>

        {/* District name labels */}
        <g>
          {districtData.map(({ name, centroid }) => (
            <text
              key={`label-${name}`}
              x={centroid[0]}
              y={centroid[1]}
              className="district-label"
              style={{
                opacity: selectedDistrict?.toLowerCase() === name.toLowerCase() ? 1 : 0.7,
                fontSize: selectedDistrict?.toLowerCase() === name.toLowerCase() ? '8px' : '6.5px',
                fontWeight: selectedDistrict?.toLowerCase() === name.toLowerCase() ? 700 : 500
              }}
            >
              {name}
            </text>
          ))}
        </g>
      </svg>

      {/* Floating tooltip */}
      {hoveredDistrict && (
        <div 
          className="svg-tooltip"
          style={{
            left: tooltipPos.x,
            top: tooltipPos.y,
            opacity: 1
          }}
        >
          <div style={{ fontWeight: 600, color: '#fff', marginBottom: '2px' }}>
            {hoveredDistrict}
          </div>
          <div style={{ 
            color: districtStatus[hoveredDistrict] === 'healthy' ? '#10b981' 
                 : districtStatus[hoveredDistrict] === 'stress' ? '#f59e0b' 
                 : districtStatus[hoveredDistrict] === 'failure' ? '#ef4444' 
                 : '#06b6d4',
            fontSize: '0.75rem',
            textTransform: 'uppercase',
            letterSpacing: '0.05em'
          }}>
            {(districtStatus[hoveredDistrict] || 'info').toUpperCase()}
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="map-legend">
        {LEGEND_ITEMS.map(({ label, color }) => (
          <div key={label} className="map-legend-item">
            <div className="map-legend-swatch" style={{ background: color }} />
            <span>{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
