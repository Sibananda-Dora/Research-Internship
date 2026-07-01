import React, { useState, useEffect, useRef, Suspense, lazy } from 'react';
import { ShieldAlert, Cpu, RefreshCw, CheckCircle, AlertCircle, Layout } from 'lucide-react';

const FarmerDashboard = lazy(() => import('./components/FarmerDashboard'));
const AnalystDashboard = lazy(() => import('./components/AnalystDashboard'));
const ArchitectureFlow = lazy(() => import('./components/ArchitectureFlow'));

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const YEARS = Array.from({ length: 20 }, (_, i) => 2006 + i);

const DEFAULT_STEPS_ORDER = [
  'validate_csv', 'fetch_telemetry', 'merge_data',
  'backup_models', 'prepare_data', 'train_models', 'save_version'
];

const STEP_LABELS = {
  validate_csv: 'Validating incoming data',
  fetch_telemetry: 'Fetching NASA telemetry',
  merge_data: 'Merging into dataset',
  backup_models: 'Backing up current models',
  prepare_data: 'Running data preparation',
  train_models: 'Retraining models (~120s)',
  save_version: 'Saving version metadata',
  queued: 'Queued...',
  complete: 'Complete!'
};

const DISTRICTS = [
  "Angul", "Balangir", "Balasore", "Bargarh", "Bhadrak", "Boudh",
  "Cuttack", "Deogarh", "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur",
  "Jajpur", "Jharsuguda", "Kalahandi", "Kandhamal", "Kendrapara", "Keonjhar",
  "Khurda", "Koraput", "Malkangiri", "Mayurbhanj", "Nabarangpur", "Nayagarh",
  "Nuapada", "Puri", "Rayagada", "Sambalpur", "Sonepur", "Sundargarh"
];

export default function App() {
  const districts = DISTRICTS;
  const [selectedDistrict, setSelectedDistrict] = useState('Ganjam');
  const [selectedYear, setSelectedYear] = useState(2024);
  const [selectedSeason, setSelectedSeason] = useState('Kharif');
  const [selectedWeek, setSelectedWeek] = useState(6);
  
  const [prediction, setPrediction] = useState(null);
  const [telemetry, setTelemetry] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [backendOffline, setBackendOffline] = useState(false);

  const [pipelineVersion, setPipelineVersion] = useState(null);
  const [pipelineCheck, setPipelineCheck] = useState(null);
  const [pipelineTaskId, setPipelineTaskId] = useState(null);
  const [pipelineStatus, setPipelineStatus] = useState(null);
  const [pipelineModal, setPipelineModal] = useState(false);
  const pollingRef = useRef(null);

  // Weather simulation modifier state
  const [simulating, setSimulating] = useState(false);
  const [modifiers, setModifiers] = useState({
    precip: 1.0,
    temp: 0.0,
    wetness: 0.0
  });

  // Role toggle
  const [userRole, setUserRole] = useState('analyst');
  const [showArchFlow, setShowArchFlow] = useState(false);

  // Coordinate picker state (for MapCard → OdishaGISMap)
  const [coordinateMode, setCoordinateMode] = useState(false);
  const [selectedCoordinate, setSelectedCoordinate] = useState(null);
  const [nearestDistrict, setNearestDistrict] = useState(null);

  // Fetch prediction and telemetry when district, year, or season changes
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      setBackendOffline(false);
      try {
        // 1. Fetch prediction
        const predRes = await fetch(`${API_BASE_URL}/api/predict/${selectedDistrict}/${selectedYear}/${selectedSeason}`);
        if (!predRes.ok) throw new Error("Backend offline");
        const predData = await predRes.json();
        setPrediction(predData);

        // 2. Fetch telemetry
        const telRes = await fetch(`${API_BASE_URL}/api/telemetry/${selectedDistrict}/${selectedYear}/${selectedSeason}`);
        const telData = await telRes.json();
        setTelemetry(telData.telemetry);
      } catch (err) {
        console.warn("FastAPI backend is offline, loading mock telemetry client-side.");
        setBackendOffline(true);
        // Generate high-fidelity mock client fallback
        const mockTelemetry = {
          PRECTOTCORR: Array.from({ length: 12 }, (_, i) => 25.0 + Math.sin(i * 1.2) * 20.0 + (i === 5 ? 120 : 0)),
          T2M: Array.from({ length: 12 }, (_, i) => 27.5 + Math.cos(i * 0.8) * 3.5),
          RH2M: Array.from({ length: 12 }, (_, i) => 70.0 + Math.sin(i * 1.5) * 15.0),
          GWETROOT: Array.from({ length: 12 }, (_, i) => 0.65 - i * 0.03 + (selectedDistrict === 'Ganjam' && i > 5 ? -0.2 : 0))
        };
        
        setTelemetry(mockTelemetry);

        // Calculate failure probability based on moisture
        const wetnessMean = mockTelemetry.GWETROOT.slice(3, 8).reduce((a,b)=>a+b, 0) / 5;
        const predictedYield = Math.max(2.1, 10.4 - (0.4 - wetnessMean) * 15.0);
        const failProb = 1.0 / (1.0 + Math.exp(2.5 * (predictedYield - 7.0)));
        const triggers = wetnessMean < 0.45 ? ["Drought Stress"] : [];

        setPrediction({
          predicted_yield: parseFloat(predictedYield.toFixed(2)),
          failure_probability: parseFloat(failProb.toFixed(3)),
          failure_anomaly: failProb > 0.5 ? 1 : 0,
          attention_weights: [0.03, 0.05, 0.07, 0.11, 0.18, 0.23, 0.17, 0.09, 0.04, 0.02, 0.01, 0.00],
          active_triggers: triggers,
          confidence_interval: {
            lower: parseFloat((predictedYield - 1.2).toFixed(2)),
            upper: parseFloat((predictedYield + 1.2).toFixed(2))
          },
          monte_carlo_distribution: Array.from({ length: 100 }, () => predictedYield + (Math.random() - 0.5) * 1.5)
        });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedDistrict, selectedYear, selectedSeason]);

  // Fetch prediction from coordinate pin
  useEffect(() => {
    if (!selectedCoordinate || !coordinateMode) return;
    const fetchCoordPrediction = async () => {
      setLoading(true);
      setError(null);
      setBackendOffline(false);
      try {
        const res = await fetch(`${API_BASE_URL}/api/predict/coordinate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            latitude: selectedCoordinate.lat,
            longitude: selectedCoordinate.lng,
            year: selectedYear,
            season: selectedSeason
          })
        });
        if (!res.ok) throw new Error("Backend offline");
        const data = await res.json();
        setPrediction(data);
        setNearestDistrict(data.nearest_district);
        // Also set the district selector to the resolved district
        setSelectedDistrict(data.nearest_district);
      } catch (err) {
        console.warn("Coordinate prediction failed, using fallback");
        setBackendOffline(true);
        // Resolve a nearest district client-side via the backend districts list
        setNearestDistrict(selectedDistrict);
      } finally {
        setLoading(false);
      }
    };
    fetchCoordPrediction();
  }, [selectedCoordinate, selectedYear, selectedSeason]);

  // Fetch pipeline version on mount
  useEffect(() => {
    const fetchVersion = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/pipeline/version`);
        if (res.ok) setPipelineVersion(await res.json());
      } catch {}
    };
    fetchVersion();
  }, []);

  // Poll pipeline status while running
  useEffect(() => {
    if (!pipelineTaskId) return;
    pollingRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/pipeline/status/${pipelineTaskId}`);
        if (res.ok) {
          const data = await res.json();
          setPipelineStatus(data);
          if (data.status === 'success' || data.status === 'failed') {
            clearInterval(pollingRef.current);
            if (data.status === 'success') {
              const verRes = await fetch(`${API_BASE_URL}/api/pipeline/version`);
              if (verRes.ok) setPipelineVersion(await verRes.json());
            }
          }
        }
      } catch {}
    }, 2000);
    return () => { if (pollingRef.current) clearInterval(pollingRef.current); };
  }, [pipelineTaskId]);

  const handleCheckPipeline = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/pipeline/check`);
      if (res.ok) {
        const data = await res.json();
        setPipelineCheck(data);
        setPipelineModal(true);
      }
    } catch {}
  };

  const handleRunPipeline = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/pipeline/update`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setPipelineTaskId(data.task_id);
        setPipelineStatus({ status: 'queued', step: 'queued', progress: 0 });
        setPipelineCheck(null);
      }
    } catch {}
  };

  const handleModifierChange = (key, value) => {
    setModifiers(prev => ({ ...prev, [key]: value }));
  };

  const handleSimulatePreset = (mods) => {
    setModifiers(prev => ({ ...prev, ...mods }));
    setTimeout(() => handleSimulationSubmit(), 300);
  };

  // Handle What-If custom simulation submission
  const handleSimulationSubmit = async () => {
    setLoading(true);
    setBackendOffline(false);
    try {
      const payload = {
        district: selectedDistrict,
        season: selectedSeason,
        year: selectedYear,
        precip_modifiers: Array.from({ length: 12 }, () => modifiers.precip),
        temp_modifiers: Array.from({ length: 12 }, () => modifiers.temp),
        wetness_modifiers: Array.from({ length: 12 }, () => modifiers.wetness),
        humidity_modifiers: Array.from({ length: 12 }, () => 0.0)
      };

      const res = await fetch(`${API_BASE_URL}/api/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (!res.ok) throw new Error("Simulation server offline");
      const simulatedData = await res.json();
      setPrediction(simulatedData);
      
      // Mutate telemetry state with simulation scaling
      setTelemetry(prev => ({
        PRECTOTCORR: prev.PRECTOTCORR.map(v => v * modifiers.precip),
        T2M: prev.T2M.map(v => v + modifiers.temp),
        RH2M: prev.RH2M,
        GWETROOT: prev.GWETROOT.map(v => Math.min(1.0, Math.max(0.0, v + modifiers.wetness)))
      }));

      setSimulating(true);
    } catch (err) {
      setBackendOffline(true);
      // Mock simulation logic
      const adjustedPrecip = telemetry.PRECTOTCORR.map(v => v * modifiers.precip);
      const adjustedTemp = telemetry.T2M.map(v => v + modifiers.temp);
      const adjustedWetness = telemetry.GWETROOT.map(v => Math.min(1.0, Math.max(0.0, v + modifiers.wetness)));

      setTelemetry({
        ...telemetry,
        PRECTOTCORR: adjustedPrecip,
        T2M: adjustedTemp,
        GWETROOT: adjustedWetness
      });

      const wetnessMean = adjustedWetness.slice(3, 8).reduce((a,b)=>a+b, 0) / 5;
      const predictedYield = Math.max(1.8, 10.4 - (0.4 - wetnessMean) * 15.0 - (modifiers.temp > 2 ? 1.5 : 0));
      const failProb = 1.0 / (1.0 + Math.exp(2.5 * (predictedYield - 7.0)));

      setPrediction(prev => ({
        ...prev,
        predicted_yield: parseFloat(predictedYield.toFixed(2)),
        failure_probability: parseFloat(failProb.toFixed(3)),
        failure_anomaly: failProb > 0.5 ? 1 : 0,
        active_triggers: wetnessMean < 0.45 ? ["Drought Stress"] : (modifiers.temp > 2 ? ["Thermal Sterility"] : []),
        confidence_interval: {
          lower: parseFloat((predictedYield - 1.1).toFixed(2)),
          upper: parseFloat((predictedYield + 1.1).toFixed(2))
        }
      }));

      setSimulating(true);
    } finally {
      setLoading(false);
    }
  };

  // Reset simulation to baseline
  const handleResetSimulation = () => {
    setModifiers({ precip: 1.0, temp: 0.0, wetness: 0.0 });
    setSimulating(false);
    // Force refetch of baseline prediction + telemetry via the existing useEffect
    const reKey = selectedDistrict + selectedYear + selectedSeason;
    // The key trick resets the effect's dependency trigger
    setTimeout(() => setSelectedDistrict(selectedDistrict), 50);
  };

  // Chat-triggered simulation
  const handleChatSimulation = (chatModifiers) => {
    setModifiers(prev => ({
      ...prev,
      precip: chatModifiers.precip,
      wetness: chatModifiers.precip < 1.0 ? -0.15 : 0.15
    }));
    // Auto execute simulation
    setTimeout(() => handleSimulationSubmit(), 500);
  };

  return (
    <div className="dashboard-container">
      <header className="glass-card" style={{ border: 'none', background: 'rgba(18,20,26,0.4)' }}>
        <div className="title-section" style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ background: 'rgba(6,182,212,0.15)', padding: '10px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Cpu size={32} className="text-cyan" />
          </div>
          <div>
            <h1>Odisha Crop Yield Twin</h1>
            <p>{coordinateMode && nearestDistrict
              ? `📍 Pinned near ${nearestDistrict} — running prediction for your location`
              : 'Select a district or pin your field on the map'}
            </p>
          </div>
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div className="role-toggle">
              <button className={userRole === 'farmer' ? 'active' : ''} onClick={() => setUserRole('farmer')}>👨‍🌾 Farmer</button>
              <button className={userRole === 'analyst' ? 'active' : ''} onClick={() => setUserRole('analyst')}>📊 Analyst</button>
            </div>
            <button
              onClick={() => setShowArchFlow(!showArchFlow)}
              className="toggle-btn"
              style={{ display: 'flex', alignItems: 'center', gap: '5px', padding: '6px 10px', fontSize: '0.75rem' }}
              title="Architecture Flow"
            >
              <Layout size={14} /> Flow
            </button>
            <button
              onClick={handleCheckPipeline}
              disabled={pipelineStatus?.status === 'running'}
              className="send-btn"
              style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '7px 14px', fontSize: '0.8rem', opacity: pipelineStatus?.status === 'running' ? 0.5 : 1 }}
            >
              <RefreshCw size={14} className={pipelineStatus?.status === 'running' ? 'spin' : ''} />
              {pipelineStatus?.status === 'running' ? 'Updating...' : 'Check Updates'}
            </button>
            {pipelineVersion && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px', padding: '5px 10px', background: 'rgba(255,255,255,0.05)', borderRadius: '6px', fontSize: '0.75rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Model</span>
                <span className="text-cyan" style={{ fontWeight: 600 }}>v{pipelineVersion.version}</span>
                {pipelineStatus?.status === 'success' && <CheckCircle size={12} className="text-healthy" />}
                {pipelineStatus?.status === 'failed' && <AlertCircle size={12} className="text-failure" />}
              </div>
            )}
          </div>
        </div>

        <div className="controls-header">
          {/* District selector */}
          <select 
            value={selectedDistrict} 
            onChange={(e) => setSelectedDistrict(e.target.value)}
          >
            {districts.map(d => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>

          {/* Season selector */}
          <select 
            value={selectedSeason} 
            onChange={(e) => setSelectedSeason(e.target.value)}
          >
            <option value="Kharif">Kharif Season</option>
            <option value="Rabi">Rabi Season</option>
          </select>

          {/* Year selector */}
          <select 
            value={selectedYear} 
            onChange={(e) => setSelectedYear(parseInt(e.target.value))}
          >
            {YEARS.map(y => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>
      </header>

      {/* Alerts */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '-10px', marginBottom: '10px' }}>
        {backendOffline && (
          <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.4)', padding: '10px 16px', borderRadius: '8px', color: '#fca5a5', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', fontWeight: 500 }}>
            <ShieldAlert size={16} />
            Backend API is offline or unreachable. Running dashboard in local simulation mode.
          </div>
        )}
        {!backendOffline && prediction?.is_mocked && (
          <div style={{ background: 'rgba(245, 158, 11, 0.15)', border: '1px solid rgba(245, 158, 11, 0.4)', padding: '10px 16px', borderRadius: '8px', color: '#fcd34d', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', fontWeight: 500 }}>
            <ShieldAlert size={16} />
            Historical data for this district/season/year combination is unavailable. Using simulated baseline data.
          </div>
        )}
      </div>

      {/* Conditional dashboard */}
      <Suspense fallback={<div className="loading-pulse" style={{padding: 40, textAlign: 'center', color: '#8892b0'}}>Loading dashboard...</div>}>
      {userRole === 'farmer' ? (
        <FarmerDashboard
          prediction={prediction}
          loading={loading}
          telemetry={telemetry}
          selectedDistrict={selectedDistrict}
          selectedYear={selectedYear}
          selectedSeason={selectedSeason}
          onSelectDistrict={setSelectedDistrict}
          onSelectYear={setSelectedYear}
          onSelectSeason={setSelectedSeason}
          coordinateMode={coordinateMode}
          selectedCoordinate={selectedCoordinate}
          onCoordinateSelect={setSelectedCoordinate}
          onToggleCoordinateMode={() => setCoordinateMode(!coordinateMode)}
          onSimulatePreset={handleSimulatePreset}
          onSimulate={handleSimulationSubmit}
          onChatSimulation={handleChatSimulation}
        />
      ) : (
        <AnalystDashboard
          prediction={prediction}
          loading={loading}
          telemetry={telemetry}
          selectedWeek={selectedWeek}
          onSelectWeek={setSelectedWeek}
          selectedDistrict={selectedDistrict}
          selectedYear={selectedYear}
          selectedSeason={selectedSeason}
          onSelectDistrict={setSelectedDistrict}
          coordinateMode={coordinateMode}
          selectedCoordinate={selectedCoordinate}
          onCoordinateSelect={setSelectedCoordinate}
          onToggleCoordinateMode={() => setCoordinateMode(!coordinateMode)}
          modifiers={modifiers}
          onModifierChange={handleModifierChange}
          simulating={simulating}
          onSimulate={handleSimulationSubmit}
          onResetSimulation={handleResetSimulation}
          onChatSimulation={handleChatSimulation}
        />
      )}
      </Suspense>
      {/* Architecture Flow overlay */}
      <Suspense fallback={null}>
      <ArchitectureFlow
        trace={prediction?.trace}
        visible={showArchFlow}
        onClose={() => setShowArchFlow(false)}
      />
      </Suspense>

      {/* Pipeline update modal */}
      {pipelineModal && pipelineCheck && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999, backdropFilter: 'blur(4px)' }}>
          <div className="glass-card" style={{ maxWidth: '480px', width: '90%', padding: '28px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>New Data Available</h3>
            <div style={{ background: 'rgba(6,182,212,0.1)', border: '1px solid rgba(6,182,212,0.3)', borderRadius: '8px', padding: '14px', fontSize: '0.9rem' }}>
              <p><strong>{pipelineCheck.new_records} new records</strong> found for year <strong>{pipelineCheck.new_years?.join(', ')}</strong></p>
              <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>New data will be merged, models retrained, and the dashboard will hot-reload.</p>
            </div>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button onClick={() => { setPipelineModal(false); setPipelineCheck(null); }} className="toggle-btn" style={{ padding: '9px 18px' }}>Cancel</button>
              <button onClick={() => { handleRunPipeline(); setPipelineModal(false); }} className="send-btn" style={{ padding: '9px 18px' }}>Download & Retrain</button>
            </div>
          </div>
        </div>
      )}

      {/* Pipeline progress overlay */}
      {pipelineStatus?.status === 'running' && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999, backdropFilter: 'blur(4px)' }}>
          <div className="glass-card" style={{ maxWidth: '440px', width: '90%', padding: '28px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <RefreshCw size={18} className="text-cyan spin" /> Updating Models
            </h3>
            <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden' }}>
              <div style={{ width: `${pipelineStatus.progress || 0}%`, height: '100%', background: 'var(--accent-gradient, linear-gradient(90deg, #06b6d4, #3b82f6))', borderRadius: '3px', transition: 'width 0.5s ease' }} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.85rem' }}>
              {['validate_csv', 'fetch_telemetry', 'merge_data', 'backup_models', 'prepare_data', 'train_models', 'save_version'].map(step => (
                <div key={step} style={{ display: 'flex', alignItems: 'center', gap: '8px', color: pipelineStatus.step === step ? 'var(--text-primary)' : (DEFAULT_STEPS_ORDER.indexOf(step) < DEFAULT_STEPS_ORDER.indexOf(pipelineStatus.step) ? 'var(--text-secondary)' : 'rgba(255,255,255,0.2)') }}>
                  <div style={{ width: '18px', height: '18px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: pipelineStatus.step === step ? 'rgba(6,182,212,0.2)' : 'transparent', border: '1px solid', borderColor: pipelineStatus.step === step ? '#06b6d4' : (DEFAULT_STEPS_ORDER.indexOf(step) < DEFAULT_STEPS_ORDER.indexOf(pipelineStatus.step) ? 'rgba(255,255,255,0.3)' : 'rgba(255,255,255,0.1)') }}>
                    {DEFAULT_STEPS_ORDER.indexOf(step) < DEFAULT_STEPS_ORDER.indexOf(pipelineStatus.step) ? <CheckCircle size={12} /> : (pipelineStatus.step === step ? <RefreshCw size={10} className="spin" /> : null)}
                  </div>
                  <span>{STEP_LABELS[step] || step}</span>
                </div>
              ))}
              {pipelineStatus.train_output && (
                <div style={{ marginTop: '8px', padding: '8px', background: 'rgba(0,0,0,0.3)', borderRadius: '6px', fontSize: '0.75rem', color: 'var(--text-secondary)', fontFamily: 'monospace', maxHeight: '80px', overflow: 'auto' }}>
                  {pipelineStatus.train_output}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Pipeline completion overlay */}
      {pipelineStatus?.status === 'success' && !pipelineModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999, backdropFilter: 'blur(4px)' }}>
          <div className="glass-card" style={{ maxWidth: '400px', width: '90%', padding: '28px', display: 'flex', flexDirection: 'column', gap: '14px', alignItems: 'center', textAlign: 'center' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'rgba(34,197,94,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <CheckCircle size={28} className="text-healthy" />
            </div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Models Updated</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Models retrained with new data. Version updated.</p>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>The dashboard is now running with the latest predictions.</p>
            <button onClick={() => setPipelineStatus(null)} className="send-btn" style={{ padding: '9px 24px', marginTop: '4px' }}>Done</button>
          </div>
        </div>
      )}
    </div>
  );
}
