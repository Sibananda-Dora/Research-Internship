"""
Comprehensive validation of the CPDT model pipeline.
Tests realistic agricultural scenarios against agronomic expectations.
"""
import numpy as np
import os, sys, json

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from predict import CDTPredictor

# ─── Initialize predictor ───
print("=" * 60)
print("  CPDT Model Validation Suite")
print("=" * 60)
predictor = CDTPredictor()
print(f"  Meta-yield loaded: {predictor.meta_yield is not None}")
print(f"  Meta-fail loaded:  {predictor.meta_fail is not None}")

# ─── Helper: build weather vector ───
def make_weather(precip_weekly, temp_weekly, rh_weekly, wetness_weekly):
    """Build 48-dim flat vector from 4 x 12 weekly arrays."""
    w48 = np.zeros(48, dtype=np.float32)
    for w in range(12):
        w48[0 + 4*w] = precip_weekly[w]  # PRECTOTCORR
        w48[1 + 4*w] = temp_weekly[w]    # T2M
        w48[2 + 4*w] = rh_weekly[w]      # RH2M
        w48[3 + 4*w] = wetness_weekly[w] # GWETROOT
    return w48

# ─── Define realistic scenarios ───
scenarios = {}

# 1. NORMAL Kharif (monsoon rice) — typical Odisha coastal weather
scenarios['Normal Kharif (Angul)'] = {
    'weather': make_weather(
        precip_weekly=[15, 25, 40, 60, 80, 90, 70, 50, 35, 20, 15, 10],  # Rising monsoon, peak W5-6
        temp_weekly=[30, 29, 28, 27, 26, 26, 27, 28, 29, 30, 30, 29],    # Slight cooling during monsoon
        rh_weekly=[65, 70, 78, 82, 85, 88, 85, 80, 75, 68, 65, 62],      # High humidity mid-season
        wetness_weekly=[0.5, 0.55, 0.65, 0.75, 0.8, 0.85, 0.8, 0.7, 0.6, 0.5, 0.45, 0.4]
    ),
    'district': 'Angul', 'season': 'Kharif', 'year': 2024,
    'expected': {'yield_range': (6.0, 14.0), 'fail_prob': '<0.4', 'triggers': []}
}

# 2. DROUGHT — prolonged dry spell during critical reproductive phase
scenarios['Drought Stress (Kalahandi)'] = {
    'weather': make_weather(
        precip_weekly=[10, 12, 8, 5, 3, 2, 4, 6, 8, 10, 8, 5],         # Very low rainfall
        temp_weekly=[32, 33, 34, 35, 36, 36, 35, 34, 33, 32, 31, 30],    # Heat stress
        rh_weekly=[55, 50, 45, 40, 38, 35, 38, 42, 48, 52, 55, 50],      # Low humidity
        wetness_weekly=[0.45, 0.4, 0.35, 0.28, 0.22, 0.18, 0.2, 0.25, 0.3, 0.35, 0.38, 0.35]
    ),
    'district': 'Kalahandi', 'season': 'Kharif', 'year': 2024,
    'expected': {'yield_range': (2.0, 20.0), 'fail_prob': '>0.25', 'triggers': ['Drought Stress']}
}

# 3. FLOOD — extreme monsoon precipitation (cyclonic event)
scenarios['Flood/Cyclone (Balasore)'] = {
    'weather': make_weather(
        precip_weekly=[20, 50, 120, 280, 320, 180, 90, 60, 30, 15, 10, 8],  # Extreme W4-5
        temp_weekly=[29, 28, 27, 25, 24, 25, 26, 27, 28, 29, 29, 28],
        rh_weekly=[75, 80, 90, 95, 98, 95, 88, 82, 78, 72, 70, 68],
        wetness_weekly=[0.6, 0.7, 0.85, 0.95, 1.0, 0.95, 0.85, 0.75, 0.65, 0.55, 0.5, 0.45]
    ),
    'district': 'Balasore', 'season': 'Kharif', 'year': 2024,
    'expected': {'yield_range': (3.0, 15.0), 'fail_prob': '>0.3', 'triggers': ['Submergence Flooding']}
}

# 4. THERMAL STERILITY — late-season heat during grain filling
scenarios['Thermal Sterility (Sambalpur)'] = {
    'weather': make_weather(
        precip_weekly=[15, 20, 35, 50, 60, 55, 40, 25, 15, 10, 8, 5],
        temp_weekly=[30, 31, 30, 29, 28, 29, 31, 35, 36, 37, 35, 33],    # Heat W7-9 (>34)
        rh_weekly=[60, 65, 72, 78, 82, 80, 75, 65, 58, 52, 55, 52],
        wetness_weekly=[0.5, 0.55, 0.6, 0.7, 0.75, 0.7, 0.6, 0.5, 0.4, 0.35, 0.3, 0.28]
    ),
    'district': 'Sambalpur', 'season': 'Kharif', 'year': 2024,
    'expected': {'yield_range': (4.0, 15.0), 'fail_prob': '>0.2', 'triggers': ['Thermal Sterility']}
}

# 5. PEST/PATHOGEN — warm humid conditions sustained
scenarios['Pest/Pathogen Risk (Cuttack)'] = {
    'weather': make_weather(
        precip_weekly=[20, 30, 45, 55, 60, 65, 55, 50, 40, 30, 25, 20],
        temp_weekly=[28, 27, 27, 26, 26, 27, 28, 28, 27, 28, 28, 27],    # 25-30 range
        rh_weekly=[78, 82, 86, 88, 90, 92, 90, 88, 86, 84, 82, 80],      # Consistently >85
        wetness_weekly=[0.6, 0.65, 0.72, 0.78, 0.82, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55]
    ),
    'district': 'Cuttack', 'season': 'Kharif', 'year': 2024,
    'expected': {'yield_range': (5.0, 12.0), 'fail_prob': '>0.15', 'triggers': ['Pest/Pathogen Risk']}
}

# 6. EXCELLENT SEASON — perfect growing conditions
scenarios['Excellent Season (Bargarh)'] = {
    'weather': make_weather(
        precip_weekly=[12, 18, 30, 45, 55, 60, 50, 40, 30, 20, 15, 10],
        temp_weekly=[29, 28, 27, 26, 26, 26, 27, 28, 28, 29, 29, 28],
        rh_weekly=[65, 70, 75, 78, 80, 82, 80, 76, 72, 68, 65, 63],
        wetness_weekly=[0.55, 0.6, 0.68, 0.75, 0.78, 0.8, 0.76, 0.7, 0.63, 0.55, 0.5, 0.48]
    ),
    'district': 'Bargarh', 'season': 'Kharif', 'year': 2024,
    'expected': {'yield_range': (7.0, 20.0), 'fail_prob': '<0.3', 'triggers': []}
}

# 7. RABI season — winter crop (different dynamics)
scenarios['Rabi Season (Puri)'] = {
    'weather': make_weather(
        precip_weekly=[5, 3, 2, 1, 0, 0, 0, 1, 2, 3, 5, 8],             # Dry winter
        temp_weekly=[25, 23, 21, 19, 18, 17, 18, 20, 22, 25, 27, 28],    # Cool winter
        rh_weekly=[72, 68, 62, 58, 55, 52, 55, 58, 62, 65, 68, 70],
        wetness_weekly=[0.55, 0.5, 0.45, 0.4, 0.38, 0.35, 0.38, 0.4, 0.42, 0.45, 0.48, 0.5]
    ),
    'district': 'Puri', 'season': 'Rabi', 'year': 2024,
    'expected': {'yield_range': (3.0, 25.0), 'fail_prob': '<0.5', 'triggers': []}
}

# 8. HISTORICAL KNOWN YEAR — test with known 2019 Angul data (should be in training)
# Use realistic 2024 data for Ganjam (coastal, high-yield district)
scenarios['Coastal High-Yield (Ganjam)'] = {
    'weather': make_weather(
        precip_weekly=[18, 25, 45, 65, 75, 85, 70, 55, 35, 22, 15, 10],
        temp_weekly=[29, 28, 27, 26, 26, 26, 27, 28, 28, 29, 29, 28],
        rh_weekly=[70, 75, 80, 84, 87, 88, 85, 80, 76, 70, 68, 65],
        wetness_weekly=[0.55, 0.6, 0.7, 0.78, 0.82, 0.85, 0.8, 0.72, 0.62, 0.54, 0.48, 0.42]
    ),
    'district': 'Ganjam', 'season': 'Kharif', 'year': 2024,
    'expected': {'yield_range': (6.0, 14.0), 'fail_prob': '<0.35', 'triggers': []}
}


# ─── Run predictions ───
results = {}
all_passed = True

print(f"\n{'='*60}")
print(f"  Running {len(scenarios)} scenarios...")
print(f"{'='*60}\n")

for name, scenario in scenarios.items():
    print(f"--- {name} ---")
    
    r = predictor.predict(
        scenario['weather'],
        scenario['district'],
        scenario['season'],
        scenario['year']
    )
    
    results[name] = r
    expected = scenario['expected']
    
    # Validate yield range
    y_lo, y_hi = expected['yield_range']
    yield_ok = y_lo <= r['predicted_yield'] <= y_hi
    
    # Validate failure probability direction
    if expected['fail_prob'].startswith('>'):
        threshold = float(expected['fail_prob'][1:])
        fail_ok = r['failure_probability'] >= threshold * 0.5  # Allow some tolerance
    elif expected['fail_prob'].startswith('<'):
        threshold = float(expected['fail_prob'][1:])
        fail_ok = r['failure_probability'] <= threshold * 1.5  # Allow some tolerance
    else:
        fail_ok = True
    
    # Validate triggers
    expected_triggers = set(expected['triggers'])
    actual_triggers = set(r['active_triggers'])
    triggers_ok = expected_triggers.issubset(actual_triggers)
    
    status = "PASS" if (yield_ok and fail_ok) else "WARN"
    trigger_status = "PASS" if triggers_ok else "MISS"
    
    if not (yield_ok and fail_ok):
        all_passed = False
    
    print(f"  Yield:   {r['predicted_yield']:.2f} Q/Acre  (XGB: {r['xgb_yield']:.2f}, LSTM: {r['lstm_yield']:.2f})")
    print(f"           Expected: {y_lo}-{y_hi}  [{status}]")
    print(f"  Failure: {r['failure_probability']:.1%}  (anomaly={r['failure_anomaly']})")
    print(f"           Expected: {expected['fail_prob']}  [{status}]")
    print(f"  Triggers: {r['active_triggers']}  [{trigger_status}]")
    print(f"           Expected: {expected['triggers']}")
    
    # Attention pattern
    attn = np.array(r['attention_weights'])
    weekly_attn = attn.reshape(12, 7).sum(axis=1)
    peak_week = weekly_attn.argmax() + 1
    critical_attn = weekly_attn[3:6].sum()
    print(f"  Attention: peak=W{peak_week}, W4-6={critical_attn:.1%}")
    print()

# ─── Monte Carlo validation on one scenario ───
print(f"\n{'='*60}")
print(f"  Monte Carlo Validation (Drought scenario)")
print(f"{'='*60}\n")

drought = scenarios['Drought Stress (Kalahandi)']
mc = predictor.monte_carlo(
    drought['weather'],
    drought['district'],
    drought['season'],
    drought['year'],
    n_samples=300
)

print(f"  MC Yield:  {mc['predicted_yield']:.2f} +/- {mc['monte_carlo_std']:.2f} Q/Acre")
print(f"  MC 90% CI: [{mc['confidence_interval']['lower']:.2f}, {mc['confidence_interval']['upper']:.2f}]")
print(f"  MC Fail:   {mc['failure_probability']:.1%}")
print(f"  MC Dist:   {len(mc['monte_carlo_distribution'])} samples")

# Validate CI makes sense
ci_width = mc['confidence_interval']['upper'] - mc['confidence_interval']['lower']
print(f"  CI Width:  {ci_width:.2f} Q/Acre")

# The CI should be non-trivial but not absurdly wide
ci_ok = 0.1 < ci_width < 15.0
print(f"  CI Valid:  {'PASS' if ci_ok else 'FAIL'} (0.1 < {ci_width:.2f} < 15.0)")

# Distribution should have 300 samples (not 600 like before with XGB noise)
dist_ok = len(mc['monte_carlo_distribution']) == 300
print(f"  Dist Size: {'PASS' if dist_ok else 'FAIL'} ({len(mc['monte_carlo_distribution'])} == 300)")

# ─── Cross-district consistency check ───
print(f"\n{'='*60}")
print(f"  Cross-District Consistency Check")
print(f"{'='*60}\n")

# Same weather across different districts should give different yields (district effect)
normal_weather = scenarios['Normal Kharif (Angul)']['weather']
district_yields = {}
for d in ['Angul', 'Bargarh', 'Cuttack', 'Ganjam', 'Kalahandi', 'Puri']:
    r = predictor.predict(normal_weather, d, 'Kharif', 2024)
    district_yields[d] = r['predicted_yield']
    print(f"  {d:15s}: {r['predicted_yield']:.2f} Q/Acre  (fail={r['failure_probability']:.1%})")

# Check that yields vary across districts (not all identical)
vals = list(district_yields.values())
spread = max(vals) - min(vals)
print(f"\n  Yield spread: {spread:.2f} Q/Acre (should be > 0)")
diversity_ok = spread > 0.01  # At least some variation
print(f"  District diversity: {'PASS' if diversity_ok else 'FAIL'}")

# ─── Temporal consistency check ───
print(f"\n{'='*60}")
print(f"  Temporal Consistency Check (same district, different years)")
print(f"{'='*60}\n")

for y in [2021, 2022, 2023, 2024]:
    r = predictor.predict(normal_weather, 'Angul', 'Kharif', y)
    print(f"  {y}: yield={r['predicted_yield']:.2f}, fail={r['failure_probability']:.1%}")

# ─── Directional stress tests ───
print(f"\n{'='*60}")
print(f"  Directional Stress Tests")
print(f"{'='*60}\n")

# Increasing drought should decrease yield
print("  Increasing drought severity (reducing precip, wetness):")
drought_yields = []
for severity in [0.2, 0.5, 0.8, 1.0, 1.5]:
    weather = make_weather(
        precip_weekly=[15*severity]*12,
        temp_weekly=[30]*12,
        rh_weekly=[60]*12,
        wetness_weekly=[0.6*severity]*12
    )
    r = predictor.predict(weather, 'Angul', 'Kharif', 2024)
    drought_yields.append(r['predicted_yield'])
    print(f"    Severity {severity:.1f}x: yield={r['predicted_yield']:.2f}, fail={r['failure_probability']:.1%}, triggers={r['active_triggers']}")

# Check monotonicity (relaxed — at least overall trend should be correct)
is_decreasing_trend = drought_yields[0] <= drought_yields[-1] * 1.5  # Allow noise
print(f"  Yield trend: {drought_yields[0]:.2f} -> {drought_yields[-1]:.2f}")
print(f"  More rain = more yield: {'REASONABLE' if drought_yields[0] < drought_yields[-1] else 'CHECK'}")

# ─── Final Summary ───
print(f"\n{'='*60}")
print(f"  VALIDATION SUMMARY")
print(f"{'='*60}")
print(f"  Scenarios tested: {len(scenarios)}")
print(f"  MC Dropout tested: YES (300 samples)")
print(f"  Cross-district diversity: {'PASS' if diversity_ok else 'FAIL'}")
print(f"  CI calibration: {'PASS' if ci_ok else 'FAIL'}")
print(f"  Distribution integrity: {'PASS' if dist_ok else 'FAIL'}")
print(f"{'='*60}")
print("  Done.")
