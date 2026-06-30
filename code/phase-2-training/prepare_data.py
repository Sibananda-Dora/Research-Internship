import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
import joblib
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TELEMETRY_DIR = os.path.join(BASE, "sources", "data", "telemetry")
np.random.seed(42)

df = pd.read_csv(f'{BASE}/sources/data/final_dataset.csv')
assert df['Is_Interpolated'].sum() == 0, 'Dataset still has interpolated rows!'
weather_cols = [c for c in df.columns if c.startswith('W')]

print(f'Loaded {df.shape[0]} clean samples')

# Build 12x4 weekly sequences (from CSV weekly columns)
var_names = ['PRECTOTCORR', 'T2M', 'RH2M', 'GWETROOT']
weather_seq_weekly = np.zeros((len(df), 12, 4))
for i, row in df.iterrows():
    for w in range(12):
        for v, var in enumerate(var_names):
            weather_seq_weekly[i, w, v] = row[f'W{w+1}_{var}']

# Build 84x4 daily sequences (from telemetry CSVs)
def load_daily_seq(district, year, season):
    fpath = os.path.join(TELEMETRY_DIR, f"{district.lower()}_daily.csv")
    if not os.path.exists(fpath):
        return None
    df_tel = pd.read_csv(fpath)
    df_tel["Date_dt"] = pd.to_datetime(df_tel["Date"].astype(str), format="%Y%m%d")
    df_tel = df_tel.sort_values("Date_dt").reset_index(drop=True)
    if season.endswith("Kharif") or season == "Kharif":
        start_dt = pd.Timestamp(year=year, month=6, day=15)
    else:
        start_dt = pd.Timestamp(year=year, month=11, day=1)
    mask = (df_tel["Date_dt"] >= start_dt) & (df_tel["Date_dt"] < start_dt + pd.Timedelta(days=84))
    window = df_tel[mask]
    if len(window) < 84:
        return None
    return window[["PRECTOTCORR","T2M","RH2M","GWETROOT"]].values[:84].astype(np.float32)

weather_seq_daily = np.zeros((len(df), 84, 4))
daily_missing = 0
for i, row in df.iterrows():
    seq = load_daily_seq(row["District"], row["Year"], row["Season"])
    if seq is not None:
        weather_seq_daily[i] = seq
    else:
        weather_seq_daily[i] = np.repeat(weather_seq_weekly[i], 7, axis=0)[:84]
        daily_missing += 1

if daily_missing > 0:
    print(f"  Warning: {daily_missing} rows missing daily telemetry (upsampled from weekly)")

# Label Encoders (for XGBoost meta-features)
district_enc = LabelEncoder()
season_enc = LabelEncoder()
district_enc.fit(df['District'])
season_enc.fit(df['Season'])

# Static features: district index (0-29) + season one-hot + year as absolute offset
# Using learned nn.Embedding(30, 8) in the model instead of 30-dim OHE
season_ohe = OneHotEncoder(sparse_output=False, handle_unknown='ignore')

season_hot = season_ohe.fit_transform(df[['Season']])
year_abs = (df['Year'] - df['Year'].min()).values.reshape(-1, 1).astype(np.float32)

static = np.column_stack([
    district_enc.transform(df['District']).astype(np.float32),
    season_hot.astype(np.float32),
    year_abs,
])

y_yield = df['Yield_Q_Acre'].values
y_failure = df['Failure_Anomaly'].values

# Engineered features for XGBoost (from weekly)
eng_features = []
for var in ['PRECTOTCORR', 'T2M', 'RH2M', 'GWETROOT']:
    var_cols = [c for c in weather_cols if var in c]
    eng_features.append(df[var_cols].mean(axis=1).values)
    eng_features.append(df[var_cols].std(axis=1).values)
    eng_features.append(df[var_cols].max(axis=1).values)
    eng_features.append(df[var_cols].min(axis=1).values)

crit_weeks = range(4, 11)
eng_features.append(df[[c for c in weather_cols if 'PRECTOTCORR' in c and any(c.startswith(f'W{w}_') for w in crit_weeks)]].sum(axis=1).values)
eng_features.append(df[[c for c in weather_cols if 'T2M' in c and any(c.startswith(f'W{w}_') for w in crit_weeks)]].mean(axis=1).values)
eng_features.append(df[[c for c in weather_cols if 'GWETROOT' in c and any(c.startswith(f'W{w}_') for w in crit_weeks)]].mean(axis=1).values)

t2m_mean = df['T2M_mean'] if 'T2M_mean' in df.columns else df[[c for c in weather_cols if 'T2M' in c]].mean(axis=1)
rh2m_mean = df['RH2M_mean'] if 'RH2M_mean' in df.columns else df[[c for c in weather_cols if 'RH2M' in c]].mean(axis=1)
eng_features.append((t2m_mean * rh2m_mean / 100).values)

xgb_features = np.column_stack(eng_features)

# Add meta-features (district, season, year)
xgb_features = np.column_stack([
    xgb_features,
    district_enc.transform(df['District']),
    season_enc.transform(df['Season']),
    (df['Year'] - df['Year'].min()).values
])

# Random 80/10/10 split: train / val (stacking calibration) / test
# Validation is held-out from training set to avoid test leakage in stacking
te_size = 0.2
va_size = 0.1  # 10% of training for stacking calibration

split = train_test_split(
    weather_seq_weekly, weather_seq_daily, static, xgb_features, y_yield, y_failure,
    test_size=te_size, random_state=42
)
(X_seq_w_tr, X_seq_w_te, X_seq_d_tr, X_seq_d_te, X_static_tr, X_static_te,
 X_xgb_tr, X_xgb_te, y_y_tr, y_y_te, y_f_tr, y_f_te) = split

# Further split training into train_final and val (for stacking calibration)
split2 = train_test_split(
    X_seq_w_tr, X_seq_d_tr, X_static_tr, X_xgb_tr, y_y_tr, y_f_tr,
    test_size=va_size, random_state=42
)
(X_seq_w_tr_final, X_seq_w_va, X_seq_d_tr_final, X_seq_d_va,
 X_static_tr_final, X_static_va, X_xgb_tr_final, X_xgb_va,
 y_y_tr_final, y_y_va, y_f_tr_final, y_f_va) = split2

print(f'Random split: train {X_seq_w_tr_final.shape[0]}, '
      f'val (stacking) {X_seq_w_va.shape[0]}, test {X_seq_w_te.shape[0]}')
print(f'Failure rate train: {y_f_tr_final.mean():.2%}, val: {y_f_va.mean():.2%}, test: {y_f_te.mean():.2%}')

# Scale LSTM weekly sequence inputs
seq_scaler = StandardScaler()
seq_w_shape = X_seq_w_tr.shape
X_seq_w_tr_s = seq_scaler.fit_transform(X_seq_w_tr.reshape(-1, 4)).reshape(seq_w_shape)
X_seq_w_tr_final_s = seq_scaler.transform(X_seq_w_tr_final.reshape(-1, 4)).reshape(X_seq_w_tr_final.shape)
X_seq_w_va_s = seq_scaler.transform(X_seq_w_va.reshape(-1, 4)).reshape(X_seq_w_va.shape)
X_seq_w_te_s = seq_scaler.transform(X_seq_w_te.reshape(-1, 4)).reshape(X_seq_w_te.shape)

# Scale daily sequence inputs (same scaler)
X_seq_d_tr_final_s = seq_scaler.transform(X_seq_d_tr_final.reshape(-1, 4)).reshape(X_seq_d_tr_final.shape)
X_seq_d_va_s = seq_scaler.transform(X_seq_d_va.reshape(-1, 4)).reshape(X_seq_d_va.shape)
X_seq_d_te_s = seq_scaler.transform(X_seq_d_te.reshape(-1, 4)).reshape(X_seq_d_te.shape)

# Scale XGBoost features
xgb_scaler = StandardScaler()
X_xgb_tr_s = xgb_scaler.fit_transform(X_xgb_tr)
X_xgb_tr_final_s = xgb_scaler.transform(X_xgb_tr_final)
X_xgb_va_s = xgb_scaler.transform(X_xgb_va)
X_xgb_te_s = xgb_scaler.transform(X_xgb_te)

out = os.path.join(os.path.dirname(__file__), 'prepared_data')
os.makedirs(out, exist_ok=True)

np.save(f'{out}/X_seq_train.npy', X_seq_w_tr_final_s)
np.save(f'{out}/X_seq_val.npy', X_seq_w_va_s)
np.save(f'{out}/X_seq_test.npy', X_seq_w_te_s)

np.save(f'{out}/X_seq_daily_train.npy', X_seq_d_tr_final_s)
np.save(f'{out}/X_seq_daily_val.npy', X_seq_d_va_s)
np.save(f'{out}/X_seq_daily_test.npy', X_seq_d_te_s)

np.save(f'{out}/X_static_train.npy', X_static_tr_final)
np.save(f'{out}/X_static_val.npy', X_static_va)
np.save(f'{out}/X_static_test.npy', X_static_te)
np.save(f'{out}/X_xgb_train.npy', X_xgb_tr_final_s)
np.save(f'{out}/X_xgb_val.npy', X_xgb_va_s)
np.save(f'{out}/X_xgb_test.npy', X_xgb_te_s)
np.save(f'{out}/y_yield_train.npy', y_y_tr_final)
np.save(f'{out}/y_yield_val.npy', y_y_va)
np.save(f'{out}/y_yield_test.npy', y_y_te)
np.save(f'{out}/y_fail_train.npy', y_f_tr_final)
np.save(f'{out}/y_fail_val.npy', y_f_va)
np.save(f'{out}/y_fail_test.npy', y_f_te)

joblib.dump(seq_scaler, f'{out}/seq_scaler.pkl')
joblib.dump(xgb_scaler, f'{out}/xgb_scaler.pkl')
joblib.dump(district_enc, f'{out}/district_encoder.pkl')
joblib.dump(season_enc, f'{out}/season_encoder.pkl')
joblib.dump(season_ohe, f'{out}/season_ohe.pkl')

print(f'Files saved to {out}')
print('Done.')
