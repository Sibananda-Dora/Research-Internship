import React, { useState } from 'react';
import MapCard from './MapCard';
import FeedbackLoop from './FeedbackLoop';
import { ShieldAlert, CloudSun, Droplets, Thermometer } from 'lucide-react';

const PRESET_SCENARIOS = [
  { label: 'Less Rain', icon: '🌤️', modifiers: { precip: 0.5, temp: 0, wetness: -0.15 } },
  { label: 'More Rain', icon: '🌧️', modifiers: { precip: 1.5, temp: 0, wetness: 0.15 } },
  { label: 'Heat Wave', icon: '🔥', modifiers: { precip: 0.8, temp: 3, wetness: -0.1 } },
];

export default function FarmerDashboard({
  prediction, loading, telemetry,
  selectedDistrict, selectedYear, selectedSeason,
  onSelectDistrict, onSelectYear, onSelectSeason,
  coordinateMode, selectedCoordinate,
  onCoordinateSelect, onToggleCoordinateMode,
  onSimulatePreset, onChatSimulation, onSimulate,
}) {
  const [language, setLanguage] = useState('english');

  if (loading || !prediction) {
    return (
      <div className="farmer-loading">
        <div className="farmer-hero-skeleton" />
        <div className="farmer-map-skeleton" />
      </div>
    );
  }

  const isFailure = prediction.failure_anomaly === 1 || prediction.failure_probability > 0.5;
  const isStress = prediction.active_triggers?.length > 0;
  const statusColor = isFailure ? 'var(--status-failure)' : isStress ? 'var(--status-stress)' : 'var(--status-healthy)';
  const statusLabel = isFailure ? 'Crop at Risk' : isStress ? 'Mild Stress Detected' : 'Healthy Crop';
  const statusEmoji = isFailure ? '🔴' : isStress ? '🟡' : '🟢';
  const dominantStress = prediction.active_triggers?.[0] || null;

  const advisoryText = dominantStress
    ? `Your ${selectedDistrict} paddy is experiencing ${dominantStress.toLowerCase()}. ${dominantStress === 'Drought Stress' ? 'Consider irrigating immediately.' : dominantStress === 'Thermal Sterility' ? 'Heat stress may reduce grain filling. Monitor field temperature.' : 'Take preventive measures as advised.'}`
    : `Your ${selectedDistrict} paddy is growing under optimal conditions. Current yield forecast is ${prediction.predicted_yield} Q/Acre.`;

  const handlePresetClick = (modifiers) => {
    onSimulatePreset(modifiers);
  };

  return (
    <div className="farmer-dashboard">
      {/* Hero card — giant yield + traffic light */}
      <div className="farmer-hero" style={{ borderLeftColor: statusColor }}>
        <div className="farmer-hero-status">
          <span className="farmer-status-dot" style={{ background: statusColor }} />
          <span className="farmer-status-emoji">{statusEmoji}</span>
          <span className="farmer-status-label" style={{ color: statusColor }}>{statusLabel}</span>
        </div>
        <div className="farmer-hero-yield">
          <span className="farmer-yield-number" style={{ color: statusColor }}>
            {prediction.predicted_yield}
          </span>
          <span className="farmer-yield-unit">Q/Acre</span>
        </div>
        <p className="farmer-hero-verdict">{advisoryText}</p>
        {prediction.failure_probability > 0 && (
          <div className="farmer-hero-risk">
            <ShieldAlert size={16} />
            Failure risk: {(prediction.failure_probability * 100).toFixed(0)}%
          </div>
        )}
        <FeedbackLoop prediction={prediction} onSimulate={onSimulate} />
      </div>

      {/* Quick presets */}
      <div className="farmer-presets">
        <h4>Quick Simulations</h4>
        <div className="farmer-preset-buttons">
          {PRESET_SCENARIOS.map(s => (
            <button
              key={s.label}
              className="farmer-preset-btn"
              onClick={() => handlePresetClick(s.modifiers)}
            >
              <span className="farmer-preset-icon">{s.icon}</span>
              <span>{s.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Full-screen map */}
      <div className="farmer-map-wrapper">
        <MapCard
          selectedDistrict={selectedDistrict}
          onSelectDistrict={onSelectDistrict}
          coordinateMode={coordinateMode}
          selectedCoordinate={selectedCoordinate}
          onCoordinateSelect={onCoordinateSelect}
          onToggleCoordinateMode={onToggleCoordinateMode}
        />
      </div>

      {/* Simplified controls row */}
      <div className="farmer-controls">
        <select value={selectedDistrict} onChange={(e) => onSelectDistrict(e.target.value)}>
          <option value="">Select District</option>
          {["Angul","Balangir","Balasore","Bargarh","Bhadrak","Boudh","Cuttack","Deogarh","Dhenkanal","Gajapati","Ganjam","Jagatsinghpur","Jajpur","Jharsuguda","Kalahandi","Kandhamal","Kendrapara","Keonjhar","Khurda","Koraput","Malkangiri","Mayurbhanj","Nabarangpur","Nayagarh","Nuapada","Puri","Rayagada","Sambalpur","Sonepur","Sundargarh"].map(d => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
        <select value={selectedSeason} onChange={(e) => onSelectSeason(e.target.value)}>
          <option value="Kharif">Kharif</option>
          <option value="Rabi">Rabi</option>
        </select>
        <select value={selectedYear} onChange={(e) => onSelectYear(parseInt(e.target.value))}>
          {Array.from({ length: 20 }, (_, i) => 2006 + i).map(y => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>
        <button
          className={`farmer-lang-btn ${language === 'odia' ? 'active' : ''}`}
          onClick={() => setLanguage(language === 'english' ? 'odia' : 'english')}
        >
          {language === 'english' ? 'ଓଡ଼ିଆ' : 'English'}
        </button>
      </div>

      {/* Stress indicators */}
      {prediction.active_triggers?.length > 0 && (
        <div className="farmer-stress-bar">
          {prediction.active_triggers.map((t, i) => (
            <div key={i} className="farmer-stress-chip">
              {t === 'Drought Stress' ? <Droplets size={14} /> : <Thermometer size={14} />}
              {t}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
