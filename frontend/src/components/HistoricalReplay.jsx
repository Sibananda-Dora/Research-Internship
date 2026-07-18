import React, { useState, useEffect, useRef, useCallback } from 'react';
import { RefreshCw, Activity, AlertTriangle, Play, Square, Clock, CheckCircle2, X, RotateCcw, TrendingUp, CloudRain, Gauge } from 'lucide-react';
import { ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
const DISTRICTS = ["Angul","Balangir","Balasore","Bargarh","Bhadrak","Boudh","Cuttack","Deogarh","Dhenkanal","Gajapati","Ganjam","Jagatsinghpur","Jajpur","Jharsuguda","Kalahandi","Kandhamal","Kendrapara","Keonjhar","Khurda","Koraput","Malkangiri","Mayurbhanj","Nabarangpur","Nayagarh","Nuapada","Puri","Rayagada","Sambalpur","Sonepur","Sundargarh"];
const YEARS = Array.from({ length: 20 }, (_, i) => 2006 + i);

const SEASON_WINDOWS = {
  Kharif: { start: 'Jun 15', end: 'Sep 06', endYearOffset: 0 },
  Rabi: { start: 'Nov 01', end: 'Jan 23', endYearOffset: 1 }
};

function round(v, d = 1) {
  if (v == null || isNaN(v)) return null;
  const f = Math.pow(10, d);
  return Math.round(v * f) / f;
}

function translateAttentionToWeeks(attentionWeights) {
  if (!Array.isArray(attentionWeights) || attentionWeights.length !== 84) return [];
  const weeks = {};
  for (let d = 0; d < attentionWeights.length; d++) {
    const wk = Math.floor(d / 7);
    weeks[wk] = (weeks[wk] || 0) + attentionWeights[d];
  }
  return Object.entries(weeks)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4)
    .map(([w]) => `W${parseInt(w, 10) + 1}`);
}

// Build a curated, fully-detailed end-of-replay narrative from the final model
// state. Pure + offline so it always renders (synthetic or real telemetry).
function buildReplaySummary({ district, year, season, prediction, telemetry, history }) {
  const win = SEASON_WINDOWS[season] || SEASON_WINDOWS.Kharif;
  const endYear = year + (win.endYearOffset || 0);
  const windowText = `${win.start}, ${year} – ${win.end}, ${endYear}`;

  const sections = [];
  const p = prediction || {};
  const t = telemetry || {};

  // --- Weather aggregates (weekly arrays) ---
  const rain = (t.PRECTOTCORR || []).map(v => v || 0);
  const temp = (t.T2M || []).map(v => v || 0);
  const hum = (t.RH2M || []).map(v => v || 0);
  const soil = (t.GWETROOT || []).map(v => (v || 0) * 100);

  const weeks = rain.length;
  const totalRain = rain.reduce((a, b) => a + b, 0);
  const peakRainWeek = rain.length ? rain.indexOf(Math.max(...rain)) + 1 : null;
  const driestWeek = rain.length ? rain.indexOf(Math.min(...rain)) + 1 : null;
  const hottestWeek = temp.length ? temp.indexOf(Math.max(...temp)) + 1 : null;
  const lowestSoilWeek = soil.length ? soil.indexOf(Math.min(...soil)) + 1 : null;
  const avgTemp = temp.length ? temp.reduce((a, b) => a + b, 0) / temp.length : null;
  const avgHum = hum.length ? hum.reduce((a, b) => a + b, 0) / hum.length : null;
  const maxSoil = soil.length ? Math.max(...soil) : null;
  const minSoil = soil.length ? Math.min(...soil) : null;

  const weatherBullets = [];
  if (weeks) {
    weatherBullets.push(`Seasonal rainfall: ${round(totalRain, 0)} mm across ${weeks} weeks (peak in W${peakRainWeek}, driest in W${driestWeek}).`);
    if (avgTemp != null) weatherBullets.push(`Temperature averaged ${round(avgTemp)}°C, peaking in W${hottestWeek} at ${round(Math.max(...temp))}°C.`);
    if (avgHum != null) weatherBullets.push(`Average humidity ${round(avgHum, 0)}%.`);
    if (soil.length) weatherBullets.push(`Root-zone soil moisture ranged ${round(minSoil)}%–${round(maxSoil)}% (lowest in W${lowestSoilWeek}).`);
  }
  const weatherPara = `Over the ${season} ${year} season in ${district} (${windowText}), the weather ${
    totalRain > 600 ? 'was wet' : totalRain < 250 ? 'was relatively dry' : 'was near-normal'
  }, with ${round(totalRain, 0)} mm of rainfall and temperatures averaging ${round(avgTemp)}°C.`;
  sections.push({ key: 'weather', title: 'Weather Narrative', para: weatherPara, bullets: weatherBullets });

  // --- Yield & Risk ---
  const yieldBullets = [];
  const predYield = p.predicted_yield;
  const failProb = p.failure_probability;
  const startYield = history.length ? history[0].yield : null;
  const endYield = history.length ? history[history.length - 1].yield : predYield;
  const peakRisk = history.length ? Math.max(...history.map(h => h.failureRisk)) : (failProb != null ? failProb * 100 : null);
  const peakRiskWeek = history.length ? history.find(h => h.failureRisk === peakRisk) : null;

  if (predYield != null) yieldBullets.push(`Final predicted yield: ${round(predYield, 2)} Q/Acre.`);
  if (startYield != null && endYield != null) {
    const delta = round(endYield - startYield, 2);
    yieldBullets.push(`Yield estimate moved from ${round(startYield, 2)} → ${round(endYield, 2)} Q/Acre over the replay${delta !== 0 ? ` (${delta > 0 ? '+' : ''}${delta})` : ''}.`);
  }
  if (failProb != null) yieldBullets.push(`Final failure probability: ${(failProb * 100).toFixed(1)}%.`);
  if (peakRisk != null) yieldBullets.push(`Peak failure risk reached ${round(peakRisk, 1)}%${peakRiskWeek ? ` (around ${peakRiskWeek.name})` : ''}.`);
  if (p.failure_anomaly != null) yieldBullets.push(`Failure anomaly score: ${round(p.failure_anomaly, 3)}.`);

  const riskWord = failProb != null ? (failProb > 0.5 ? 'high' : failProb > 0.3 ? 'moderate' : 'low') : 'unknown';
  const yieldPara = `The digital twin projects a ${riskWord} risk outcome for ${district} ${season} ${year}, settling at ${predYield != null ? `${round(predYield, 2)} Q/Acre` : 'an unavailable yield estimate'} with a ${(failProb != null ? (failProb * 100).toFixed(1) : '?')}% failure probability.`;

  // --- Confidence ---
  const confBullets = [];
  if (p.confidence_interval) {
    const ci = p.confidence_interval;
    const lo = ci.lower != null ? ci.lower : ci[0];
    const hi = ci.upper != null ? ci.upper : ci[1];
    if (lo != null && hi != null) confBullets.push(`Yield 95% confidence interval: ${round(lo, 2)} – ${round(hi, 2)} Q/Acre.`);
  }
  if (p.monte_carlo_distribution && Array.isArray(p.monte_carlo_distribution.mean)) {
    // sometimes nested; guard
  }
  if (p.monte_carlo_distribution && typeof p.monte_carlo_distribution === 'object') {
    const mcd = p.monte_carlo_distribution;
    if (mcd.mean != null) confBullets.push(`Monte-Carlo mean: ${round(mcd.mean, 2)} Q/Acre (σ=${mcd.std != null ? round(mcd.std, 2) : 'n/a'}).`);
  } else if (Array.isArray(p.monte_carlo_distribution)) {
    const vals = p.monte_carlo_distribution;
    if (vals.length) {
      const mean = vals.reduce((a, b) => a + b, 0) / vals.length;
      const std = Math.sqrt(vals.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / vals.length);
      confBullets.push(`Monte-Carlo mean: ${round(mean, 2)} Q/Acre (σ=${round(std, 2)}).`);
    }
  }
  if (!confBullets.length) confBullets.push('Model confidence intervals were not returned for this run.');
  sections.push({ key: 'yieldRisk', title: 'Yield & Risk', para: yieldPara, bullets: yieldBullets });
  sections.push({ key: 'confidence', title: 'Model Confidence', para: 'Uncertainty quantification from the ensemble:', bullets: confBullets });

  // --- Triggers / Alerts ---
  const trigBullets = [];
  const details = Array.isArray(p.trigger_details) ? p.trigger_details : [];
  const active = Array.isArray(p.active_triggers) ? p.active_triggers : [];
  if (details.length) {
    details.forEach(d => {
      if (d.active) {
        trigBullets.push(`${d.label || d.id}: ${round(d.current_value, 2)} ${d.unit || ''} vs threshold ${d.threshold} ${d.unit || ''} — severity ${d.severity || 'n/a'}. ${d.description || ''}`.replace(/\s+/g, ' ').trim());
      }
    });
  }
  if (!trigBullets.length && active.length) {
    active.forEach(tg => trigBullets.push(`${tg} was flagged by the model.`));
  }
  const trigPara = active.length
    ? `${active.length} stress trigger(s) fired during the season: ${active.join(', ')}.`
    : 'No stress triggers fired — seasonal conditions stayed within safe operating thresholds.';
  sections.push({ key: 'triggers', title: 'Triggers & Alerts', para: trigPara, bullets: trigBullets });

  // --- Model focus ---
  const topWeeks = translateAttentionToWeeks(p.attention_weights);
  if (topWeeks.length) {
    sections.push({
      key: 'focus',
      title: 'Model Temporal Focus',
      para: `The LSTM attention concentrated most on ${topWeeks.join(' → ')}, indicating these growth stages drove the prediction.`,
      bullets: []
    });
  }

  return {
    district, year, season, windowText,
    overview: `Replay of ${district} — ${season} ${year} (${windowText}). ${weatherPara}`,
    sections
  };
}

function ReplaySummaryModal({ district, year, season, prediction, telemetry, history, onClose, onRunAgain }) {
  const summary = buildReplaySummary({ district, year, season, prediction, telemetry, history });

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  const sectionIcon = {
    weather: CloudRain,
    yieldRisk: TrendingUp,
    confidence: Gauge,
    triggers: AlertTriangle,
    focus: Activity
  };

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(4px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px'
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="glass-card"
        style={{
          width: '100%', maxWidth: '680px', maxHeight: '86vh', overflowY: 'auto',
          background: 'var(--card-bg)', border: '1px solid var(--border-color)',
          borderRadius: '14px', padding: '24px', boxShadow: '0 20px 60px rgba(0,0,0,0.5)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '4px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <CheckCircle2 size={22} style={{ color: 'var(--status-healthy)' }} />
            <h2 style={{ fontSize: '1.15rem', fontWeight: 600, margin: 0 }}>Season Replay Complete</h2>
          </div>
          <button onClick={onClose} aria-label="Close"
            style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '4px' }}>
            <X size={18} />
          </button>
        </div>
        <div style={{ fontSize: '0.85rem', color: 'var(--accent)', marginBottom: '16px', fontFamily: 'var(--font-mono)' }}>
          {district} · {season} · {year} · {summary.windowText}
        </div>

        <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', lineHeight: 1.5, margin: '0 0 18px' }}>
          {summary.overview}
        </p>

        {summary.sections.map((s) => {
          const Icon = sectionIcon[s.key] || Activity;
          return (
            <div key={s.key} style={{ marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <Icon size={15} style={{ color: 'var(--accent)' }} />
                <h3 style={{ fontSize: '0.95rem', fontWeight: 600, margin: 0, color: 'var(--text-primary)' }}>{s.title}</h3>
              </div>
              {s.para && (
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', lineHeight: 1.5, margin: '0 0 6px' }}>{s.para}</p>
              )}
              {s.bullets.length > 0 && (
                <ul style={{ margin: 0, paddingLeft: '18px', color: 'var(--text-secondary)', fontSize: '0.85rem', lineHeight: 1.6 }}>
                  {s.bullets.map((b, i) => <li key={i}>{b}</li>)}
                </ul>
              )}
            </div>
          );
        })}

        <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '20px', borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
          <button onClick={onClose}
            style={{ padding: '9px 16px', fontSize: '0.85rem', borderRadius: '6px', cursor: 'pointer',
              background: 'rgba(255,255,255,0.05)', color: 'var(--text-secondary)', border: '1px solid var(--border-color)' }}>
            Close
          </button>
          <button onClick={onRunAgain}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '9px 16px', fontSize: '0.85rem', borderRadius: '6px', cursor: 'pointer', fontWeight: 600,
              background: 'rgba(34,197,94,0.18)', color: 'var(--status-healthy)', border: '1px solid rgba(34,197,94,0.4)' }}>
            <RotateCcw size={14} /> Run Again
          </button>
        </div>
      </div>
    </div>
  );
}

export default function HistoricalReplay({ onBack }) {
  const [district, setDistrict] = useState('Ganjam');
  const [year, setYear] = useState(2024);
  const [season, setSeason] = useState('Kharif');
  const [speed, setSpeed] = useState(1.5);
  const [sessionId, setSessionId] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [progress, setProgress] = useState(0);
  const [total, setTotal] = useState(0);
  const [prediction, setPrediction] = useState(null);
  const [telemetry, setTelemetry] = useState(null);
  const [history, setHistory] = useState([]);
  const [currentDate, setCurrentDate] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [showSummary, setShowSummary] = useState(false);

  const wsRef = useRef(null);
  const reconnectRef = useRef(null);
  const summaryShownRef = useRef(false);

  const connectWs = useCallback(() => {
    const wsBase = API_BASE_URL.replace(/^http/, 'ws');
    let retries = 0;
    const maxRetries = 10;
    let mounted = true;

    const connect = () => {
      if (!mounted) return;
      if (wsRef.current) wsRef.current.close();
      const ws = new WebSocket(`${wsBase}/ws/farm-stream`);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mounted) { ws.close(); return; }
        setWsConnected(true);
        retries = 0;
      };

      ws.onmessage = (event) => {
        if (!mounted) return;
        try {
          const data = JSON.parse(event.data);
          if (data.type === "REAL_TIME_UPDATE") {
            setPrediction(data.prediction);
            setTelemetry(data.telemetry);
            setCurrentDate(data.date);
            setHistory(prev => {
              const newPoint = {
                name: `${data.date.substring(4,6)}/${data.date.substring(6,8)}`,
                yield: data.prediction.predicted_yield,
                failureRisk: data.prediction.failure_probability * 100
              };
              return [...prev, newPoint];
            });
          } else if (data.type === "REPLAY_COMPLETE") {
            if (!summaryShownRef.current) {
              summaryShownRef.current = true;
              setIsStreaming(false);
              setShowSummary(true);
            }
          }
        } catch {}
      };

      ws.onclose = () => {
        setWsConnected(false);
        if (mounted && retries < maxRetries) {
          const delay = Math.min(1000 * Math.pow(2, retries), 30000);
          retries++;
          reconnectRef.current = setTimeout(connect, delay);
        }
      };

      ws.onerror = () => ws.close();
    };

    connect();
    return () => {
      mounted = false;
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.onerror = null;
        wsRef.current.onmessage = null;
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!isStreaming) return;
    const cleanup = connectWs();
    return cleanup;
  }, [isStreaming, connectWs]);

  useEffect(() => {
    if (!sessionId || !isStreaming) return;
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/stream/status/${sessionId}`);
        if (res.ok) {
          const data = await res.json();
          setProgress(data.progress || 0);
          setTotal(data.total || 0);
          if ((data.status === 'stopped' || (data.total && data.progress >= data.total)) && !summaryShownRef.current) {
            summaryShownRef.current = true;
            setIsStreaming(false);
            setShowSummary(true);
          }
        }
      } catch {}
    }, 2000);
    return () => clearInterval(interval);
  }, [sessionId, isStreaming]);

  const startStream = async () => {
    setHistory([]);
    summaryShownRef.current = false;
    setShowSummary(false);
    try {
      const res = await fetch(`${API_BASE_URL}/api/stream/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ district, year, season, speed })
      });
      if (res.ok) {
        const data = await res.json();
        setSessionId(data.session_id);
        setIsStreaming(true);
      }
    } catch (e) {
      console.error("Failed to start stream", e);
    }
  };

  const stopStream = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/stream/stop`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });
    } catch (e) {
      console.error("Failed to stop stream", e);
    }
    setIsStreaming(false);
    setSessionId(null);
    setProgress(0);
    setTotal(0);
  };

  const changeSpeed = async (s) => {
    setSpeed(s);
    if (sessionId) {
      try {
        await fetch(`${API_BASE_URL}/api/stream/speed`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: sessionId, speed: s })
        });
      } catch {}
    }
  };

  // Full 12-week series. Future/incomplete weeks arrive as null from the
  // backend (season-anchored), so bars/lines simply don't draw there yet.
  // We keep null (not 0) so the axis stays fixed at 12 weeks and the left
  // weeks never resize or re-value as the right side fills in.
  const telemetryData = telemetry ? Array.from({ length: 12 }, (_, i) => ({
    idx: i,
    week: `W${i + 1}`,
    precipitation: telemetry.PRECTOTCORR?.[i] ?? null,
    temperature: telemetry.T2M?.[i] ?? null,
    humidity: telemetry.RH2M?.[i] ?? null,
    soilMoisture: telemetry.GWETROOT?.[i] != null ? telemetry.GWETROOT[i] * 100 : null
  })) : [];

  // Week index within the season (0-based), anchored to the selected replay year
  // so Rabi (Nov 1 -> Jan 23, crossing a year) computes correctly.
  const seasonStartMonth = season === 'Kharif' ? 6 : 11;
  const currentWeekIndex = (() => {
    if (!currentDate) return 0;
    const y = parseInt(currentDate.substring(0, 4), 10);
    const m = parseInt(currentDate.substring(4, 6), 10);
    const d = parseInt(currentDate.substring(6, 8), 10);
    const start = new Date(year, seasonStartMonth - 1, 1);
    const cur = new Date(y, m - 1, d);
    const days = Math.floor((cur - start) / 86400000);
    return Math.max(0, Math.min(11, Math.floor(days / 7)));
  })();

  const hasResults = prediction && telemetry;

  return (
    <>
    <div className="glass-card" style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Clock size={22} className="text-accent" />
          <h2 style={{ fontSize: '1.2rem', fontWeight: 600 }}>Historical Replay</h2>
          {wsConnected && <span style={{ fontSize: '0.7rem', color: 'var(--status-healthy)', background: 'rgba(34,197,94,0.15)', padding: '2px 8px', borderRadius: '4px' }}>WS connected</span>}
        </div>
      </div>

      {/* Controls */}
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'flex-end', marginBottom: '16px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>District</label>
          <select value={district} onChange={e => setDistrict(e.target.value)} disabled={isStreaming} style={{ padding: '8px 12px', borderRadius: '6px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-color)', color: '#fff', fontSize: '0.85rem' }}>
            {DISTRICTS.map(d => <option key={d} value={d}>{d}</option>)}
          </select>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Year</label>
          <select value={year} onChange={e => setYear(parseInt(e.target.value))} disabled={isStreaming} style={{ padding: '8px 12px', borderRadius: '6px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-color)', color: '#fff', fontSize: '0.85rem' }}>
            {YEARS.map(y => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Season</label>
          <select value={season} onChange={e => setSeason(e.target.value)} disabled={isStreaming} style={{ padding: '8px 12px', borderRadius: '6px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-color)', color: '#fff', fontSize: '0.85rem' }}>
            <option value="Kharif">Kharif</option>
            <option value="Rabi">Rabi</option>
          </select>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Speed</label>
          <div style={{ display: 'flex', gap: '4px' }}>
            {[1, 2].map(s => (
              <button key={s} onClick={() => changeSpeed(s)}
                style={{
                  padding: '6px 10px', fontSize: '0.75rem', borderRadius: '4px',
                  background: speed === s ? 'rgba(99,102,241,0.25)' : 'rgba(255,255,255,0.05)',
                  border: `1px solid ${speed === s ? 'rgba(99,102,241,0.5)' : 'rgba(255,255,255,0.1)'}`,
                  color: speed === s ? 'var(--chart-5)' : 'var(--text-secondary)', cursor: 'pointer'
                }}>{s}x</button>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginLeft: 'auto' }}>
          {isStreaming && total > 0 && (
            <span style={{ fontSize: '0.8rem', color: 'var(--status-healthy)' }}>Day {progress}/{total}</span>
          )}
          <button
            onClick={isStreaming ? stopStream : startStream}
            style={{
              display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 16px', fontSize: '0.85rem',
              background: isStreaming ? 'rgba(239,68,68,0.2)' : 'rgba(34,197,94,0.2)',
              color: isStreaming ? 'var(--status-failure)' : 'var(--status-healthy)',
              border: `1px solid ${isStreaming ? 'rgba(239,68,68,0.4)' : 'rgba(34,197,94,0.4)'}`,
              borderRadius: '6px', cursor: 'pointer', fontWeight: 600
            }}
          >
            {isStreaming ? <Square size={14} /> : <Play size={14} />}
            {isStreaming ? 'Stop' : 'Start Simulation'}
          </button>
          {hasResults && !isStreaming && (
            <button onClick={() => { setPrediction(null); setTelemetry(null); setHistory([]); }}
              style={{ padding: '8px 12px', fontSize: '0.8rem', background: 'rgba(255,255,255,0.05)', color: 'var(--text-secondary)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', cursor: 'pointer' }}>
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Results */}
      {!hasResults && (
        <div style={{ padding: '60px 20px', textAlign: 'center', color: 'var(--text-secondary)', background: 'rgba(0,0,0,0.1)', borderRadius: '12px' }}>
          <Activity size={48} style={{ opacity: 0.2, margin: '0 auto 16px' }} />
          <p style={{ fontSize: '1rem' }}>{isStreaming ? 'Reading telemetry data...' : 'Select parameters and click Start to replay historical data day-by-day.'}</p>
        </div>
      )}

      {hasResults && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Top row: Date + Yield + Risk */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
            <div className="glass-card" style={{ background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.2)', padding: '14px' }}>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '6px' }}>Simulated Date</div>
              <div style={{ fontSize: '1.6rem', fontFamily: 'monospace', color: '#fff' }}>
                {currentDate?.substring(0,4)}-{currentDate?.substring(4,6)}-{currentDate?.substring(6,8)}
              </div>
            </div>
            <div className="glass-card" style={{ background: 'rgba(34,197,94,0.05)', border: '1px solid rgba(34,197,94,0.2)', padding: '14px' }}>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '6px' }}>Yield</div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--status-healthy)' }}>
                {prediction.predicted_yield.toFixed(2)} <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 'normal' }}>Q/Acre</span>
              </div>
            </div>
            <div className="glass-card" style={{ borderLeft: `4px solid ${prediction.failure_probability > 0.5 ? 'var(--status-failure)' : 'var(--status-healthy)'}`, padding: '14px' }}>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '6px' }}>Failure Risk</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 'bold', color: prediction.failure_probability > 0.5 ? 'var(--status-failure)' : 'var(--status-healthy)' }}>
                {(prediction.failure_probability * 100).toFixed(1)}%
              </div>
            </div>
          </div>

          {/* Telemetry charts */}
          <div className="glass-card" style={{ background: 'rgba(0,0,0,0.2)', padding: '16px' }}>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Activity size={14} /> Season Progression — Week 1 to {currentWeekIndex + 1}
            </div>
            <div style={{ height: '180px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={telemetryData} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="week" type="category" domain={['W1','W2','W3','W4','W5','W6','W7','W8','W9','W10','W11','W12']} stroke="rgba(255,255,255,0.4)" fontSize={9} tick={{ fill: 'rgba(255,255,255,0.4)' }} />
                  <YAxis yAxisId="precip" stroke="var(--chart-1)" fontSize={10} tick={{ fill: 'var(--chart-1)' }} />
                  <YAxis yAxisId="scaled" orientation="right" stroke="var(--chart-5)" fontSize={10} tick={{ fill: 'var(--chart-5)' }} />
                  <Tooltip contentStyle={{ backgroundColor: 'rgba(15,23,42,0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }} />
                  <Bar yAxisId="precip" dataKey="precipitation" fill="var(--chart-1)" radius={[2,2,0,0]} name="Rainfall (mm)" isAnimationActive={true} animationDuration={400} />
                  <Line yAxisId="scaled" type="monotone" dataKey="temperature" stroke="var(--chart-4)" strokeWidth={2} dot={false} name="Temp (°C)" isAnimationActive={false} connectNulls={false} />
                  <Line yAxisId="scaled" type="monotone" dataKey="humidity" stroke="var(--chart-5)" strokeWidth={2} dot={false} name="Humidity (%)" isAnimationActive={false} connectNulls={false} />
                  <Line yAxisId="scaled" type="monotone" dataKey="soilMoisture" stroke="var(--chart-3)" strokeWidth={2} dot={false} name="Soil Moisture (%)" isAnimationActive={false} connectNulls={false} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Yield trajectory */}
          {history.length > 1 && (
            <div className="glass-card" style={{ background: 'rgba(0,0,0,0.2)', padding: '16px' }}>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Activity size={14} /> Yield & Risk Over Time
              </div>
              <div style={{ height: '160px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={history} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="name" stroke="rgba(255,255,255,0.4)" fontSize={8} tick={{ fill: 'rgba(255,255,255,0.4)' }} interval="preserveStartEnd" minTickGap={24} angle={-35} textAnchor="end" height={36} />
                    <YAxis yAxisId="yield" stroke="var(--chart-2)" fontSize={9} tick={{ fill: 'var(--chart-2)' }} />
                    <YAxis yAxisId="risk" orientation="right" stroke="var(--status-failure)" fontSize={9} tick={{ fill: 'var(--status-failure)' }} />
                    <Tooltip contentStyle={{ backgroundColor: 'rgba(15,23,42,0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }} />
                    <Line yAxisId="yield" type="monotone" dataKey="yield" stroke="var(--chart-2)" strokeWidth={2.5} dot={false} name="Yield" animationDuration={300} isAnimationActive={false} />
                    <Line yAxisId="risk" type="monotone" dataKey="failureRisk" stroke="var(--status-failure)" strokeWidth={2} dot={false} name="Risk %" animationDuration={300} isAnimationActive={false} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Active triggers */}
          {prediction.active_triggers?.length > 0 && (
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              {prediction.active_triggers.map((t, i) => (
                <div key={i} style={{ padding: '8px 14px', borderRadius: '8px', background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)', color: 'var(--status-stress)', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <AlertTriangle size={14} /> {t}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>

    {showSummary && prediction && telemetry && (
      <ReplaySummaryModal
        district={district} year={year} season={season}
        prediction={prediction} telemetry={telemetry} history={history}
        onClose={() => setShowSummary(false)}
        onRunAgain={() => { setShowSummary(false); startStream(); }}
      />
    )}
    </>
  );
}
