"""Prepares pre-training data: 84-step daily weather sequences from telemetry CSVs."""

import os, sys, numpy as np, pandas as pd
from glob import glob

TELEMETRY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "sources", "data", "telemetry")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "pretrain_data")

SEASONS = {
    "Kharif": {"start_month": 6, "start_day": 15, "length": 84},
    "Rabi": {"start_month": 11, "start_day": 1, "length": 84},
}

DISTRICTS_30 = [
    "Angul","Balangir","Balasore","Bargarh","Bhadrak","Boudh","Cuttack","Deogarh",
    "Dhenkanal","Gajapati","Ganjam","Jagatsinghpur","Jajpur","Jharsuguda","Kalahandi",
    "Kandhamal","Kendrapara","Keonjhar","Khurda","Koraput","Malkangiri","Mayurbhanj",
    "Nabarangpur","Nayagarh","Nuapada","Puri","Rayagada","Sambalpur","Sonepur","Sundargarh"
]

def extract_pretrain_sequences():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_sequences = []
    season_labels = []
    district_labels = []
    year_labels = []

    for district in DISTRICTS_30:
        fpath = os.path.join(TELEMETRY_DIR, f"{district.lower()}_daily.csv")
        if not os.path.exists(fpath):
            print(f"  MISSING: {fpath}")
            continue

        df = pd.read_csv(fpath)
        df["Date"] = df["Date"].astype(str)
        df["Date_dt"] = pd.to_datetime(df["Date"], format="%Y%m%d")
        df = df.sort_values("Date_dt").reset_index(drop=True)

        print(f"[{district}] {len(df)} daily records from {df['Date_dt'].min().date()} to {df['Date_dt'].max().date()}")

        years = sorted(df["Date_dt"].dt.year.unique())

        for year in years:
            for season, spec in SEASONS.items():
                if season == "Kharif":
                    start_dt = pd.Timestamp(year=year, month=spec["start_month"], day=spec["start_day"])
                else:
                    start_dt = pd.Timestamp(year=year, month=spec["start_month"], day=spec["start_day"])
                    # Check if we have enough data - need data past the winter solstice
                    if year + 1 not in years:
                        continue

                mask = (df["Date_dt"] >= start_dt) & (df["Date_dt"] < start_dt + pd.Timedelta(days=spec["length"]))
                window = df[mask]

                if len(window) < 84:
                    continue  # skip incomplete windows

                seq = window[["PRECTOTCORR", "T2M", "RH2M", "GWETROOT"]].values[:84].astype(np.float32)

                all_sequences.append(seq)
                season_labels.append(0 if season == "Kharif" else 1)
                district_labels.append(DISTRICTS_30.index(district))
                year_labels.append(year)

    if len(all_sequences) == 0:
        print("No sequences extracted. Have you run fetch_nasa_telemetry.py (updated to fetch 1981-2026) first?")
        return

    arr = np.stack(all_sequences, axis=0)
    np.save(os.path.join(OUTPUT_DIR, "weather_sequences.npy"), arr)
    np.save(os.path.join(OUTPUT_DIR, "season_labels.npy"), np.array(season_labels, dtype=np.int32))
    np.save(os.path.join(OUTPUT_DIR, "district_labels.npy"), np.array(district_labels, dtype=np.int32))
    np.save(os.path.join(OUTPUT_DIR, "year_labels.npy"), np.array(year_labels, dtype=np.int32))

    print(f"\nSaved {len(arr)} pretrain sequences of shape {arr.shape}")
    print(f"  Year range: {min(year_labels)} to {max(year_labels)}")
    print(f"  Districts: {len(set(district_labels))}")
    print(f"  Seasons: {len(set(season_labels))}")

if __name__ == "__main__":
    extract_pretrain_sequences()
