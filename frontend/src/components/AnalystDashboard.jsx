import React from 'react';
import MapCard from './MapCard';
import MetricsCard from './MetricsCard';
import Timeline from './Timeline';
import Heatmap from './Heatmap';
import DSSChat from './DSSChat';
import FeedbackLoop from './FeedbackLoop';
import { Sliders } from 'lucide-react';

export default function AnalystDashboard({
  prediction, loading, telemetry, selectedWeek, onSelectWeek,
  selectedDistrict, selectedYear, selectedSeason,
  onSelectDistrict, coordinateMode, selectedCoordinate,
  onCoordinateSelect, onToggleCoordinateMode,
  modifiers, onModifierChange, simulating, onSimulate, onResetSimulation,
  onChatSimulation
}) {
  return (
    <div className="dashboard-grid">
      <div className="main-content-flow">
        <MetricsCard prediction={prediction} loading={loading} />

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
            <Sliders size={18} className="text-cyan" />
            <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>What-If Soil & Climate Simulator</h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Precipitation Scaling</span>
              <span className="text-cyan">{(modifiers.precip * 100).toFixed(0)}%</span>
            </div>
            <input type="range" min="0.2" max="2.0" step="0.1" value={modifiers.precip}
              onChange={(e) => onModifierChange('precip', parseFloat(e.target.value))} />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Temperature Offset</span>
              <span className="text-cyan">{modifiers.temp > 0 ? `+${modifiers.temp}` : modifiers.temp} °C</span>
            </div>
            <input type="range" min="-5" max="5" step="0.5" value={modifiers.temp}
              onChange={(e) => onModifierChange('temp', parseFloat(e.target.value))} />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Soil Moisture Offset</span>
              <span className="text-cyan">{modifiers.wetness > 0 ? `+${modifiers.wetness}` : modifiers.wetness}</span>
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

        <FeedbackLoop
          prediction={prediction}
          onSimulate={onSimulate}
        />
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
