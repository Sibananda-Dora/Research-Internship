import os
import pandas as pd
import numpy as np

# Define Paths
data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sources", "data")
yield_path = os.path.join(data_dir, "harmonized_yield.csv")
telemetry_dir = os.path.join(data_dir, "telemetry")
output_path = os.path.join(data_dir, "final_dataset.csv")

def process_season_telemetry(df_daily, year, season):
    """
    Extracts the 84-day vegetative window for the given crop year and season,
    and aggregates daily values into 12 weekly steps.
    """
    # Define start and end date of the 12-week (84-day) window
    if season == 'Kharif':
        # Kharif vegetative cycle: June 15 to Sept 6 (84 days)
        start_date_str = f"{year}-06-15"
    elif season == 'Rabi':
        # Rabi vegetative cycle: Nov 1 to Jan 23 of the following year (84 days)
        start_date_str = f"{year}-11-01"
    else:
        return None
        
    start_date = pd.to_datetime(start_date_str)
    end_date = start_date + pd.Timedelta(days=83)
    
    # Filter daily data
    df_window = df_daily[(df_daily['Parsed_Date'] >= start_date) & (df_daily['Parsed_Date'] <= end_date)].copy()
    
    if len(df_window) != 84:
        # If we are slightly short or have missing dates, try to re-index or print warning
        # (For example, leap years, or missing API entries)
        if len(df_window) == 0:
            return None
        # Re-index to ensure exactly 84 days, forward filling any small gaps
        idx = pd.date_range(start=start_date, end=end_date)
        df_window.set_index('Parsed_Date', inplace=True)
        df_window = df_window.reindex(idx)
        df_window['PRECTOTCORR'] = df_window['PRECTOTCORR'].ffill().bfill()
        df_window['T2M'] = df_window['T2M'].ffill().bfill()
        df_window['RH2M'] = df_window['RH2M'].ffill().bfill()
        df_window['GWETROOT'] = df_window['GWETROOT'].ffill().bfill()
        df_window.reset_index(names='Parsed_Date', inplace=True)
        
    # Group into 12 weeks (7 days each)
    df_window['Week'] = np.repeat(np.arange(1, 13), 7)
    
    # Aggregate features: sum for precipitation, mean for others
    weekly_agg = df_window.groupby('Week').agg({
        'PRECTOTCORR': 'sum',
        'T2M': 'mean',
        'RH2M': 'mean',
        'GWETROOT': 'mean'
    }).reset_index()
    
    # Flatten weekly aggregates into a single feature dictionary
    features = {}
    for _, row in weekly_agg.iterrows():
        w = int(row['Week'])
        features[f"W{w}_PRECTOTCORR"] = row['PRECTOTCORR']
        features[f"W{w}_T2M"] = row['T2M']
        features[f"W{w}_RH2M"] = row['RH2M']
        features[f"W{w}_GWETROOT"] = row['GWETROOT']
        
    return features

def main():
    print("Loading yield dataset...")
    df_yield = pd.read_csv(yield_path)
    
    # Load all cached daily files into a dictionary of DataFrames to avoid repeated disk reads
    print("Pre-loading daily weather telemetry files...")
    daily_telemetry = {}
    for filename in os.listdir(telemetry_dir):
        if filename.endswith("_daily.csv"):
            district_name = filename.split("_")[0].capitalize()
            filepath = os.path.join(telemetry_dir, filename)
            df_daily = pd.read_csv(filepath)
            
            # Format Date column: NASA dates are stored as YYYYMMDD in index/column.
            # Convert string key YYYYMMDD to datetime.
            df_daily['Parsed_Date'] = pd.to_datetime(df_daily['Date'].astype(str), format='%Y%m%d')
            daily_telemetry[district_name] = df_daily

    print("Extracting features and merging telemetry with yield data...")
    merged_records = []
    
    for idx, row in df_yield.iterrows():
        district = row['District']
        year = int(row['Year'])
        season = row['Season']
        
        # Look up preloaded daily telemetry
        df_daily = daily_telemetry.get(district)
        if df_daily is None:
            # Match case insensitive just in case
            df_daily = daily_telemetry.get(district.capitalize())
            
        features = None
        if df_daily is not None:
            features = process_season_telemetry(df_daily, year, season)
            
        # Create combined row record
        record = row.to_dict()
        if features:
            record.update(features)
        else:
            # Fill with NaN if telemetry is missing
            for w in range(1, 13):
                record[f"W{w}_PRECTOTCORR"] = np.nan
                record[f"W{w}_T2M"] = np.nan
                record[f"W{w}_RH2M"] = np.nan
                record[f"W{w}_GWETROOT"] = np.nan
                
        merged_records.append(record)
        
    df_final = pd.DataFrame(merged_records)

    # Note: interpolated rows kept for now — apply_real_data_split.py replaces
    # them with real values where available. Final cleanup happens after that.

    df_final.to_csv(output_path, index=False)
    print(f"Success! Final merged dataset saved to {output_path}")
    print(df_final.head())
    print("Dataset shape:", df_final.shape)

if __name__ == '__main__':
    main()
