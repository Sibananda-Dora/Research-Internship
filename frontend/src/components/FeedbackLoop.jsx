import React, { useState, useEffect, useRef } from 'react';
import { Sprout, ArrowRight } from 'lucide-react';

function computeAction(triggers) {
  if (!triggers || triggers.length === 0) {
    return { label: 'General irrigation', modifiers: { precip: 1.0, temp: 0, wetness: 0.08 } };
  }
  const t = triggers[0];
  if (t === 'Drought Stress') {
    return { label: 'Irrigate fields', modifiers: { precip: 1.2, temp: 0, wetness: 0.12 } };
  }
  if (t === 'Thermal Sterility') {
    return { label: 'Apply cooling mist', modifiers: { precip: 1.0, temp: -2, wetness: 0.1 } };
  }
  if (t === 'Flood Stress') {
    return { label: 'Improve drainage', modifiers: { precip: 0.7, temp: 0, wetness: -0.1 } };
  }
  return { label: 'Apply treatment', modifiers: { precip: 1.0, temp: 0, wetness: 0.08 } };
}

export default function FeedbackLoop({ prediction, onSimulate }) {
  const [before, setBefore] = useState(null);
  const [after, setAfter] = useState(null);
  const [showDiff, setShowDiff] = useState(false);
  const prevYieldRef = useRef(null);

  useEffect(() => {
    if (prediction?.predicted_yield != null) {
      if (!before && !showDiff) {
        setBefore({ yield: prediction.predicted_yield, risk: prediction.failure_probability });
        prevYieldRef.current = prediction.predicted_yield;
      }
      if (showDiff) {
        setAfter({ yield: prediction.predicted_yield, risk: prediction.failure_probability });
      }
    }
  }, [prediction]);

  const action = computeAction(prediction?.active_triggers);
  const disabled = !prediction || showDiff;

  const handleAction = () => {
    setBefore({ yield: prediction.predicted_yield, risk: prediction.failure_probability });
    setAfter(null);
    setShowDiff(true);
    onSimulate(action.modifiers);
  };

  const delta = before && after ? after.yield - before.yield : null;

  return (
    <div className="glass-card feedback-loop" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
        <Sprout size={16} className="text-healthy" />
        <h3 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Feedback Loop</h3>
      </div>

      {!disabled ? (
        <button onClick={handleAction} className="send-btn" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', padding: '10px', fontSize: '0.85rem' }}>
          <Sprout size={16} />
          {action.label}
        </button>
      ) : (
        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontStyle: 'italic', textAlign: 'center', padding: '10px' }}>
          Simulating farmer action...
        </div>
      )}

      {disabled && (
        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textAlign: 'center' }}>
          {action.label} applied — re-running prediction
        </div>
      )}

      {showDiff && before && (
        <div className="feedback-diff">
          <div className="feedback-diff-col">
            <span className="feedback-diff-label">Before</span>
            <span className="feedback-diff-val">{before.yield?.toFixed(2)}</span>
            <span className="feedback-diff-sub">Q/Acre</span>
            <span className="feedback-diff-risk" style={{ color: before.risk > 0.5 ? 'var(--status-failure)' : 'var(--status-healthy)' }}>
              Risk {(before.risk * 100).toFixed(0)}%
            </span>
          </div>
          <div className="feedback-diff-arrow">
            <ArrowRight size={20} />
            {delta != null && (
              <span className={`feedback-diff-delta ${delta >= 0 ? 'positive' : 'negative'}`}>
                {delta >= 0 ? '+' : ''}{delta.toFixed(2)}
              </span>
            )}
          </div>
          <div className="feedback-diff-col">
            <span className="feedback-diff-label">After</span>
            <span className="feedback-diff-val">{after ? after.yield?.toFixed(2) : '...'}</span>
            <span className="feedback-diff-sub">Q/Acre</span>
            <span className="feedback-diff-risk" style={{ color: after?.risk > 0.5 ? 'var(--status-failure)' : 'var(--status-healthy)' }}>
              Risk {after ? (after.risk * 100).toFixed(0) : '...'}%
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
