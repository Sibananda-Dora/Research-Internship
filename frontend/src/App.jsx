import React, { useState, useEffect } from 'react';
import MapCard from './components/MapCard';
import MetricsCard from './components/MetricsCard';
import Timeline from './components/Timeline';
import Heatmap from './components/Heatmap';
import DSSChat from './components/DSSChat';
import { Leaf, Sliders, ShieldAlert, Cpu } from 'lucide-react';

const API_BASE_URL = 'http://127.0.0.1:8000';

const YEARS = Array.from({ length: 20 }, (_, i) => 2006 + i);

export default function App() {
  const [districts, setDistricts] = useState([
    "Angul", "Balangir", "Balasore", "Bargarh", "Bhadrak", "Boudh",
    "Cuttack", "Deogarh", "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur",
    "Jajpur", "Jharsuguda", "Kalahandi", "Kandhamal", "Kendrapara", "Keonjhar",
    "Khurda", "Koraput", "Malkangiri", "Mayurbhanj", "Nabarangpur", "Nayagarh",
    "Nuapada", "Puri", "Rayagada", "Sambalpur", "Sonepur", "Sundargarh"
  ]);
  
  const [selectedDistrict, setSelectedDistrict] = useState('Ganjam');
  const [selectedYear, setSelectedYear] = useState(2024);
  const [selectedSeason, setSelectedSeason] = useState('Kharif');
  const [selectedWeek, setSelectedWeek] = useState(6);
  
  const [prediction, setPrediction] = useState(null);
  const [telemetry, setTelemetry] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [backendOffline, setBackendOffline] = useState(false);

  // Weather simulation modifier state
  const [simulating, setSimulating] = useState(false);
  const [modifiers, setModifiers] = useState({
    precip: 1.0,
    temp: 0.0,
    wetness: 0.0
  });

  // Coordinate picker state (for MapCard → OdishaGISMap)
  const [coordinateMode, setCoordinateMode] = useState(false);
  const [selectedCoordinate, setSelectedCoordinate] = useState(null);
  const [nearestDistrict, setNearestDistrict] = useState(null);

  // Calculate dummy status map for map choropleths
  const [districtStatus, setDistrictStatus] = useState({});

  // Generate a random status map for visual interest based on seed
  useEffect(() => {
    const statuses = ['healthy', 'healthy', 'stress', 'healthy', 'failure', 'stress', 'healthy'];
    const tempStatus = {};
    districts.forEach((d, idx) => {
      // Semi-random deterministic seed
      const seed = d.length + idx + (selectedYear % 10) + (selectedSeason === 'Kharif' ? 2 : 1);
      tempStatus[d] = statuses[seed % statuses.length];
    });
    setDistrictStatus(tempStatus);
  }, [selectedYear, selectedSeason, districts]);

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

      {/* Main dashboard grid */}
      <div className="dashboard-grid">
        <div className="main-content-flow">
          {/* Prediction summary */}
          <MetricsCard prediction={prediction} loading={loading} />

          {/* Map twin and timeline */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '20px' }}>
            <MapCard 
              selectedDistrict={selectedDistrict} 
              onSelectDistrict={setSelectedDistrict}
              districtStatus={districtStatus}
              coordinateMode={coordinateMode}
              selectedCoordinate={selectedCoordinate}
              onCoordinateSelect={setSelectedCoordinate}
              onToggleCoordinateMode={() => setCoordinateMode(!coordinateMode)}
            />

            <Timeline 
              selectedWeek={selectedWeek}
              onSelectWeek={setSelectedWeek}
              telemetry={telemetry}
              loading={loading}
            />
          </div>

          {/* Attention Weights Heatmap */}
          <Heatmap 
            attentionWeights={prediction?.attention_weights}
            telemetry={telemetry}
            selectedWeek={selectedWeek}
            onSelectWeek={setSelectedWeek}
            loading={loading}
          />
        </div>

        {/* Sidebar panels */}
        <div className="sidebar-panel">
          {/* What-If Simulation sliders */}
          <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
              <Sliders size={18} className="text-cyan" />
              <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>What-If Soil & Climate Simulator</h3>
            </div>

            {/* Precip slider */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Precipitation Scaling</span>
                <span className="text-cyan">{(modifiers.precip * 100).toFixed(0)}%</span>
              </div>
              <input 
                type="range" 
                min="0.2" 
                max="2.0" 
                step="0.1" 
                value={modifiers.precip}
                onChange={(e) => setModifiers(prev => ({ ...prev, precip: parseFloat(e.target.value) }))}
              />
            </div>

            {/* Temp slider */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Temperature Offset</span>
                <span className="text-cyan">{modifiers.temp > 0 ? `+${modifiers.temp}` : modifiers.temp} °C</span>
              </div>
              <input 
                type="range" 
                min="-5" 
                max="5" 
                step="0.5" 
                value={modifiers.temp}
                onChange={(e) => setModifiers(prev => ({ ...prev, temp: parseFloat(e.target.value) }))}
              />
            </div>

            {/* Wetness slider */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Soil Moisture Offset</span>
                <span className="text-cyan">{modifiers.wetness > 0 ? `+${modifiers.wetness}` : modifiers.wetness}</span>
              </div>
              <input 
                type="range" 
                min="-0.3" 
                max="0.3" 
                step="0.05" 
                value={modifiers.wetness}
                onChange={(e) => setModifiers(prev => ({ ...prev, wetness: parseFloat(e.target.value) }))}
              />
            </div>

            <div style={{ display: 'flex', gap: '10px', marginTop: '6px' }}>
              <button 
                onClick={handleSimulationSubmit}
                className="send-btn" 
                style={{ flex: 1, padding: '10px' }}
              >
                Run Simulation
              </button>
              {simulating && (
                <button 
                  onClick={handleResetSimulation}
                  className="toggle-btn"
                  style={{ padding: '10px' }}
                >
                  Reset
                </button>
              )}
            </div>
          </div>

          {/* Expert chatbot */}
          <DSSChat 
            district={selectedDistrict}
            year={selectedYear}
            season={selectedSeason}
            onRunSimulation={handleChatSimulation}
          />
        </div>
      </div>
    </div>
  );
}
