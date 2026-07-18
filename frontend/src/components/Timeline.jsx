import React from 'react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, BarChart, Bar, Legend, ReferenceLine 
} from 'recharts';
import { Calendar } from 'lucide-react';

export default function Timeline({ 
  selectedWeek, 
  onSelectWeek, 
  telemetry, 
  loading 
}) {
  if (loading || !telemetry) {
    return (
      <div className="glass-card timeline-card skeleton" style={{ height: '340px' }}></div>
    );
  }

  // Map telemetry data into Recharts friendly format
  const chartData = Array.from({ length: 12 }, (_, idx) => {
    return {
      week: idx + 1,
      name: `W${idx + 1}`,
      precipitation: telemetry.PRECTOTCORR[idx] || 0,
      temperature: telemetry.T2M[idx] || 0,
      humidity: telemetry.RH2M[idx] || 0,
      soilWetness: ((telemetry.GWETROOT[idx] || 0) * 100), // Convert fraction to %
    };
  });

  return (
    <div className="glass-card timeline-card">
      <div className="card-header" style={{ marginBottom: '8px' }}>
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px' }} className="text-accent">
          <Calendar size={18} />
          12-Week Vegetative Timeline (Active: Week {selectedWeek})
        </h2>
      </div>

      {/* Recharts Spatial-Temporal Trends */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        {/* Chart 1: Precipitation and Soil Wetness */}
        <div>
          <h4 style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '8px', textTransform: 'uppercase' }}>
            Water Indices (Rainfall & Root Wetness)
          </h4>
          <div style={{ width: '100%', height: '180px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorPrecip" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--chart-1)" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="var(--chart-1)" stopOpacity={0.0}/>
                  </linearGradient>
                  <linearGradient id="colorWetness" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--chart-3)" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="var(--chart-3)" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={10} />
                <YAxis yAxisId="left" stroke="var(--chart-1)" fontSize={10} />
                <YAxis yAxisId="right" orientation="right" stroke="var(--chart-3)" fontSize={10} />
                <Tooltip 
                  contentStyle={{ background: 'var(--bg-secondary)', borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
                  itemStyle={{ fontSize: '0.8rem' }}
                />
                <ReferenceLine x={`W${selectedWeek}`} stroke="rgba(255,255,255,0.4)" strokeDasharray="3 3" yAxisId="left" />
                <Area yAxisId="left" type="monotone" dataKey="precipitation" stroke="var(--chart-1)" fillOpacity={1} fill="url(#colorPrecip)" name="Rain (mm)" />
                <Area yAxisId="right" type="monotone" dataKey="soilWetness" stroke="var(--chart-3)" fillOpacity={1} fill="url(#colorWetness)" name="Soil Wetness (%)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Temperature and Humidity */}
        <div>
          <h4 style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '8px', textTransform: 'uppercase' }}>
            Atmospheric Factors (Temp & Humidity)
          </h4>
          <div style={{ width: '100%', height: '180px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorTemp" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--chart-2)" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="var(--chart-2)" stopOpacity={0.0}/>
                  </linearGradient>
                  <linearGradient id="colorHum" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--chart-5)" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="var(--chart-5)" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={10} />
                <YAxis yAxisId="left" stroke="var(--chart-2)" fontSize={10} />
                <YAxis yAxisId="right" orientation="right" stroke="var(--chart-5)" fontSize={10} />
                <Tooltip 
                  contentStyle={{ background: 'var(--bg-secondary)', borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
                  itemStyle={{ fontSize: '0.8rem' }}
                />
                <ReferenceLine x={`W${selectedWeek}`} stroke="rgba(255,255,255,0.4)" strokeDasharray="3 3" yAxisId="left" />
                <Area yAxisId="left" type="monotone" dataKey="temperature" stroke="var(--chart-2)" fillOpacity={1} fill="url(#colorTemp)" name="Temp (°C)" />
                <Area yAxisId="right" type="monotone" dataKey="humidity" stroke="var(--chart-5)" fillOpacity={1} fill="url(#colorHum)" name="Humidity (%)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Week Slider controls */}
      <div className="slider-container">
        <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)' }}>W1</span>
        <div className="slider-track-wrap">
          <input 
            type="range" 
            min="1" 
            max="12" 
            step="1" 
            value={selectedWeek} 
            onChange={(e) => onSelectWeek(parseInt(e.target.value))}
          />
        </div>
        <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)' }}>W12</span>
      </div>
    </div>
  );
}
