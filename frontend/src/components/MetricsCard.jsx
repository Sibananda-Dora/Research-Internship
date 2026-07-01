import React from 'react';
import { TrendingUp, AlertTriangle, CloudSun, ShieldAlert } from 'lucide-react';

export default function MetricsCard({ prediction, loading }) {
  if (loading || !prediction) {
    return (
      <div className="metrics-row">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="glass-card skeleton" style={{ height: '120px' }}></div>
        ))}
      </div>
    );
  }

  const {
    predicted_yield,
    failure_probability,
    failure_anomaly,
    confidence_interval,
    active_triggers
  } = prediction;

  const isFailure = failure_anomaly === 1 || failure_probability > 0.5;
  const statusClass = isFailure ? 'failure' : (active_triggers.length > 0 ? 'stress' : 'healthy');
  
  // Choose dominant trigger
  const dominantStress = active_triggers.length > 0 ? active_triggers[0] : 'None (Optimal)';

  return (
    <div className="metrics-row">
      {/* 1. Yield Forecast */}
      <div className="glass-card metric-card info">
        <div className="metric-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <TrendingUp size={14} className="text-cyan" />
          Yield Forecast
        </div>
        <div className="metric-val text-cyan">
          {predicted_yield} <span style={{ fontSize: '1rem', color: 'var(--text-secondary)' }}>Q/Acre</span>
        </div>
        <div className="metric-change text-cyan">
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
          {(failure_probability * 100).toFixed(1)}%
        </div>
        <div className="metric-change text-secondary">
          {isFailure ? 'High anomaly risk detected' : 'Optimal growing condition'}
        </div>
      </div>

      {/* 3. Dominant Biophysical Stress */}
      <div className={`glass-card metric-card ${active_triggers.length > 0 ? 'stress' : 'healthy'}`}>
        <div className="metric-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <CloudSun size={14} className={active_triggers.length > 0 ? 'text-stress' : 'text-healthy'} />
          Active Stress
        </div>
        <div className={`metric-val ${active_triggers.length > 0 ? 'text-stress' : 'text-healthy'}`} style={{ fontSize: '1.45rem', height: '51px', display: 'flex', alignItems: 'center' }}>
          {dominantStress}
        </div>
        <div className="metric-change text-secondary" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {active_triggers.length > 0 ? `${active_triggers.length} stress trigger(s) active` : 'No stress triggers activated'}
        </div>
      </div>

      {/* 4. Monte Carlo Confidence */}
      <div className="glass-card metric-card info">
        <div className="metric-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <AlertTriangle size={14} className="text-cyan" />
          Confidence (90%)
        </div>
        <div className="metric-val text-cyan" style={{ fontSize: '1.65rem', height: '51px', display: 'flex', alignItems: 'center' }}>
          {confidence_interval?.lower?.toFixed(2) ?? '?'} - {confidence_interval?.upper?.toFixed(2) ?? '?'}
        </div>
        <div className="metric-change text-secondary">
          Monte Carlo uncertainty bounds
        </div>
      </div>
    </div>
  );
}
