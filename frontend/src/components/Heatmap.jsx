import React, { useMemo } from 'react';
import { Eye } from 'lucide-react';

export default function Heatmap({ 
  attentionWeights, 
  telemetry, 
  onSelectWeek, 
  selectedWeek, 
  loading 
}) {
  if (loading || !attentionWeights || !telemetry) {
    return (
      <div className="glass-card skeleton" style={{ height: '140px' }}></div>
    );
  }

  // Aggregate 84 daily weights into 12 weekly weights
  const weeklyWeights = useMemo(() => {
    if (attentionWeights.length <= 12) return attentionWeights;
    const weekly = [];
    for (let w = 0; w < 12; w++) {
      const start = w * 7;
      const end = Math.min(start + 7, attentionWeights.length);
      const chunk = attentionWeights.slice(start, end);
      weekly.push(chunk.reduce((a, b) => a + b, 0) / chunk.length);
    }
    return weekly;
  }, [attentionWeights]);

  // Helper to determine week-specific biophysical stress indicators
  const getWeekStresses = (idx) => {
    const stresses = [];
    const p = telemetry.PRECTOTCORR?.[idx] ?? 0;
    const t = telemetry.T2M?.[idx] ?? 0;
    const r = telemetry.RH2M?.[idx] ?? 0;
    const g = telemetry.GWETROOT?.[idx] ?? 0;

    if (g < 0.35) stresses.push("Drought Risk (Low Soil Wetness)");
    if (p > 200) stresses.push("Submergence Risk (Heavy Rainfall)");
    if (t > 34.0) stresses.push("Thermal Sterility Risk (High Temp)");
    if (r > 85.0 && t >= 25.0 && t <= 30.0) stresses.push("Pest/Pathogen Risk");
    
    return stresses;
  };

  // Find max weight to normalize cell scaling/opacity
  const maxWeight = Math.max(...weeklyWeights, 0.01);

  return (
    <div className="glass-card">
      <div className="card-header" style={{ marginBottom: '10px' }}>
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px' }} className="text-accent">
          <Eye size={18} />
          LSTM Temporal Attention Weights (Explainable AI)
        </h2>
      </div>
      
      <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '14px' }}>
        Higher opacity indicates weeks that the Deep Learning model focused on to predict crop yields and detect failure vectors. Click cells to focus the timeline.
      </p>

      <div className="attention-heatmap">
        {weeklyWeights.map((weight, idx) => {
          const weekNum = idx + 1;
          const isSelected = selectedWeek === weekNum;
          
          // Compute opacity relative to the highest weight
          const relativeWeight = weight / maxWeight;
          const baseColor = isSelected ? 'rgba(56, 189, 248,' : 'rgba(56, 189, 248,';
          const bgOpacity = 0.1 + relativeWeight * 0.85; // Map from 0.1 to 0.95 opacity
          
          const stresses = getWeekStresses(idx);
          const cellColor = stresses.length > 0 && stresses.some(s => s.includes("Drought") || s.includes("Sterility")) 
            ? `rgba(245, 158, 11, ${bgOpacity})` 
            : stresses.length > 0 && stresses.some(s => s.includes("Submergence"))
            ? `rgba(239, 68, 68, ${bgOpacity})`
            : `rgba(56, 189, 248, ${bgOpacity})`;

          return (
            <div
              key={idx}
              className={`heatmap-cell ${isSelected ? 'active-cell' : ''}`}
              style={{ 
                backgroundColor: cellColor, 
                border: isSelected ? '2px solid #ffffff' : '1px solid rgba(255,255,255,0.08)',
                color: bgOpacity > 0.5 ? '#000000' : '#ffffff',
                fontWeight: isSelected ? '700' : '500'
              }}
              onClick={() => onSelectWeek(weekNum)}
            >
              <div>W{weekNum}</div>
              <div 
                className="heatmap-label" 
                style={{ 
                  color: bgOpacity > 0.5 ? 'rgba(0,0,0,0.7)' : 'rgba(255,255,255,0.6)',
                  fontSize: '0.6rem'
                }}
              >
                {(weight * 100).toFixed(1)}%
              </div>
              
              {/* Tooltip helper (using browser title for simple, light overlay) */}
              <title>
                {`Week ${weekNum} LSTM Weight: ${(weight * 100).toFixed(2)}%\n`}
                {`Precipitation: ${(telemetry.PRECTOTCORR?.[idx] ?? 0).toFixed(1)} mm\n`}
                {`Temperature: ${(telemetry.T2M?.[idx] ?? 0).toFixed(1)} °C\n`}
                {`Soil Wetness: ${((telemetry.GWETROOT?.[idx] ?? 0) * 100).toFixed(1)}%\n`}
                {stresses.length > 0 ? `Alerts:\n- ${stresses.join('\n- ')}` : 'Conditions: Stable'}
              </title>
            </div>
          );
        })}
      </div>
      
      <div style={{ display: 'flex', gap: '16px', marginTop: '12px', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ display: 'inline-block', width: '12px', height: '12px', borderRadius: '3px', background: 'rgba(56, 189, 248, 0.8)' }}></span>
          Model Attention Focus
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ display: 'inline-block', width: '12px', height: '12px', borderRadius: '3px', background: 'rgba(245, 158, 11, 0.8)' }}></span>
          Thermal / Dry Stress (Soil & Temp)
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ display: 'inline-block', width: '12px', height: '12px', borderRadius: '3px', background: 'rgba(239, 68, 68, 0.8)' }}></span>
          Excess Water Stress (Submergence)
        </div>
      </div>
    </div>
  );
}
