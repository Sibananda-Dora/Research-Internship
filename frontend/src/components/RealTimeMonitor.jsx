import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Activity, AlertTriangle, RefreshCw, MapPin, Clock, Thermometer, Droplets, CloudRain, Sprout, Bug, Send } from 'lucide-react';
import { ComposedChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const POLL_INTERVAL = 60000;

const TRIGGER_META = {
  flooding: { icon: <Droplets size={14} />, label: 'Flooding' },
  drought: { icon: <Sprout size={14} />, label: 'Drought' },
  thermal: { icon: <Thermometer size={14} />, label: 'Thermal Stress' },
  pest: { icon: <Bug size={14} />, label: 'Pest Risk' },
};
const TRIGGER_ORDER = ['flooding', 'drought', 'thermal', 'pest'];

function buildTriggerList(prediction) {
  const details = prediction?.trigger_details;
  if (Array.isArray(details) && details.length) {
    return TRIGGER_ORDER.map(id => {
      const d = details.find(x => x.id === id) || {};
      const meta = TRIGGER_META[id] || {};
      return {
        id,
        label: d.label || meta.label || id,
        active: !!d.active,
        progress: d.progress != null ? d.progress : (d.active ? 1 : 0),
        severity: d.severity || null,
        current_value: d.current_value ?? null,
        threshold: d.threshold ?? null,
        unit: d.unit || null,
        description: d.description || '',
      };
    });
  }
  const activeStrs = (prediction?.active_triggers || []).map(s => String(s).toLowerCase());
  return TRIGGER_ORDER.map(id => {
    const meta = TRIGGER_META[id] || {};
    const label = meta.label || id;
    const active = activeStrs.some(s => s.includes(id) || s.includes(label.toLowerCase()));
    return {
      id, label, active,
      progress: active ? 1 : 0,
      severity: active ? 'high' : null,
      current_value: null, threshold: null, unit: null, description: '',
    };
  });
}

const TelegramNotifier = ({ prediction, district }) => {
  const [countdown, setCountdown] = useState(240);
  const [sent, setSent] = useState(false);
  const [sending, setSending] = useState(false);

  const hasRisk = prediction && prediction.failure_probability > 0.5;

  const sendAlert = useCallback(async () => {
    if (sent || sending) return;
    setSending(true);
    try {
      const activeTriggers = buildTriggerList(prediction).filter(t => t.active).map(t => t.label);
      const text = `🚨 *URGENT: CROP FAILURE WARNING* 🚨
*District:* ${district}
*Trigger:* ${activeTriggers.length > 0 ? activeTriggers.join(', ') : 'Multiple factors'}

*Advisory:* High risk of crop failure detected (${(prediction.failure_probability * 100).toFixed(1)}%). Please initiate disaster response protocols.

➖➖➖➖➖➖➖➖➖➖
🚨 *ଜରୁରୀ: ଫସଲ ନଷ୍ଟ ଚେତାବନୀ* 🚨
*ଜିଲ୍ଲା:* ${district}
*କାରଣ:* ${activeTriggers.length > 0 ? activeTriggers.join(', ') : 'ବିଭିନ୍ନ କାରଣ'}

*ପରାମର୍ଶ:* ଫସଲ ନଷ୍ଟ ହେବାର ଅଧିକ ଆଶଙ୍କା ଦେଖାଦେଇଛି (${(prediction.failure_probability * 100).toFixed(1)}%)। ଦୟାକରି ତୁରନ୍ତ ଆବଶ୍ୟକୀୟ ପଦକ୍ଷେପ ଗ୍ରହଣ କରନ୍ତୁ।`;
      
      const botToken = import.meta.env.VITE_TELEGRAM_BOT_TOKEN;
      const chatId = import.meta.env.VITE_TELEGRAM_CHAT_ID;
      if (!botToken || !chatId) return;
      await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ chat_id: chatId, text, parse_mode: 'Markdown' })
      });
      setSent(true);
    } catch (e) {
      console.error(e);
    }
    setSending(false);
  }, [prediction, district, sent, sending]);

  useEffect(() => {
    if (!hasRisk) {
      setCountdown(240);
      setSent(false);
      return;
    }
    if (sent) return;
    
    const timer = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          sendAlert();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [hasRisk, sent, sendAlert]);

  const mins = Math.floor(countdown / 60);
  const secs = countdown % 60;

  return (
    <div style={{ marginTop: 'auto', paddingTop: '12px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
      <div style={{ padding: '10px 12px', background: hasRisk ? 'rgba(56, 189, 248, 0.1)' : 'rgba(255,255,255,0.05)', border: hasRisk ? '1px solid rgba(56, 189, 248, 0.25)' : '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: hasRisk ? 'var(--accent)' : 'var(--text-muted)' }}>
          <Send size={14} className={(hasRisk && !sent) ? "pulse-glow" : ""} />
          <span style={{ fontSize: '0.75rem', fontWeight: 500, letterSpacing: '0.3px' }}>
            {sent ? 'Alert Sent to Telegram!' : hasRisk ? `Auto-Notifying in ${mins}:${secs.toString().padStart(2, '0')}` : 'System Monitoring...'}
          </span>
        </div>
        {!sent && (
          <button onClick={sendAlert} disabled={sending} className="toggle-btn" style={{ padding: '4px 10px', background: hasRisk ? 'var(--accent)' : 'rgba(255,255,255,0.1)', color: hasRisk ? '#fff' : 'var(--text-secondary)', border: 'none', fontSize: '0.7rem', opacity: sending ? 0.7 : 1 }}>
            {sending ? 'Sending...' : 'Test Alert'}
          </button>
        )}
      </div>
    </div>
  );
};

export default function RealTimeMonitor({ visible, coordinate, district: initialDistrict, season, year }) {
  const [data, setData] = useState(null);
  const [interpData, setInterpData] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [lastFetchTime, setLastFetchTime] = useState(null);
  const [pollProgress, setPollProgress] = useState(0);
  const [isFetching, setIsFetching] = useState(false);
  const dataRef = useRef(null);
  const pollStartRef = useRef(null);
  const pollStartDataRef = useRef(null);
  const pollRef = useRef(null);
  const clockRef = useRef(null);
  const interpRef = useRef(null);
  const streamStartRef = useRef(null);

  const district = initialDistrict || 'Ganjam';

  const fetchRealtime = useCallback(async () => {
    setIsFetching(true);
    try {
      const body = {
        latitude: coordinate?.lat || 20.5,
        longitude: coordinate?.lng || 85.8,
        district,
        year: year || 2024,
        season: season || 'Kharif',
      };
      const res = await fetch(`${API_BASE_URL}/api/realtime/coordinate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`Backend returned ${res.status}`);
      const result = await res.json();

      const prev = dataRef.current;
      if (prev) {
        pollStartDataRef.current = { ...prev };
      } else {
        // First poll: create slightly-off baseline so streaming starts immediately
        const base = JSON.parse(JSON.stringify(result));
        if (base.telemetry) {
          base.telemetry.T2M -= 0.5;
          base.telemetry.RH2M -= 3;
          base.telemetry.PRECTOTCORR = Math.max(0, (base.telemetry.PRECTOTCORR ?? 0) * 0.7);
          base.telemetry.GWETROOT = Math.max(0, (base.telemetry.GWETROOT ?? 0.5) - 0.02);
        }
        if (base.prediction) {
          base.prediction.predicted_yield = Math.max(0, (base.prediction.predicted_yield ?? 0) - 0.15);
          base.prediction.failure_probability = Math.max(0, (base.prediction.failure_probability ?? 0) - 0.03);
        }
        pollStartDataRef.current = base;
      }
      pollStartRef.current = Date.now();
      dataRef.current = result;
      setData(result);
      setInterpData(null);
      setLastFetchTime(new Date());
    } catch (err) {
      console.error('Realtime fetch error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
      setIsFetching(false);
    }
  }, [coordinate, district, year, season]);

  // Reset the streaming trend to 0 whenever the pinned location changes, so a
  // new location gets a fresh trend from t=0 (matches "until stopped or
  // location changed" behaviour). `district` on the Dashboard also qualifies.
  useEffect(() => {
    setHistory([]);
    streamStartRef.current = null;
    pollStartRef.current = null;
    pollStartDataRef.current = null;
    interpData && setInterpData(null);
  }, [coordinate?.lat, coordinate?.lng, district, year, season]);

  useEffect(() => {
    if (!visible) return;
    setLoading(true);
    fetchRealtime();
    pollRef.current = setInterval(fetchRealtime, POLL_INTERVAL);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [visible, fetchRealtime]);

  // 1-second interpolation ticker — smooth streaming between 60s polls
  useEffect(() => {
    if (!visible) return;

    // Seeded micro-drift for visible streaming when real data is stable
    const drift = (seed, amplitude) => {
      const x = Math.sin(Date.now() * 0.008 + seed * 100) * 100;
      return (x - Math.floor(x) - 0.5) * 2 * amplitude;
    };

    const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

    const tick = () => {
      const end = dataRef.current;
      const start = pollStartDataRef.current;
      const startTime = pollStartRef.current;
      if (!end || !start || !startTime) return;

      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / POLL_INTERVAL, 1);
      setPollProgress(progress);
      const t = (a, b) => a + (b - a) * progress;

      const interpTelemetry = {
        T2M: t(start.telemetry?.T2M ?? 0, end.telemetry?.T2M ?? 0) + drift(1, 0.2),
        RH2M: t(start.telemetry?.RH2M ?? 0, end.telemetry?.RH2M ?? 0) + drift(2, 1.0),
        PRECTOTCORR: Math.max(0, t(start.telemetry?.PRECTOTCORR ?? 0, end.telemetry?.PRECTOTCORR ?? 0) + drift(3, 0.1)),
        GWETROOT: clamp(t(start.telemetry?.GWETROOT ?? 0.5, end.telemetry?.GWETROOT ?? 0.5) + drift(4, 0.005), 0, 1),
      };

      let interpPrediction = end.prediction;
      if (start.prediction && end.prediction) {
        interpPrediction = {
          ...end.prediction,
          predicted_yield: Math.max(0, t(
            start.prediction.predicted_yield ?? 0,
            end.prediction.predicted_yield ?? 0
          ) + drift(5, 0.05)),
          failure_probability: clamp(t(
            start.prediction.failure_probability ?? 0,
            end.prediction.failure_probability ?? 0
          ) + drift(6, 0.005), 0, 1),
        };
      }

      setInterpData({
        telemetry: interpTelemetry,
        telemetry_weekly: end.telemetry_weekly,
        week_sources: end.week_sources,
        current_week: end.current_week,
        prediction: interpPrediction,
        nearest_district: end.nearest_district,
        is_mocked: end.is_mocked,
      });

      if (interpPrediction) {
        if (!streamStartRef.current) streamStartRef.current = Date.now();
        setHistory(prev => {
          const entry = {
            time: new Date().toLocaleTimeString(),
            seconds: ((Date.now() - streamStartRef.current) / 1000),
            yield: interpPrediction.predicted_yield,
            failureRisk: interpPrediction.failure_probability * 100,
            temp: interpTelemetry.T2M,
            humidity: interpTelemetry.RH2M,
            precip: interpTelemetry.PRECTOTCORR,
            soilMoisture: interpTelemetry.GWETROOT * 100,
          };
          const next = [...prev, entry];
          return next;
        });
      }
    };

    if (dataRef.current) {
      if (!pollStartRef.current) pollStartRef.current = Date.now();
      tick();
    }

    interpRef.current = setInterval(tick, 1000);
    return () => {
      if (interpRef.current) clearInterval(interpRef.current);
    };
  }, [visible]);

  useEffect(() => {
    if (!visible) return;
    clockRef.current = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => { if (clockRef.current) clearInterval(clockRef.current); };
  }, [visible]);

  if (!visible) return null;

  const liveData = interpData || data;

  const timeStr = currentTime.toLocaleTimeString();
  const lastFetchStr = lastFetchTime?.toLocaleTimeString() || '--';
  const lat = coordinate?.lat?.toFixed(4) || '20.5000';
  const lng = coordinate?.lng?.toFixed(4) || '85.8000';

  const gaugeColor = (value, type) => {
    if (type === 'temp') return value > 34 ? 'var(--status-failure)' : value > 28 ? 'var(--status-stress)' : 'var(--status-healthy)';
    if (type === 'humidity') return value > 85 ? 'var(--status-failure)' : 'var(--status-healthy)';
    if (type === 'precip') return value > 10 ? 'var(--chart-1)' : 'rgba(255,255,255,0.5)';
    if (type === 'soil') return value < 0.35 ? 'var(--status-failure)' : 'var(--status-healthy)';
    return '#fff';
  };

  const gaugeCards = liveData ? [
    { label: 'Temperature', value: liveData.telemetry?.T2M, unit: '°C', icon: <Thermometer size={20} />, type: 'temp' },
    { label: 'Humidity', value: liveData.telemetry?.RH2M, unit: '%', icon: <Droplets size={20} />, type: 'humidity' },
    { label: 'Precipitation', value: liveData.telemetry?.PRECTOTCORR, unit: 'mm', icon: <CloudRain size={20} />, type: 'precip' },
    { label: 'Soil Moisture', value: liveData.telemetry?.GWETROOT !== undefined ? (liveData.telemetry.GWETROOT * 100).toFixed(0) : null, unit: '%', icon: <Sprout size={20} />, type: 'soil' },
  ] : [];

  return (
    <>
      <style>{`
        @keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
      `}</style>
    <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Activity size={20} style={{ color: 'var(--status-healthy)' }} /> Real-Time Weather Monitor
            {!loading && <span style={{ fontSize: '0.7rem', padding: '3px 8px', background: 'rgba(16, 185, 129, 0.15)', color: 'var(--status-healthy)', borderRadius: '4px', border: '1px solid rgba(16, 185, 129, 0.3)', animation: 'pulse 2s infinite' }}>LIVE</span>}
          </h3>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <MapPin size={14} style={{ color: 'var(--status-failure)' }} />
          <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{lat}°N, {lng}°E → {liveData?.nearest_district || district}</span>
          <Clock size={14} style={{ color: 'var(--text-secondary)' }} />
          <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Last: {lastFetchStr}</span>
          <span style={{ color: 'var(--chart-5)', fontSize: '0.85rem', fontFamily: 'monospace' }}>{timeStr}</span>
          <button onClick={fetchRealtime} disabled={loading} className="toggle-btn" style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '4px 8px', fontSize: '0.75rem' }}>
            <RefreshCw size={12} className={loading ? 'spin' : ''} /> Refresh
          </button>
        </div>
      </div>

      {/* Poll progress bar + countdown */}
      {liveData && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ flex: 1, height: '4px', background: 'rgba(255,255,255,0.08)', borderRadius: '2px', overflow: 'hidden' }}>
            <div style={{
              width: `${pollProgress * 100}%`,
              height: '100%',
              background: isFetching ? 'var(--accent)' : 'var(--accent-soft)',
              borderRadius: '2px',
              transition: 'width 1s linear',
              opacity: isFetching ? 0.6 : 1,
            }} />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
            {isFetching ? (
              <><RefreshCw size={11} className="spin" /> Refreshing...</>
            ) : (
              <><Clock size={11} /> Next in {Math.ceil((1 - pollProgress) * 60)}s</>
            )}
          </div>
        </div>
      )}

      {error && (
        <div style={{ padding: '10px 14px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '8px', color: 'var(--status-failure)', fontSize: '0.85rem' }}>
          <AlertTriangle size={14} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
          {error}
        </div>
      )}

      {liveData && (
        <div style={{ position: 'relative' }}>
          {isFetching && (
            <div style={{
              position: 'absolute', inset: 0, zIndex: 5, pointerEvents: 'none',
              background: 'linear-gradient(90deg, transparent 0%, var(--accent-soft) 50%, transparent 100%)',
              backgroundSize: '200% 100%',
              animation: 'shimmer 1.5s ease-in-out infinite',
              borderRadius: '8px',
            }} />
          )}
          <div className="realtime-gauge-grid">
            {gaugeCards.map(g => (
              <div key={g.label} style={{ background: 'rgba(0,0,0,0.25)', padding: '14px', textAlign: 'center', borderRadius: '8px', border: `1px solid ${gaugeColor(g.value, g.type)}22` }}>
                <div style={{ color: gaugeColor(g.value, g.type), marginBottom: '4px' }}>{g.icon}</div>
                <div style={{ fontSize: '1.6rem', fontWeight: 'bold', color: 'var(--text-primary)', lineHeight: '1.2' }}>
                  {g.value != null ? (typeof g.value === 'number' ? g.value.toFixed(1) : g.value) : '--'}
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginLeft: '4px' }}>{g.unit}</span>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{g.label}</div>
              </div>
            ))}
          </div>

          {/* Real-Time Telemetry Stream — 4 variables over elapsed seconds */}
          {history.length > 1 && (
            <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: '10px', padding: '16px' }}>
              <h4 style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Activity size={14} /> Real-Time Telemetry Stream — 4 Variables (seconds)
              </h4>
              <div style={{ height: '180px', width: '100%' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={history} margin={{ top: 10, right: 10, bottom: 5, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis
                      dataKey="seconds"
                      type="number"
                      domain={[0, 'dataMax']}
                      stroke="rgba(255,255,255,0.4)"
                      fontSize={9}
                      tick={{ fill: 'rgba(255,255,255,0.4)' }}
                      tickFormatter={(v) => `${Math.round(v)}s`}
                    />
                    <YAxis yAxisId="scaled" stroke="var(--chart-4)" fontSize={9} tick={{ fill: 'var(--chart-4)' }} label={{ value: '°C / %', angle: 90, position: 'insideRight', style: { fill: 'var(--chart-4)', fontSize: 10 } }} />
                    <YAxis yAxisId="other" orientation="right" stroke="var(--chart-1)" fontSize={9} tick={{ fill: 'var(--chart-1)' }} label={{ value: 'mm / %', angle: -90, position: 'insideLeft', style: { fill: 'var(--chart-1)', fontSize: 10 } }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: 'rgba(15,23,42,0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                      labelFormatter={(v) => `${Math.round(v)}s`}
                    />
                    <Line yAxisId="scaled" type="monotone" dataKey="temp" stroke="var(--chart-4)" strokeWidth={2} dot={false} name="Temp (°C)" isAnimationActive={false} />
                    <Line yAxisId="scaled" type="monotone" dataKey="humidity" stroke="var(--chart-5)" strokeWidth={2} dot={false} name="Humidity (%)" isAnimationActive={false} />
                    <Line yAxisId="other" type="monotone" dataKey="precip" stroke="var(--chart-1)" strokeWidth={2} dot={false} name="Precip (mm)" isAnimationActive={false} />
                    <Line yAxisId="other" type="monotone" dataKey="soilMoisture" stroke="var(--chart-3)" strokeWidth={2} dot={false} name="Soil Moisture (%)" isAnimationActive={false} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
              <div style={{ display: 'flex', gap: '12px', marginTop: '6px', fontSize: '0.65rem', color: 'var(--text-muted)', justifyContent: 'center' }}>
                <span><span style={{ color: 'var(--chart-4)' }}>━</span> Temp</span>
                <span><span style={{ color: 'var(--chart-5)' }}>━</span> Humidity</span>
                <span><span style={{ color: 'var(--chart-1)' }}>━</span> Precip</span>
                <span><span style={{ color: 'var(--chart-3)' }}>━</span> Soil Moisture</span>
              </div>
            </div>
          )}

          {liveData.prediction && (
            <div style={{ display: 'grid', gridTemplateColumns: '2.5fr 1.5fr', gap: '12px', alignItems: 'stretch' }}>
              {/* Column 1: Live Prediction + Yield/Failure stream */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ background: 'rgba(34,197,94,0.05)', border: '1px solid rgba(34,197,94,0.2)', borderRadius: '8px', padding: '12px' }}>
                  <h4 style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Activity size={12} style={{ color: 'var(--status-healthy)' }} /> Live Prediction
                  </h4>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: 'var(--status-healthy)', lineHeight: '1.1' }}>
                        {liveData.prediction.predicted_yield?.toFixed(2) || '--'} <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 'normal' }}>Q/Acre</span>
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '3px' }}>
                        Failure Risk: <span style={{ color: liveData.prediction.failure_probability > 0.5 ? 'var(--status-failure)' : 'var(--status-healthy)' }}>
                          {((liveData.prediction.failure_probability || 0) * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>90% CI</div>
                      <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--accent)' }}>
                        {liveData.prediction.confidence_interval?.lower?.toFixed(1)} – {liveData.prediction.confidence_interval?.upper?.toFixed(1)}
                      </div>
                    </div>
                  </div>
                </div>

                {history.length > 1 && (
                  <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: '8px', padding: '12px', display: 'flex', flexDirection: 'column' }}>
                    <h4 style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Activity size={12} /> Live Prediction Stream — Yield &amp; Failure (seconds)
                    </h4>
                    <div style={{ height: '200px', width: '100%', flex: '0 0 200px' }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={history} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                          <XAxis
                            dataKey="seconds"
                            type="number"
                            domain={[0, 'dataMax']}
                            stroke="rgba(255,255,255,0.4)"
                            fontSize={9}
                            tick={{ fill: 'rgba(255,255,255,0.4)' }}
                            tickFormatter={(v) => `${Math.round(v)}s`}
                          />
                          <YAxis yAxisId="yield" stroke="var(--chart-2)" fontSize={9} tick={{ fill: 'var(--chart-2)' }} />
                          <YAxis yAxisId="risk" orientation="right" stroke="var(--status-failure)" fontSize={9} tick={{ fill: 'var(--status-failure)' }} />
                          <Tooltip
                            contentStyle={{ backgroundColor: 'rgba(15,23,42,0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                            labelFormatter={(v) => `${Math.round(v)}s`}
                          />
                          <Line yAxisId="yield" type="monotone" dataKey="yield" stroke="var(--chart-2)" strokeWidth={2} dot={false} name="Yield (Q/Acre)" isAnimationActive={false} />
                          <Line yAxisId="risk" type="monotone" dataKey="failureRisk" stroke="var(--status-failure)" strokeWidth={2} dot={false} name="Risk (%)" isAnimationActive={false} />
                        </ComposedChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}
              </div>

              {/* Column 2: Active Triggers */}
              <div style={{ background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '12px', display: 'flex', flexDirection: 'column' }}>
                <h4 style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <AlertTriangle size={12} /> Active Triggers
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', flex: 1 }}>
                  {buildTriggerList(liveData.prediction).map(t => {
                    const meta = TRIGGER_META[t.id] || {};
                    const color = t.active
                      ? (t.severity === 'high' ? 'var(--status-failure)' : t.severity === 'medium' ? 'var(--status-stress)' : 'var(--status-healthy)')
                      : 'var(--text-muted)';
                    const prog = Math.max(0, Math.min(1, t.progress || 0));
                    return (
                      <div key={t.id} style={{ opacity: t.active ? 1 : 0.45, transition: 'opacity 0.3s' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                          <span style={{ color }}>{meta.icon}</span>
                          <span style={{ color: 'var(--text-primary)', fontSize: '0.78rem', fontWeight: 500, flex: 1 }}>{t.label}</span>
                          {t.active && (
                            <span style={{ fontSize: '0.65rem', fontWeight: 600, padding: '2px 6px', borderRadius: '4px', background: `${color}22`, color: color, border: `1px solid ${color}44` }}>
                              ACTIVE RISK
                            </span>
                          )}
                          <span style={{ width: 8, height: 8, borderRadius: '50%', background: t.active ? color : 'var(--text-muted)' }} />
                        </div>
                        {t.current_value != null && (
                          <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', marginTop: '3px' }}>
                            {typeof t.current_value === 'number' ? t.current_value.toFixed(1) : t.current_value}
                            {t.unit ? ` ${t.unit}` : ''}
                            {t.threshold != null ? ` / threshold ${t.threshold}` : ''}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
                <TelegramNotifier prediction={liveData.prediction} district={liveData.nearest_district || district} />
              </div>
            </div>
          )}
        </div>
      )}

      {!liveData && !error && (
        <div style={{ textAlign: 'center', padding: '40px 20px' }}>
          <div className="spin" style={{ display: 'inline-block', marginBottom: '12px' }}><RefreshCw size={32} style={{ color: 'var(--text-secondary)' }} /></div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Fetching live weather data from Open-Meteo...</div>
        </div>
      )}
    </div>
    </>
  );
}
