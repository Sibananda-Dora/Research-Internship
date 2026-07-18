"""
The orchestrator that routes queries to the right model(s).
Each model is an independent node — the router decides which to call
based on what the user needs.

Query types:
  - yield_forecast:    XGBoost only (fast, stable yield prediction)
  - failure_risk:      XGBoost classifier + biophysical triggers
  - temporal_analysis: LSTM attention weights + triggers
  - what_if:           LSTM MC Dropout (uncertainty for simulations)
  - full_diagnosis:    ALL models (default)
"""

import numpy as np
import torch
import torch.nn.functional as F
from typing import Optional, List, Dict, Any
from enum import Enum
import os, sys
from pydantic import BaseModel, ConfigDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from predict import CDTPredictor, get_biophysical_triggers, get_trigger_details, engineer_features

VAR_NAMES = ['PRECTOTCORR', 'T2M', 'RH2M', 'GWETROOT']

# ---------------------------------------------------------------------------
# Query types — routing is based on this
# ---------------------------------------------------------------------------
class QueryType(str, Enum):
    YIELD_FORECAST    = 'yield_forecast'       # XGBoost yield only
    FAILURE_RISK      = 'failure_risk'          # XGBoost classifier + triggers
    TEMPORAL_ANALYSIS = 'temporal_analysis'     # LSTM attention + triggers
    WHAT_IF           = 'what_if'               # MC Dropout
    FULL_DIAGNOSIS    = 'full_diagnosis'        # all models


# ---------------------------------------------------------------------------
# Shared state passed through the DAG
# ---------------------------------------------------------------------------
class GraphState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # --- inputs (set by caller) ---
    district: str
    season: str
    year: int
    weather_48: np.ndarray
    query_type: QueryType = QueryType.FULL_DIAGNOSIS

    # --- per-model outputs (populated by nodes) ---
    xgb_yield:      Optional[float]         = None
    xgb_fail_prob:  Optional[float]         = None
    lstm_yield:     Optional[float]         = None
    lstm_fail_prob: Optional[float]         = None
    lstm_attention: Optional[List[float]]   = None
    mc_samples:     Optional[List[float]]   = None
    mc_ci:          Optional[Dict]          = None
    mc_std:         Optional[float]         = None
    triggers:       Optional[List[str]]     = None
    trigger_details: Optional[List[dict]]   = None

    # --- final compiled response ---
    response: Optional[Dict]                = None


# ---------------------------------------------------------------------------
# Singleton predictor — shared across all nodes (loaded once)
# ---------------------------------------------------------------------------
_predictor: Optional[CDTPredictor] = None

def _get_predictor():
    global _predictor
    if _predictor is None:
        _predictor = CDTPredictor()
    return _predictor


# ===================================================================
# N O D E S — each is a pure function: GraphState → GraphState
# ===================================================================

def node_xgb_yield(state: GraphState) -> GraphState:
    """XGBoost Regressor — best at stable, fast yield prediction."""
    pred = _get_predictor()
    _, _, xgb_scaled = pred._prepare(state.weather_48, state.district, state.season, state.year)
    state.xgb_yield = float(pred.xgb_reg.predict(xgb_scaled)[0])
    return state


def node_xgb_failure(state: GraphState) -> GraphState:
    """XGBoost Classifier — best at binary failure risk."""
    pred = _get_predictor()
    _, _, xgb_scaled = pred._prepare(state.weather_48, state.district, state.season, state.year)
    state.xgb_fail_prob = float(pred.xgb_clf.predict_proba(xgb_scaled)[0, 1])
    return state


def node_lstm_attention(state: GraphState) -> GraphState:
    """LSTM + Temporal Attention — only model that produces attention weights."""
    pred = _get_predictor()
    seq_scaled, static_in, _ = pred._prepare(state.weather_48, state.district, state.season, state.year)
    seq_t = torch.tensor(seq_scaled, dtype=torch.float32)
    static_t = torch.tensor(static_in, dtype=torch.float32)
    pred.dnn.eval()
    with torch.no_grad():
        y_lstm, f_logits, attn_w = pred.dnn(seq_t, static_t)
    state.lstm_yield = float(y_lstm.item())
    state.lstm_fail_prob = float(torch.sigmoid(f_logits).item())
    state.lstm_attention = attn_w.squeeze().numpy().tolist()
    return state


def node_mc_dropout(state: GraphState) -> GraphState:
    """Monte Carlo Dropout — uncertainty quantification for what-if simulations."""
    pred = _get_predictor()
    mc = pred.monte_carlo(state.weather_48, state.district, state.season, state.year, n_samples=500)
    state.mc_samples = mc['monte_carlo_distribution']
    state.mc_ci = mc['confidence_interval']
    state.mc_std = mc['monte_carlo_std']
    return state


def node_triggers(state: GraphState) -> GraphState:
    """Biophysical rule engine — hardcoded but domain-grounded trigger detection."""
    w_dict = {}
    for vi, vn in enumerate(VAR_NAMES):
        w_dict[vn] = [float(state.weather_48[vi + 4 * w]) for w in range(12)]
    state.trigger_details = get_trigger_details(w_dict)
    state.triggers = [d['label'] for d in state.trigger_details if d['active']]
    return state


# ===================================================================
# R O U T E R — decides which nodes to run based on query type
# ===================================================================

QUERY_ROUTES = {
    QueryType.YIELD_FORECAST:    ['xgb_yield'],
    QueryType.FAILURE_RISK:      ['xgb_failure', 'triggers'],
    QueryType.TEMPORAL_ANALYSIS: ['lstm_attention', 'triggers'],
    QueryType.WHAT_IF:           ['mc_dropout', 'xgb_yield'],
    QueryType.FULL_DIAGNOSIS:    ['xgb_yield', 'xgb_failure', 'lstm_attention', 'mc_dropout', 'triggers'],
}

NODE_MAP = {
    'xgb_yield':      node_xgb_yield,
    'xgb_failure':    node_xgb_failure,
    'lstm_attention': node_lstm_attention,
    'mc_dropout':     node_mc_dropout,
    'triggers':       node_triggers,
}


DISTRICT_COORDS = {
    "Angul": (20.8444, 85.1511), "Balangir": (20.7121, 83.4893),
    "Balasore": (21.4942, 86.9317), "Bargarh": (21.3331, 83.6149),
    "Bhadrak": (21.0574, 86.5051), "Boudh": (20.8403, 84.3276),
    "Cuttack": (20.4625, 85.8830), "Deogarh": (21.5323, 84.7317),
    "Dhenkanal": (20.6621, 85.5976), "Gajapati": (18.8105, 84.1485),
    "Ganjam": (19.3150, 84.7941), "Jagatsinghpur": (20.2721, 86.1717),
    "Jajpur": (20.8521, 86.3317), "Jharsuguda": (21.8574, 84.0276),
    "Kalahandi": (19.7214, 83.0276), "Kandhamal": (20.2317, 84.2185),
    "Kendrapara": (20.5021, 86.4117), "Keonjhar": (21.6276, 85.5817),
    "Khurda": (20.1821, 85.6217), "Koraput": (18.8125, 82.7117),
    "Malkangiri": (18.3521, 81.8817), "Mayurbhanj": (21.9321, 86.7517),
    "Nabarangpur": (19.2321, 82.3517), "Nayagarh": (20.1321, 85.1017),
    "Nuapada": (20.3321, 82.5217), "Puri": (19.8125, 85.8317),
    "Rayagada": (19.1721, 83.4217), "Sambalpur": (21.4625, 83.9817),
    "Sonepur": (21.0321, 83.9117), "Sundargarh": (22.1221, 84.0317)
}


def _compile_response(state: GraphState) -> Dict:
    """Assemble final output based on what models actually ran."""
    route_names = [n for n in QUERY_ROUTES.get(state.query_type, [])]
    nodes_executed = len([n for n in route_names if getattr(state, n.replace('xgb_','xgb_').replace('lstm_','lstm_').replace('mc_','mc_'), None) is not None or True])
    lat, lng = DISTRICT_COORDS.get(state.district, (None, None))
    resp = {
        'district': state.district,
        'season': state.season,
        'year': state.year,
        'query_type': state.query_type.value,
        'active_triggers': state.triggers or [],
        'trigger_details': state.trigger_details or [],
        'trace': {
            'layer1_physical': {
                'district': state.district,
                'season': state.season,
                'year': state.year,
                'latitude': lat,
                'longitude': lng,
            },
            'layer2_data': {
                'dataset_rows': 1083,
                'telemetry_source': 'NASA POWER 1981-2026',
                'feature_vars': ['PRECTOTCORR', 'T2M', 'RH2M', 'GWETROOT'],
            },
            'layer3_cognitive': {
                'models': ['lstm', 'xgb_reg', 'xgb_clf', 'stacking'],
                'lstm_params': '56K',
                'xgb_trees': 500,
                'stacking_weights_yield': '0.2L/0.8X',
                'stacking_weights_failure': '0.68L/0.32X',
            },
            'layer4_orchestration': {
                'query_type': state.query_type.value,
                'nodes_available': len(route_names),
                'nodes_executed': nodes_executed,
                'route': route_names,
            },
        },
    }

    # Yield
    if state.xgb_yield is not None and state.lstm_yield is not None:
        pred = _get_predictor()
        if pred.meta_yield is not None:
            ensemble_yield = float(pred.meta_yield.predict(np.array([[state.lstm_yield, state.xgb_yield]]))[0])
        else:
            y_lstm_clipped = np.clip(state.lstm_yield, state.xgb_yield - 3.0, state.xgb_yield + 3.0)
            ensemble_yield = (state.xgb_yield + y_lstm_clipped) / 2
        resp['predicted_yield'] = round(ensemble_yield, 2)
        resp['yield_source'] = 'stacked_ensemble'
    elif state.xgb_yield is not None:
        resp['predicted_yield'] = round(state.xgb_yield, 2)
        resp['yield_source'] = 'xgb_regressor'
    elif state.lstm_yield is not None:
        resp['predicted_yield'] = round(state.lstm_yield, 2)
        resp['yield_source'] = 'lstm_attention'

    # Failure probability
    if state.lstm_fail_prob is not None and state.xgb_fail_prob is not None:
        pred = _get_predictor()
        if pred.meta_fail is not None:
            ensemble_fail = float(np.clip(pred.meta_fail.predict(np.array([[state.lstm_fail_prob, state.xgb_fail_prob]]))[0], 0, 1))
        else:
            ensemble_fail = (state.xgb_fail_prob + state.lstm_fail_prob) / 2
        resp['failure_probability'] = round(ensemble_fail, 3)
        resp['failure_source'] = 'stacked_ensemble'
    elif state.lstm_fail_prob is not None:
        resp['failure_probability'] = round(state.lstm_fail_prob, 3)
        resp['failure_source'] = 'lstm_attention'
    elif state.xgb_fail_prob is not None:
        resp['failure_probability'] = round(state.xgb_fail_prob, 3)
        resp['failure_source'] = 'xgb_classifier'

    if 'failure_probability' in resp:
        resp['failure_anomaly'] = 1 if resp['failure_probability'] > 0.5 else 0

    # Attention (LSTM only)
    if state.lstm_attention is not None:
        resp['attention_weights'] = state.lstm_attention

    # MC uncertainty (MC Dropout only)
    if state.mc_samples is not None:
        resp['monte_carlo_distribution'] = state.mc_samples
        resp['confidence_interval'] = state.mc_ci
        resp['monte_carlo_std'] = round(state.mc_std, 3) if state.mc_std is not None else None

    return resp


# ===================================================================
# O R C H E S T R A T O R   E N T R Y   P O I N T
# ===================================================================

def run(
    district: str,
    season: str,
    year: int,
    weather_48: np.ndarray,
    query_type: QueryType = QueryType.FULL_DIAGNOSIS,
) -> Dict:
    """
    Main entry point.  Routes to the right models and returns a response dict.

    Usage:
        result = orchestrator.run('Angul', 'Kharif', 2024, weather_vec)
        # or with a specific query type:
        result = orchestrator.run('Angul', 'Kharif', 2024, weather_vec,
                                   query_type=QueryType.YIELD_FORECAST)
    """
    state = GraphState(
        district=district,
        season=season,
        year=year,
        weather_48=weather_48,
        query_type=query_type,
    )

    route = QUERY_ROUTES.get(query_type, QUERY_ROUTES[QueryType.FULL_DIAGNOSIS])

    for node_name in route:
        node_fn = NODE_MAP[node_name]
        state = node_fn(state)

    state.response = _compile_response(state)
    return state.response
