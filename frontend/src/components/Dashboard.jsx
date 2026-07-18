import React from 'react';
import MapCard from './MapCard';
import MetricsCard from './MetricsCard';
import Timeline from './Timeline';
import Heatmap from './Heatmap';
import DSSChat from './DSSChat';
import RealTimeMonitor from './RealTimeMonitor';
import { Sliders } from 'lucide-react';

export default function Dashboard({
  prediction, actualData, loading, telemetry, selectedWeek, onSelectWeek,
  selectedDistrict, selectedYear, selectedSeason,
  onSelectDistrict, coordinateMode, selectedCoordinate,
  onCoordinateSelect, onToggleCoordinateMode,
  modifiers, onModifierChange, simulating, onSimulate, onResetSimulation,
  onChatSimulation,
  showRealtimeMonitor,
}) {
  return (
    <div className="dashboard-grid">
      <div className="main-content-flow">
        <MetricsCard prediction={prediction} actualData={actualData} loading={loading} />

        <RealTimeMonitor
          visible={showRealtimeMonitor}
          coordinate={selectedCoordinate}
          district={selectedDistrict}
          season={selectedSeason}
          year={selectedYear}
        />

        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '20px' }}>
          <MapCard
            selectedDistrict={selectedDistrict}
            onSelectDistrict={onSelectDistrict}
            coordinateMode={coordinateMode}
            selectedCoordinate={selectedCoordinate}
            onCoordinateSelect={onCoordinateSelect}
            onToggleCoordinateMode={onToggleCoordinateMode}
          />

          <Timeline
            selectedWeek={selectedWeek}
            onSelectWeek={onSelectWeek}
            telemetry={telemetry}
            loading={loading}
          />
        </div>

        <Heatmap
          attentionWeights={prediction?.attention_weights}
          telemetry={telemetry}
          selectedWeek={selectedWeek}
          onSelectWeek={onSelectWeek}
          loading={loading}
        />
      </div>

      <div className="sidebar-panel">
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
            <Sliders size={18} className="text-accent" />
            <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>What-If Soil & Climate Simulator</h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Precipitation Offset (mm)</span>
              <span className="text-accent">{modifiers.precip_offset > 0 ? `+${modifiers.precip_offset}` : modifiers.precip_offset} mm</span>
            </div>
            <input type="range" min="-100" max="100" step="5" value={modifiers.precip_offset}
              onChange={(e) => onModifierChange('precip_offset', parseFloat(e.target.value))} />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Temperature Offset</span>
              <span className="text-accent">{modifiers.temp > 0 ? `+${modifiers.temp}` : modifiers.temp} °C</span>
            </div>
            <input type="range" min="-5" max="5" step="0.5" value={modifiers.temp}
              onChange={(e) => onModifierChange('temp', parseFloat(e.target.value))} />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Soil Moisture Offset</span>
              <span className="text-accent">{modifiers.wetness > 0 ? `+${modifiers.wetness}` : modifiers.wetness}</span>
            </div>
            <input type="range" min="-0.3" max="0.3" step="0.05" value={modifiers.wetness}
              onChange={(e) => onModifierChange('wetness', parseFloat(e.target.value))} />
          </div>

          <div style={{ display: 'flex', gap: '10px', marginTop: '6px' }}>
            <button onClick={onSimulate} className="send-btn" style={{ flex: 1, padding: '10px' }}>
              Run Simulation
            </button>
            {simulating && (
              <button onClick={onResetSimulation} className="toggle-btn" style={{ padding: '10px' }}>Reset</button>
            )}
          </div>
        </div>

        <DSSChat
          district={selectedDistrict}
          year={selectedYear}
          season={selectedSeason}
          onRunSimulation={onChatSimulation}
        />
      </div>
    </div>
  );
}
