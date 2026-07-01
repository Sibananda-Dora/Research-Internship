import React from 'react';
import OdishaGISMap from './OdishaGISMap';
import { Layers, MapPin, Crosshair } from 'lucide-react';

export default function MapCard({ 
  selectedDistrict, 
  onSelectDistrict, 
  coordinateMode,
  selectedCoordinate,
  onCoordinateSelect,
  onToggleCoordinateMode
}) {
  return (
    <div className="glass-card map-card">
      <div className="card-header">
        <h2 className="text-cyan" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '1.1rem' }}>
          <Layers size={18} />
          {coordinateMode 
            ? `Pinpoint: ${selectedCoordinate ? `${selectedCoordinate.lat.toFixed(3)}°N, ${selectedCoordinate.lng.toFixed(3)}°E` : 'Click the map to select your field'}`
            : `District: ${selectedDistrict || 'Select a District'}`
          }
        </h2>
      </div>
      
      <div className="map-container-inner" style={{ height: '480px' }}>
        <OdishaGISMap 
          selectedDistrict={selectedDistrict} 
          onSelectDistrict={onSelectDistrict} 
          coordinateMode={coordinateMode}
          selectedCoordinate={selectedCoordinate}
          onCoordinateSelect={onCoordinateSelect}
          onToggleCoordinateMode={onToggleCoordinateMode}
        />
      </div>
    </div>
  );
}
