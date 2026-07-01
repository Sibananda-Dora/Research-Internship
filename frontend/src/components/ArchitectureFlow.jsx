import React from 'react';
import { X, Cpu, Database, Brain, Network } from 'lucide-react';

const LAYERS = [
  {
    id: 'physical',
    icon: Cpu,
    label: 'L1: Physical',
    color: '#06b6d4',
    extract: (t) => t?.layer1_physical
      ? `${t.layer1_physical.district}, ${t.layer1_physical.season} ${t.layer1_physical.year}`
      : 'No active query',
    detail: (t) => t?.layer1_physical?.latitude
      ? `${t.layer1_physical.latitude.toFixed(2)}°N, ${t.layer1_psychological?.toFixed(2) ?? t.layer1_physical.longitude.toFixed(2)}°E`
      : '',
  },
  {
    id: 'data',
    icon: Database,
    label: 'L2: Data',
    color: '#10b981',
    extract: (t) => t?.layer2_data
      ? `final_dataset.csv (${t.layer2_data.dataset_rows} rows) → ${t.layer2_data.telemetry_source}`
      : 'Waiting for query',
    detail: (t) => t?.layer2_data?.feature_vars?.join(', ') || '',
  },
  {
    id: 'cognitive',
    icon: Brain,
    label: 'L3: Cognitive',
    color: '#8b5cf6',
    extract: (t) => t?.layer3_cognitive
      ? `LSTM(${t.layer3_cognitive.lstm_params}) + XGB(${t.layer3_cognitive.xgb_trees} trees)`
      : 'Models not loaded',
    detail: (t) => t?.layer3_cognitive
      ? `Stacking [${t.layer3_cognitive.stacking_weights_yield}] yield, [${t.layer3_cognitive.stacking_weights_failure}] failure`
      : '',
  },
  {
    id: 'orchestration',
    icon: Network,
    label: 'L4: Orchestration',
    color: '#f59e0b',
    extract: (t) => t?.layer4_orchestration
      ? `Query: ${t.layer4_orchestration.query_type} → Nodes: ${t.layer4_orchestration.nodes_executed}/${t.layer4_orchestration.nodes_available}`
      : 'Idle',
    detail: (t) => t?.layer4_orchestration?.route?.join(' → ') || '',
  },
];

export default function ArchitectureFlow({ trace, visible, onClose }) {
  if (!visible) return null;

  return (
    <div className="arch-overlay">
      <div className="arch-panel">
        <div className="arch-header">
          <h3 style={{ fontSize: '1rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Cpu size={18} className="text-cyan" /> Architecture Flow
          </h3>
          <button onClick={onClose} className="arch-close">
            <X size={16} />
          </button>
        </div>

        <div className="arch-layers">
          {LAYERS.map((layer, i) => {
            const Icon = layer.icon;
            const isActive = !!trace;
            const mainText = layer.extract(trace);
            const detailText = layer.detail(trace);

            return (
              <div
                key={layer.id}
                className={`arch-layer ${isActive ? 'active' : ''}`}
                style={{ '--layer-color': layer.color }}
              >
                <div className="arch-layer-line">
                  <div className="arch-layer-dot" style={{ background: layer.color, boxShadow: isActive ? `0 0 12px ${layer.color}40` : 'none' }}>
                    <Icon size={14} />
                  </div>
                  {i < LAYERS.length - 1 && <div className="arch-connector" style={{ background: isActive ? layer.color : 'rgba(255,255,255,0.08)' }} />}
                </div>
                <div className="arch-layer-content">
                  <span className="arch-layer-label" style={{ color: layer.color }}>{layer.label}</span>
                  <span className="arch-layer-text">{mainText}</span>
                  {detailText && <span className="arch-layer-detail">{detailText}</span>}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
