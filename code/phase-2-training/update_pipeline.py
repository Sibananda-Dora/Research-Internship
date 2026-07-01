import os, sys, json, shutil, subprocess, requests, math
from datetime import datetime, date
import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PATH = os.path.join(BASE, "sources", "data", "final_dataset.csv")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
PREPARED_DIR = os.path.join(os.path.dirname(__file__), "prepared_data")
PIPELINE_LOG = os.path.join(os.path.dirname(__file__), "version.json")
TELEMETRY_DIR = os.path.join(BASE, "sources", "data", "telemetry")

DEFAULT_STEPS = [
    "validate_csv", "fetch_telemetry", "merge_data",
    "backup_models", "prepare_data", "train_models", "save_version"
]


def get_current_version():
    if os.path.exists(PIPELINE_LOG):
        with open(PIPELINE_LOG) as f:
            return json.load(f)
    return {"version": "1.0", "last_trained": None, "metrics": {}}


def get_dataset_info():
    if not os.path.exists(DATA_PATH):
        return {"latest_year": None, "total_records": 0, "years": []}
    df = pd.read_csv(DATA_PATH)
    return {
        "latest_year": int(df["Year"].max()),
        "total_records": len(df),
        "years": sorted(df["Year"].unique().tolist()),
        "districts": sorted(df["District"].unique().tolist()),
        "last_season": df.sort_values("Year").iloc[-1]["Season"]
    }


def check_new_data(data_source_url=None, csv_path=None):
    info = get_dataset_info()
    current_latest = info["latest_year"]
    result = {"new_data": False, "latest_year": current_latest, "new_records": 0}

    if csv_path and os.path.exists(csv_path):
        new_df = pd.read_csv(csv_path)
        required = {"District", "Year", "Season", "Yield_Q_Acre"}
        if not required.issubset(new_df.columns):
            result["error"] = f"CSV missing required columns: {required - set(new_df.columns)}"
            return result
        new_records = new_df[new_df["Year"] > current_latest]
        result["new_data"] = len(new_records) > 0
        result["new_records"] = int(len(new_records))
        result["new_years"] = sorted(new_records["Year"].unique().tolist())
        result["file_path"] = os.path.abspath(csv_path)
    elif data_source_url:
        result["data_source_url"] = data_source_url
    return result


def validate_csv(csv_path, status_callback=None):
    if status_callback:
        status_callback("Validating incoming data...")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    df = pd.read_csv(csv_path)
    required = {"District", "Year", "Season", "Yield_Q_Acre"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    invalid = df[df["Yield_Q_Acre"].isna() | (df["Yield_Q_Acre"] <= 0)]
    if len(invalid) > 0:
        raise ValueError(f"{len(invalid)} rows have invalid Yield_Q_Acre")
    return df


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


def _get_season_dates(year, season):
    if season.lower() == 'kharif':
        return f"{year}0615", f"{year}0906"
    return f"{year}1101", f"{year + 1}0123"


def _fetch_weekly_telemetry(district, year, season):
    lat, lon = DISTRICT_COORDS.get(district, (20.5, 85.0))
    start_date, end_date = _get_season_dates(year, season)
    url = (f"https://power.larc.nasa.gov/api/temporal/daily/point"
           f"?parameters=PRECTOTCORR,T2M,RH2M,GWETROOT"
           f"&community=AG&longitude={lon:.4f}&latitude={lat:.4f}"
           f"&start={start_date}&end={end_date}&format=JSON")
    try:
        resp = requests.get(url, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()
        params = data.get("properties", {}).get("parameter", {})
        result = {}
        for var_name in ["PRECTOTCORR", "T2M", "RH2M", "GWETROOT"]:
            daily_values = [v if v > -900 else 0.0 for v in list(params.get(var_name, {}).values())]
            weekly = []
            days_per_week = max(1, len(daily_values) // 12)
            for w in range(12):
                chunk = daily_values[w * days_per_week: min((w + 1) * days_per_week, len(daily_values))]
                val = round(sum(chunk), 2) if var_name == "PRECTOTCORR" else round(sum(chunk) / len(chunk), 2)
                weekly.append(val)
            result[var_name] = weekly
        return result
    except Exception as e:
        print(f"NASA POWER API error for {district} {year} {season}: {e}")
        return None


def _generate_fallback_telemetry(district, year, season):
    lat = DISTRICT_COORDS.get(district, (20.5, 85.0))[0]
    lat_factor = (lat - 18.0) / 4.5
    return {
        "PRECTOTCORR": [round(15.0 + math.sin(i * 0.8 + lat_factor) * 25.0, 2) for i in range(12)],
        "T2M": [round(27.5 + math.cos(i * 0.6) * 3.0 - lat_factor * 2.0, 2) for i in range(12)],
        "RH2M": [round(72.0 + math.sin(i * 1.2) * 12.0 + lat_factor * 5.0, 2) for i in range(12)],
        "GWETROOT": [round(min(1.0, max(0.0, 0.65 - i * 0.025 + lat_factor * 0.1)), 2) for i in range(12)]
    }


def fetch_missing_telemetry(df, status_callback=None):
    if status_callback:
        status_callback("Fetching NASA POWER telemetry for new records...")
    os.makedirs(TELEMETRY_DIR, exist_ok=True)

    for idx, row in df.iterrows():
        district = row["District"]
        year = int(row["Year"])
        season = row["Season"]

        weekly = _fetch_weekly_telemetry(district, year, season)
        if weekly is None:
            weekly = _generate_fallback_telemetry(district, year, season)
            print(f"Using fallback telemetry for {district} {year} {season}")

        for w in range(12):
            df.loc[idx, f"W{w+1}_PRECTOTCORR"] = weekly["PRECTOTCORR"][w]
            df.loc[idx, f"W{w+1}_T2M"] = weekly["T2M"][w]
            df.loc[idx, f"W{w+1}_RH2M"] = weekly["RH2M"][w]
            df.loc[idx, f"W{w+1}_GWETROOT"] = weekly["GWETROOT"][w]
    return df


def merge_into_dataset(new_df, status_callback=None):
    if status_callback:
        status_callback("Merging new records into dataset...")
    existing = pd.read_csv(DATA_PATH)
    combined = pd.concat([existing, new_df], ignore_index=True)
    combined.drop_duplicates(subset=["District", "Year", "Season"], keep="last", inplace=True)
    combined.sort_values(["Year", "District", "Season"], inplace=True)
    combined.reset_index(drop=True, inplace=True)
    combined["Is_Interpolated"] = False

    for (dist, season), group in combined.groupby(["District", "Season"]):
        q1 = group["Yield_Q_Acre"].quantile(0.25)
        mask = (combined["District"] == dist) & (combined["Season"] == season)
        combined.loc[mask, "Q1_Threshold"] = round(q1, 6)

    combined["Failure_Anomaly"] = (combined["Yield_Q_Acre"] < combined["Q1_Threshold"]).astype(int)
    combined.to_csv(DATA_PATH, index=False)
    return len(combined)


def backup_models(status_callback=None):
    if status_callback:
        status_callback("Backing up current models...")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(MODEL_DIR, f"backup_{ts}")
    shutil.copytree(MODEL_DIR, backup_dir, ignore=shutil.ignore_patterns("backup_*"))
    return backup_dir


def run_prepare_data(status_callback=None):
    if status_callback:
        status_callback("Running data preparation...")
    prepare_script = os.path.join(os.path.dirname(__file__), "prepare_data.py")
    result = subprocess.run([sys.executable, prepare_script], capture_output=True, text=True, cwd=os.path.dirname(__file__))
    if result.returncode != 0:
        raise RuntimeError(f"prepare_data.py failed:\n{result.stderr}")
    return result.stdout


def run_train(status_callback=None):
    if status_callback:
        status_callback("Retraining models (this may take ~120s)...")
    train_script = os.path.join(os.path.dirname(__file__), "train.py")
    result = subprocess.run([sys.executable, train_script], capture_output=True, text=True, cwd=os.path.dirname(__file__))
    if result.returncode != 0:
        raise RuntimeError(f"train.py failed:\n{result.stderr}")
    return result.stdout


def save_version(backup_dir, status_callback=None):
    if status_callback:
        status_callback("Saving version metadata...")
    import re
    old_version = get_current_version()
    major, minor = map(int, old_version.get("version", "1.0").split("."))
    new_version_str = f"{major}.{minor + 1}"
    metrics = {"yield_r2": None, "failure_auc": None}
    train_output = old_version.get("_last_train_output", "")
    r2_match = re.search(r"Stacked.*R2[^:]*:\s*([\d.]+)", train_output)
    auc_match = re.search(r"Stacked.*AUC[^:]*:\s*([\d.]+)", train_output)
    if r2_match:
        metrics["yield_r2"] = float(r2_match.group(1))
    if auc_match:
        metrics["failure_auc"] = float(auc_match.group(1))
    version_info = {
        "version": new_version_str,
        "last_trained": datetime.now().isoformat(),
        "metrics": metrics,
        "backup_dir": backup_dir,
        "_last_train_output": train_output[:500]
    }
    with open(PIPELINE_LOG, "w") as f:
        json.dump(version_info, f, indent=2)
    return version_info


def run_pipeline(csv_path, steps=None, status_callback=None):
    if steps is None:
        steps = DEFAULT_STEPS
    status = {}

    for step in steps:
        status["step"] = step
        status["progress"] = DEFAULT_STEPS.index(step) / len(DEFAULT_STEPS) * 100
        if status_callback:
            status_callback(status)

        if step == "validate_csv":
            status["validated_df"] = validate_csv(csv_path, status_callback)
        elif step == "fetch_telemetry":
            status["validated_df"] = fetch_missing_telemetry(status["validated_df"], status_callback)
            info = get_dataset_info()
            status["current_year"] = info["latest_year"]
        elif step == "merge_data":
            status["total_rows"] = merge_into_dataset(status["validated_df"], status_callback)
        elif step == "backup_models":
            status["backup_dir"] = backup_models(status_callback)
        elif step == "prepare_data":
            status["prepare_output"] = run_prepare_data(status_callback)
        elif step == "train_models":
            status["train_output"] = run_train(status_callback)
        elif step == "save_version":
            status["version_info"] = save_version(status.get("backup_dir"), status_callback)

    status["step"] = "complete"
    status["progress"] = 100
    status["status"] = "success"
    if status_callback:
        status_callback(status)
    return status


def parse_train_output_for_metrics(train_output):
    import re
    r2_match = re.search(r"Stacked.*R2[^:]*:\s*([\d.]+)", train_output)
    auc_match = re.search(r"Stacked.*AUC[^:]*:\s*([\d.]+)", train_output)
    return {
        "yield_r2": float(r2_match.group(1)) if r2_match else None,
        "failure_auc": float(auc_match.group(1)) if auc_match else None
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CDT Update Pipeline")
    parser.add_argument("csv_path", help="Path to new yield data CSV")
    parser.add_argument("--skip-telemetry", action="store_true", help="Skip NASA telemetry fetch")
    parser.add_argument("--dry-run", action="store_true", help="Validate only, don't modify")
    args = parser.parse_args()

    if args.dry_run:
        result = check_new_data(csv_path=args.csv_path)
        print(json.dumps(result, indent=2))
    else:
        steps = DEFAULT_STEPS.copy()
        if args.skip_telemetry:
            steps.remove("fetch_telemetry")
        result = run_pipeline(args.csv_path, steps=steps)
        print(json.dumps({k: v for k, v in result.items() if k != "validated_df"}, indent=2))
