import React, { useState } from 'react';
import RealTimeMonitor from './RealTimeMonitor';
import OdishaGISMap from './OdishaGISMap';
import { MapPin, Activity, Crosshair } from 'lucide-react';

export default function SimulatorPage() {
  const [lat, setLat] = useState('20.5');
  const [lng, setLng] = useState('85.8');
  const [isStreaming, setIsStreaming] = useState(false);
  const [coordinateMode, setCoordinateMode] = useState(false);
  const [selectedCoordinate, setSelectedCoordinate] = useState(null);

  // Real-time monitor reflects TODAY's live weather, so drive year/season from
  // the actual date instead of a hardcoded 2024. Kharif window = Jun 15–Oct 31,
  // Rabi = Nov 1–Jun 14 (matches backend season_start logic in main.py).
  const now = new Date();
  const currentYear = now.getFullYear();
  const currentSeason =
    (now >= new Date(currentYear, 5, 15) && now < new Date(currentYear, 10, 1))
      ? 'Kharif'
      : 'Rabi';

  const startStream = (e) => {
    e.preventDefault();
    setIsStreaming(true);
  };

  const handleMapPin = (coord) => {
    setSelectedCoordinate(coord);
    setLat(coord.lat.toFixed(4));
    setLng(coord.lng.toFixed(4));
  };

  const handleTogglePinMode = () => {
    setCoordinateMode(prev => !prev);
  };

  if (isStreaming) {
    return (
      <div style={{ padding: '20px' }}>
        <button 
          onClick={() => setIsStreaming(false)}
          className="toggle-btn"
          style={{ marginBottom: '20px' }}
        >
          ← Back to Setup
        </button>
        <RealTimeMonitor
          visible={true}
          coordinate={{ lat: parseFloat(lat), lng: parseFloat(lng) }}
          district="Unknown"
          season={currentSeason}
          year={currentYear}
        />
      </div>
    );
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: '20px', minHeight: '60vh' }}>
      {/* Left: Setup form */}
      <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px', alignSelf: 'start' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Activity size={24} className="text-accent" />
          <h2 style={{ fontSize: '1.3rem', fontWeight: '600' }}>Simulator Setup</h2>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          Enter coordinates or click the map to pin a location, then start live streaming.
        </p>
        
        <form onSubmit={startStream} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Latitude</label>
            <input 
              type="number" 
              step="0.0001" 
              value={lat} 
              onChange={e => setLat(e.target.value)}
              required
              className="chat-input"
            />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Longitude</label>
            <input 
              type="number" 
              step="0.0001" 
              value={lng} 
              onChange={e => setLng(e.target.value)}
              required
              className="chat-input"
            />
          </div>

          <button 
            type="button"
            onClick={handleTogglePinMode}
            className="toggle-btn"
            style={{ 
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', padding: '10px',
              background: coordinateMode ? 'var(--accent-soft)' : 'rgba(255,255,255,0.04)',
              border: `1px solid ${coordinateMode ? 'var(--accent)' : 'var(--border-color)'}`,
              color: coordinateMode ? 'var(--accent)' : 'var(--text-secondary)'
            }}
          >
            <Crosshair size={16} />
            {coordinateMode ? 'Click map to pin a location' : 'Pin on Map'}
          </button>

          {selectedCoordinate && (
            <div style={{ 
              background: 'var(--accent-soft)', border: '1px solid var(--accent)',
              borderRadius: '8px', padding: '10px 14px', fontSize: '0.85rem',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center'
            }}>
              <span style={{ color: 'var(--text-secondary)' }}>📍 Pinned</span>
              <span style={{ color: 'var(--accent)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                {selectedCoordinate.lat.toFixed(4)}°, {selectedCoordinate.lng.toFixed(4)}°
              </span>
            </div>
          )}
          
          <button type="submit" className="send-btn" style={{ padding: '12px', marginTop: '4px', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}>
            <MapPin size={16} />
            Start Live Streaming
          </button>
        </form>
      </div>

      {/* Right: Map */}
      <div className="glass-card" style={{ padding: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <Crosshair size={16} className="text-accent" />
          <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
            {coordinateMode ? 'Click anywhere on the map to set coordinates' : 'Toggle "Pin on Map" to select a location'}
          </span>
        </div>
        <div style={{ height: 'calc(100vh - 320px)', minHeight: '450px', borderRadius: '10px', overflow: 'hidden' }}>
          <OdishaGISMap 
            selectedDistrict={null}
            onSelectDistrict={() => {}}
            coordinateMode={coordinateMode}
            selectedCoordinate={selectedCoordinate}
            onCoordinateSelect={handleMapPin}
            onToggleCoordinateMode={handleTogglePinMode}
          />
        </div>
      </div>
    </div>
  );
}
