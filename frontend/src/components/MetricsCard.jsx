import React from 'react';
import { TrendingUp, AlertTriangle, CloudSun, ShieldAlert, Map, Sprout, History } from 'lucide-react';

export default function MetricsCard({ prediction, actualData, loading }) {
  if (loading || (!prediction && !actualData)) {
    return (
      <div className="metrics-row">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="glass-card skeleton" style={{ height: '120px' }}></div>
        ))}
      </div>
    );
  }

  // If actualData is passed, show the Historical APY view
  if (actualData !== undefined) {
    return (
      <div className="metrics-row">
        {/* 1. Actual Yield */}
        <div className="glass-card metric-card info">
          <div className="metric-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <History size={14} className="text-accent" />
            Actual APY Yield
          </div>
          <div className="metric-val text-accent">
            {actualData ? actualData.yield_q_acre.toFixed(2) : 'N/A'} <span style={{ fontSize: '1rem', color: 'var(--text-secondary)' }}>Q/Acre</span>
          </div>
          <div className="metric-change text-accent">
            Recorded ground truth
          </div>
        </div>

        {/* 2. Actual Area */}
        <div className="glass-card metric-card healthy">
          <div className="metric-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Map size={14} className="text-healthy" />
            Cultivated Area
          </div>
          <div className="metric-val text-healthy">
            {actualData ? (actualData.area / 1000).toFixed(1) : 'N/A'} <span style={{ fontSize: '1rem', color: 'var(--text-secondary)' }}>k Hectares</span>
          </div>
          <div className="metric-change text-secondary">
            Total area for season
          </div>
        </div>

        {/* 3. Actual Production */}
        <div className="glass-card metric-card healthy">
          <div className="metric-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Sprout size={14} className="text-healthy" />
            Total Production
          </div>
          <div className="metric-val text-healthy">
            {actualData ? (actualData.production / 1000).toFixed(1) : 'N/A'} <span style={{ fontSize: '1rem', color: 'var(--text-secondary)' }}>k Tonnes</span>
          </div>
          <div className="metric-change text-secondary">
            Gross harvest
          </div>
        </div>

        {/* 4. Model Prediction (for comparison) */}
        <div className="glass-card metric-card stress">
          <div className="metric-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <TrendingUp size={14} className="text-stress" />
            Model Past Prediction
          </div>
          <div className="metric-val text-stress">
            {prediction ? prediction.predicted_yield : 'N/A'} <span style={{ fontSize: '1rem', color: 'var(--text-secondary)' }}>Q/Acre</span>
          </div>
          <div className="metric-change text-secondary">
            Digital Twin retro-forecast
          </div>
        </div>
      </div>
    );
  }

  // Fallback to original metrics if no actualData is passed (e.g. Farmer mode)
  const {
    predicted_yield,
    failure_probability,
    failure_anomaly,
    confidence_interval,
    active_triggers
  } = prediction || {};

  const isFailure = failure_anomaly === 1 || failure_probability > 0.5;
  const statusClass = isFailure ? 'failure' : (active_triggers && active_triggers.length > 0 ? 'stress' : 'healthy');
  
  // Choose dominant trigger
  const dominantStress = active_triggers && active_triggers.length > 0 ? active_triggers[0] : 'None (Optimal)';

  return (
    <div className="metrics-row">
      {/* 1. Yield Forecast */}
      <div className="glass-card metric-card info">
        <div className="metric-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <TrendingUp size={14} className="text-accent" />
          Yield Forecast
        </div>
        <div className="metric-val text-accent">
          {predicted_yield} <span style={{ fontSize: '1rem', color: 'var(--text-secondary)' }}>Q/Acre</span>
        </div>
        <div className="metric-change text-accent">
          Cognitive Analytics prediction
        </div>
      </div>

      {/* 2. Failure Probability */}
      <div className={`glass-card metric-card ${statusClass}`}>
        <div className="metric-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <ShieldAlert size={14} className={isFailure ? 'text-failure' : 'text-healthy'} />
          Failure Probability
        </div>
        <div className={`metric-val ${isFailure ? 'text-failure' : 'text-healthy'}`}>
          {failure_probability ? (failure_probability * 100).toFixed(1) : 0}%
        </div>
        <div className="metric-change text-secondary">
          {isFailure ? 'High anomaly risk detected' : 'Optimal growing condition'}
        </div>
      </div>

      {/* 3. Dominant Biophysical Stress */}
      <div className={`glass-card metric-card ${active_triggers && active_triggers.length > 0 ? 'stress' : 'healthy'}`}>
        <div className="metric-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <CloudSun size={14} className={active_triggers && active_triggers.length > 0 ? 'text-stress' : 'text-healthy'} />
          Active Stress
        </div>
        <div className={`metric-val ${active_triggers && active_triggers.length > 0 ? 'text-stress' : 'text-healthy'}`} style={{ fontSize: '1.45rem', height: '51px', display: 'flex', alignItems: 'center' }}>
          {dominantStress}
        </div>
        <div className="metric-change text-secondary" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {active_triggers && active_triggers.length > 0 ? `${active_triggers.length} stress trigger(s) active` : 'No stress triggers activated'}
        </div>
      </div>

      {/* 4. Monte Carlo Confidence */}
      <div className="glass-card metric-card info">
        <div className="metric-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <AlertTriangle size={14} className="text-accent" />
          Confidence (90%)
        </div>
        <div className="metric-val text-accent" style={{ fontSize: '1.65rem', height: '51px', display: 'flex', alignItems: 'center' }}>
          {confidence_interval?.lower?.toFixed(2) ?? '?'} - {confidence_interval?.upper?.toFixed(2) ?? '?'}
        </div>
        <div className="metric-change text-secondary">
          Monte Carlo uncertainty bounds
        </div>
      </div>
    </div>
  );
}
