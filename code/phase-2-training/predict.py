import numpy as np
import os, warnings
warnings.filterwarnings('ignore')

import pandas as pd
import xgboost as xgb
import torch
import torch.nn as nn
import torch.nn.functional as F
import joblib
from pathlib import Path

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
DATA_DIR = os.path.join(os.path.dirname(__file__), 'prepared_data')
TELEMETRY_DIR = os.path.join(BASE, "sources", "data", "telemetry")

device = torch.device('cpu')
VAR_NAMES = ['PRECTOTCORR', 'T2M', 'RH2M', 'GWETROOT']
SEQ_LEN = 84

# ---------- LSTM + Attention (84-step daily) ----------
class LSTMAttention(nn.Module):
    def __init__(self, input_dim=4, hidden_dim=64, n_layers=2, static_dim=11,
                 embedding_dim=8, n_districts=30, seq_len=84):
        super().__init__()
        self.embedding_dim = embedding_dim
        self.seq_len = seq_len
        self.district_embedding = nn.Embedding(n_districts, embedding_dim)
        self.encoder = nn.LSTM(input_dim, hidden_dim, n_layers, batch_first=True, dropout=0.2)
        self.pos_bias = nn.Parameter(torch.zeros(self.seq_len))
        self.attention = nn.Sequential(
            nn.Linear(hidden_dim, 32), nn.Tanh(), nn.Linear(32, 1)
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim + static_dim, 32), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(32, 16), nn.ReLU(), nn.Dropout(0.2),
        )
        self.yield_head = nn.Linear(16, 1)
        self.failure_head = nn.Linear(16, 1)

    def forward(self, x_seq, x_static):
        enc_out, _ = self.encoder(x_seq)
        enc_out_norm = F.layer_norm(enc_out, enc_out.shape[-1:])
        raw_scores = self.attention(enc_out_norm).squeeze(-1)
        scores = raw_scores + self.pos_bias[:self.seq_len].unsqueeze(0)
        attn_weights = F.softmax(scores, dim=1)
        context = torch.sum(enc_out * attn_weights.unsqueeze(-1), dim=1)
        d_idx = x_static[:, 0].long()
        d_emb = self.district_embedding(d_idx)
        rest = x_static[:, 1:]
        combined = torch.cat([context, d_emb, rest], dim=1)
        features = self.fc(combined)
        return self.yield_head(features).squeeze(-1), self.failure_head(features).squeeze(-1), attn_weights


# ---------- Biophysical triggers ----------
def get_trigger_details(weather_12x4):
    """Structured diagnostics for all four biophysical triggers.

    Each entry: id, label, active, severity, current_value, threshold, unit,
    progress, description. `progress` is 0..1+ (fraction of the threshold /
    required consecutive-run met); >1 means the threshold is exceeded.
    """
    precip = weather_12x4.get('PRECTOTCORR', [0.0] * 12)
    temp = weather_12x4.get('T2M', [20.0] * 12)
    rh = weather_12x4.get('RH2M', [70.0] * 12)
    wetness = weather_12x4.get('GWETROOT', [0.5] * 12)

    details = []

    # Submergence Flooding — peak rainfall in early vegetative weeks (W1-5)
    peak_precip = max((precip[w] for w in range(1, 6) if w < len(precip)), default=0.0)
    details.append({
        'id': 'flooding',
        'label': 'Submergence Flooding',
        'active': peak_precip > 250,
        'severity': 'warning',
        'current_value': round(peak_precip, 1),
        'threshold': 250,
        'unit': 'mm',
        'progress': round(min(peak_precip / 250.0, 1.5), 3),
        'description': 'Heavy rainfall in early vegetative phase (W1-5) risks waterlogging.',
    })

    # Drought Stress — >=3 consecutive weeks of low root-zone wetness in W3-8
    drought_run = 0
    drought_max = 0
    for w in range(3, 8):
        if w < len(wetness) and wetness[w] < 0.35:
            drought_run += 1
            drought_max = max(drought_max, drought_run)
        else:
            drought_run = 0
    details.append({
        'id': 'drought',
        'label': 'Drought Stress',
        'active': drought_max >= 3,
        'severity': 'critical',
        'current_value': drought_max,
        'threshold': 3,
        'unit': 'wks',
        'progress': round(min(drought_max / 3.0, 1.5), 3),
        'description': '3+ consecutive weeks of low soil moisture in reproductive window (W3-8).',
    })

    # Thermal Sterility — peak temperature in reproductive phase (W7-9)
    peak_temp = max((temp[w] for w in range(7, 10) if w < len(temp)), default=0.0)
    details.append({
        'id': 'thermal',
        'label': 'Thermal Sterility',
        'active': peak_temp > 34,
        'severity': 'critical',
        'current_value': round(peak_temp, 1),
        'threshold': 34,
        'unit': '°C',
        'progress': round(min(peak_temp / 34.0, 1.5), 3),
        'description': 'Spike >34°C during flowering (W7-9) causes pollen sterility.',
    })

    # Pest/Pathogen Risk — >=2 consecutive warm-humid weeks
    pest_run = 0
    pest_max = 0
    for w in range(12):
        if w < len(rh) and w < len(temp) and rh[w] > 85 and 25 <= temp[w] <= 30:
            pest_run += 1
            pest_max = max(pest_max, pest_run)
        else:
            pest_run = 0
    details.append({
        'id': 'pest',
        'label': 'Pest/Pathogen Risk',
        'active': pest_max >= 2,
        'severity': 'warning',
        'current_value': pest_max,
        'threshold': 2,
        'unit': 'wks',
        'progress': round(min(pest_max / 2.0, 1.5), 3),
        'description': 'Warm, humid conditions (RH>85%, 25-30°C) over 2+ weeks favor disease.',
    })

    return details


def get_biophysical_triggers(weather_12x4):
    """Backward-compatible: return list of active trigger label strings."""
    return [d['label'] for d in get_trigger_details(weather_12x4) if d['active']]


# ---------- Feature engineering ----------
def weekly_to_daily(weekly_12x4):
    """Upsample 12 weekly values to 84 daily by repeating each week 7 times."""
    return np.repeat(weekly_12x4, 7, axis=0)[:84]  # (84, 4)

def _load_daily_seq(district, year, season):
    """Load 84-day daily telemetry from CSV, matching prepare_data.py."""
    fpath = os.path.join(TELEMETRY_DIR, f"{district.lower()}_daily.csv")
    if not os.path.exists(fpath):
        return None
    try:
        df_tel = pd.read_csv(fpath)
        df_tel["Date_dt"] = pd.to_datetime(df_tel["Date"].astype(str), format="%Y%m%d")
        df_tel = df_tel.sort_values("Date_dt").reset_index(drop=True)
        if season.lower() == "kharif":
            start_dt = pd.Timestamp(year=year, month=6, day=15)
        else:
            start_dt = pd.Timestamp(year=year, month=11, day=1)
        mask = (df_tel["Date_dt"] >= start_dt) & (df_tel["Date_dt"] < start_dt + pd.Timedelta(days=84))
        window = df_tel[mask]
        if len(window) < 84:
            return None
        return window[["PRECTOTCORR", "T2M", "RH2M", "GWETROOT"]].values[:84].astype(np.float32)
    except Exception:
        return None

def engineer_features(weather_flat_48, district, season, year, district_enc, season_enc, season_ohe):
    w = weather_flat_48.reshape(12, 4)

    # Daily sequence for LSTM — load real daily telemetry when available
    daily = _load_daily_seq(district, year, season)
    if daily is not None:
        seq_daily = daily
    else:
        seq_daily = weekly_to_daily(w)

    # Static features for LSTM (district index + season OHE + year)
    
    try:
        d_idx = district_enc.transform([district])[0]
    except Exception as e:
        raise ValueError(f"Unknown district '{district}'. Valid districts: {list(district_enc.classes_)}") from e
    s_enc = season_enc.transform([season])[0]
    
    # Year as absolute offset from 2006 (matches prepare_data.py)
    yr_offset = year - 2006
    
    s_hot = season_ohe.transform([[season]])[0]
    
    static_in = np.array([d_idx, s_hot[0], s_hot[1], yr_offset], dtype=np.float32)

    # XGBoost engineered features (from weekly data)
    xgb_feats = []
    for vi, vn in enumerate(VAR_NAMES):
        col = w[:, vi]
        xgb_feats.extend([col.mean(), col.std(ddof=1), col.max(), col.min()])

    crit = w[3:10]
    xgb_feats.append(crit[:, 0].sum())
    xgb_feats.append(crit[:, 1].mean())
    xgb_feats.append(crit[:, 3].mean())

    t2m_mean = w[:, 1].mean()
    rh2m_mean = w[:, 2].mean()
    xgb_feats.append(t2m_mean * rh2m_mean / 100)

    # Meta-features (must match prepare_data.py order: district, season, year)
    xgb_feats.append(float(d_idx))
    xgb_feats.append(float(s_enc))
    xgb_feats.append(float(yr_offset))

    return seq_daily.astype(np.float32), static_in, np.array(xgb_feats, dtype=np.float32)


# ---------- Main predictor ----------
class CDTPredictor:
    def __init__(self):
        config = torch.load(f'{MODEL_DIR}/lstm_config.pth', map_location=device, weights_only=True)
        self.dnn = LSTMAttention(
            input_dim=config.get('input_dim', 4),
            hidden_dim=config.get('hidden_dim', 64),
            n_layers=config.get('n_layers', 2),
            static_dim=config.get('static_dim', 11),
            embedding_dim=config.get('embedding_dim', 8),
            n_districts=config.get('n_districts', 30),
            seq_len=config.get('seq_len', 84),
        )
        try:
            self.dnn.load_state_dict(
                torch.load(f'{MODEL_DIR}/lstm_final.pth', map_location=device, weights_only=True)
            )
        except:
            # Fallback to lstm_best.pt which is also the full state dict
            self.dnn.load_state_dict(
                torch.load(f'{MODEL_DIR}/lstm_best.pt', map_location=device, weights_only=True)
            )
        self.dnn.eval()

        self.xgb_reg = xgb.XGBRegressor()
        self.xgb_reg.load_model(f'{MODEL_DIR}/xgb_regressor.json')

        self.xgb_clf = xgb.XGBClassifier()
        self.xgb_clf.load_model(f'{MODEL_DIR}/xgb_classifier.json')

        self.seq_scaler = joblib.load(f'{DATA_DIR}/seq_scaler.pkl')
        self.xgb_scaler = joblib.load(f'{DATA_DIR}/xgb_scaler.pkl')

        # Load stacking meta-learners (Fix #5); fallback to naive average if not found
        meta_yield_path = os.path.join(MODEL_DIR, 'meta_yield.pkl')
        meta_fail_path = os.path.join(MODEL_DIR, 'meta_fail.pkl')
        self.meta_yield = joblib.load(meta_yield_path) if os.path.exists(meta_yield_path) else None
        self.meta_fail = joblib.load(meta_fail_path) if os.path.exists(meta_fail_path) else None
        
        self.district_enc = joblib.load(f'{DATA_DIR}/district_encoder.pkl')
        self.season_enc = joblib.load(f'{DATA_DIR}/season_encoder.pkl')
        self.season_ohe = joblib.load(f'{DATA_DIR}/season_ohe.pkl')

    def _prepare(self, weather_flat_48, district, season, year):
        seq_daily, static_in, xgb_in = engineer_features(
            weather_flat_48, district, season, year,
            self.district_enc, self.season_enc, self.season_ohe
        )

        seq_scaled = self.seq_scaler.transform(seq_daily.reshape(-1, 4)).reshape(1, SEQ_LEN, 4)
        static_in = static_in.reshape(1, -1)
        xgb_scaled = self.xgb_scaler.transform(xgb_in.reshape(1, -1))

        return seq_scaled, static_in, xgb_scaled

    def predict(self, weather_flat_48, district, season, year):
        seq_scaled, static_in, xgb_scaled = self._prepare(weather_flat_48, district, season, year)
        seq_t = torch.tensor(seq_scaled, dtype=torch.float32)
        static_t = torch.tensor(static_in, dtype=torch.float32)

        # XGBoost
        y_xgb = float(self.xgb_reg.predict(xgb_scaled)[0])
        f_xgb_prob = float(self.xgb_clf.predict_proba(xgb_scaled)[0, 1])

        # LSTM
        self.dnn.eval()
        with torch.no_grad():
            y_lstm, f_logits, attn_w = self.dnn(seq_t, static_t)
            y_lstm = y_lstm.item()
            f_lstm_prob = torch.sigmoid(f_logits).item()
            attn = attn_w.squeeze().numpy().tolist()

        # Ensemble via stacking meta-learner (Fix #5) or fallback to naive average
        if self.meta_yield is not None:
            ensemble_yield = float(self.meta_yield.predict(np.array([[y_lstm, y_xgb]]))[0])
        else:
            y_lstm_clipped = np.clip(y_lstm, y_xgb - 3.0, y_xgb + 3.0)
            ensemble_yield = (y_xgb + y_lstm_clipped) / 2

        if self.meta_fail is not None:
            ensemble_fail = float(np.clip(self.meta_fail.predict(np.array([[f_lstm_prob, f_xgb_prob]]))[0], 0, 1))
        else:
            ensemble_fail = (f_xgb_prob + f_lstm_prob) / 2

        f_anomaly = 1 if ensemble_fail > 0.5 else 0

        # Uncertainty via ensemble spread (heuristic 90% CI)
        yield_spread = abs(y_lstm - y_xgb)
        ci_lower = max(0, ensemble_yield - yield_spread)
        ci_upper = ensemble_yield + yield_spread

        # Triggers
        w_dict = {}
        for vi, vn in enumerate(VAR_NAMES):
            w_dict[vn] = [float(weather_flat_48[vi + 4 * w]) for w in range(12)]
        trigger_details = get_trigger_details(w_dict)
        triggers = [d['label'] for d in trigger_details if d['active']]

        return {
            'predicted_yield': round(ensemble_yield, 2),
            'failure_probability': round(ensemble_fail, 3),
            'failure_anomaly': f_anomaly,
            'attention_weights': attn,
            'active_triggers': triggers,
            'trigger_details': trigger_details,
            'xgb_yield': round(y_xgb, 2),
            'lstm_yield': round(y_lstm, 2),
            'monte_carlo_distribution': [],
            'confidence_interval': {'lower': round(ci_lower, 2), 'upper': round(ci_upper, 2)}
        }

    def _enable_dropout(self):
        for m in self.dnn.modules():
            if isinstance(m, nn.Dropout):
                m.training = True

    def monte_carlo(self, weather_flat_48, district, season, year, n_samples=500):
        """Monte Carlo Dropout uncertainty quantification.

        Fix #3: Removed fake XGB Gaussian noise injection. The MC distribution now contains
        only principled Bayesian uncertainty from LSTM dropout sampling. XGBoost provides a
        deterministic anchor point but does NOT corrupt the uncertainty distribution.
        """
        seq_scaled, static_in, xgb_scaled = self._prepare(weather_flat_48, district, season, year)
        seq_t = torch.tensor(seq_scaled, dtype=torch.float32)
        static_t = torch.tensor(static_in, dtype=torch.float32)

        self.dnn.eval()
        self._enable_dropout()
        with torch.no_grad():
            yields_mc = []
            fails_mc = []
            attns_mc = []
            for _ in range(n_samples):
                y, f, attn = self.dnn(seq_t, static_t)
                yields_mc.append(y.item())
                fails_mc.append(torch.sigmoid(f).item())
                attns_mc.append(attn.squeeze().numpy())

        yields_mc = np.array(yields_mc)
        fails_mc = np.array(fails_mc)
        attns_mc = np.array(attns_mc)

        # XGBoost deterministic anchor — used for sanity-clipping only, NOT injected as noise
        xgb_y = float(self.xgb_reg.predict(xgb_scaled)[0])
        xgb_f = float(self.xgb_clf.predict_proba(xgb_scaled)[0, 1])

        # Blend MC samples with XGBoost via stacking meta-learner if available
        if self.meta_yield is not None:
            # Apply stacking to each MC sample individually for proper uncertainty propagation
            stacked_yields = np.array([
                self.meta_yield.predict(np.array([[y_mc, xgb_y]]))[0]
                for y_mc in yields_mc
            ])
        else:
            # Fallback: clip and average with XGBoost
            stacked_yields = np.clip(yields_mc, xgb_y - 5.0, xgb_y + 5.0)
            stacked_yields = (stacked_yields + xgb_y) / 2

        if self.meta_fail is not None:
            stacked_fails = np.array([
                np.clip(self.meta_fail.predict(np.array([[f_mc, xgb_f]]))[0], 0, 1)
                for f_mc in fails_mc
            ])
        else:
            stacked_fails = (fails_mc + xgb_f) / 2

        return {
            'predicted_yield': float(np.mean(stacked_yields)),
            'failure_probability': float(np.mean(stacked_fails)),
            'failure_anomaly': int(np.mean(stacked_fails) > 0.5),
            'monte_carlo_distribution': stacked_yields.tolist(),
            'confidence_interval': {
                'lower': float(np.percentile(stacked_yields, 5)),
                'upper': float(np.percentile(stacked_yields, 95))
            },
            'monte_carlo_std': float(np.std(stacked_yields)),
            'attention_weights': attns_mc.mean(axis=0).tolist(),
        }


if __name__ == '__main__':
    print('=== Predictor Test (84-step daily model) ===')
    predictor = CDTPredictor()

    print('\n--- Test 1: Angul Kharif 2024 (real daily CSV available) ---')
    r = predictor.predict(np.random.rand(48).astype(np.float32), 'Angul', 'Kharif', 2024)
    print(f'XGBoost yield: {r["xgb_yield"]}, LSTM yield: {r["lstm_yield"]}')
    print(f'Ensemble: {r["predicted_yield"]} Q/Acre, fail={r["failure_probability"]:.2%}')
    print(f'Active triggers: {r["active_triggers"]}')
    aw = np.array(r['attention_weights'])
    print(f'Attention shape: {aw.shape}')
    top3_days = np.argsort(aw)[-3:][::-1]
    print(f'Top-3 attention days: {top3_days} — unique daily values expected (real CSV)')

    print('\n--- Test 2: MC Dropout ---')
    mc = predictor.monte_carlo(np.random.rand(48).astype(np.float32), 'Angul', 'Kharif', 2024, n_samples=200)
    print(f'MC: yield={mc["predicted_yield"]:.2f} +/- {mc["monte_carlo_std"]:.2f}')
    print(f'MC 90% CI: [{mc["confidence_interval"]["lower"]:.2f}, {mc["confidence_interval"]["upper"]:.2f}]')

    print('\n--- Test 3: Verify daily vs weekly-upsampled input ---')
    dummy = np.random.rand(48).astype(np.float32)
    real_r = predictor.predict(dummy, 'Angul', 'Kharif', 2024)
    _, static_in, _ = predictor._prepare(dummy, 'Angul', 'Kharif', 2024)
    seq_scaled, _, _ = predictor._prepare(dummy, 'Angul', 'Kharif', 2024)
    seq_84 = predictor.seq_scaler.inverse_transform(seq_scaled.reshape(-1, 4))
    unique_counts = [len(np.unique(seq_84[w*7:(w+1)*7], axis=0)) for w in range(12)]
    n_weeks_nonuniform = sum(1 for c in unique_counts if c > 1)
    print(f'  Weeks with non-uniform daily values (real data): {n_weeks_nonuniform}/12 '
          f'({"PASS" if n_weeks_nonuniform > 6 else "FAIL"}) — if all weeks are 1, input is upsampled not real')

    print('\nDone.')
