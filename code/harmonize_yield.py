import pandas as pd
import numpy as np
import os

# Define Paths
data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sources", "data")
hist_path = os.path.join(data_dir, "odisha_data.csv")
recent_path = os.path.join(data_dir, "DES-District-Data-For-2024-25.csv")
output_path = os.path.join(data_dir, "harmonized_yield.csv")

# Standard District Names from NASA POWER Ingest configuration
STANDARD_DISTRICTS = [
    "Angul", "Balangir", "Balasore", "Bargarh", "Bhadrak", "Boudh", "Cuttack",
    "Deogarh", "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur", "Jajpur",
    "Jharsuguda", "Kalahandi", "Kandhamal", "Kendrapara", "Keonjhar", "Khurda",
    "Koraput", "Malkangiri", "Mayurbhanj", "Nabarangpur", "Nayagarh", "Nuapada",
    "Puri", "Rayagada", "Sambalpur", "Sonepur", "Sundargarh"
]

# District Spelling Mapper
DISTRICT_MAP = {
    "ANUGUL": "Angul",
    "ANGUL": "Angul",
    "BALANGIR": "Balangir",
    "BALESHWAR": "Balasore",
    "BALASORE": "Balasore",
    "BARGARH": "Bargarh",
    "BHADRAK": "Bhadrak",
    "BOUDH": "Boudh",
    "CUTTACK": "Cuttack",
    "DEOGARH": "Deogarh",
    "DHENKANAL": "Dhenkanal",
    "GAJAPATI": "Gajapati",
    "GANJAM": "Ganjam",
    "JAGATSINGHAPUR": "Jagatsinghpur",
    "JAGATSINGHPUR": "Jagatsinghpur",
    "JAJAPUR": "Jajpur",
    "JAJPUR": "Jajpur",
    "JHARSUGUDA": "Jharsuguda",
    "KALAHANDI": "Kalahandi",
    "KANDHAMAL": "Kandhamal",
    "KENDRAPARA": "Kendrapara",
    "KENDUJHAR": "Keonjhar",
    "KEONJHAR": "Keonjhar",
    "KHORDHA": "Khurda",
    "KHURDA": "Khurda",
    "KORAPUT": "Koraput",
    "MALKANGIRI": "Malkangiri",
    "MAYURBHANJ": "Mayurbhanj",
    "NABARANGPUR": "Nabarangpur",
    "NAYAGARH": "Nayagarh",
    "NUAPADA": "Nuapada",
    "PURI": "Puri",
    "RAYAGADA": "Rayagada",
    "SAMBALPUR": "Sambalpur",
    "SONEPUR": "Sonepur",
    "SUNDARGARH": "Sundargarh"
}

def load_and_clean_historical():
    print("Loading historical data...")
    df = pd.read_csv(hist_path)
    df.columns = df.columns.str.strip()
    
    # Filter for Rice
    df = df[df['Crop'].str.strip() == 'Rice'].copy()
    
    # Map district names
    df['District'] = df['District'].str.strip().str.upper().map(DISTRICT_MAP)
    
    # Clean seasons: Winter/Autumn/Kharif -> Kharif, Summer -> Rabi
    season_map = {
        'Winter': 'Kharif',
        'Autumn': 'Kharif',
        'Kharif': 'Kharif',
        'Summer': 'Rabi'
    }
    df['Season'] = df['Season'].str.strip().map(season_map)
    
    # Group and aggregate (sum area and production, recalculate yield in MT/ha)
    df_agg = df.groupby(['District', 'Crop_Year', 'Season']).agg({
        'Area': 'sum',
        'Production': 'sum'
    }).reset_index()
    
    # Calculate Yield in MT/ha
    df_agg['Yield_MTha'] = df_agg['Production'] / df_agg['Area']
    
    # Rename year column
    df_agg.rename(columns={'Crop_Year': 'Year'}, inplace=True)
    
    return df_agg

def load_and_clean_recent():
    print("Loading recent data...")
    df = pd.read_csv(recent_path)
    df.columns = df.columns.str.strip()
    
    # Filter for Rice
    df = df[df['Crop'].str.strip() == 'Rice'].copy()
    
    # Filter out Season == 'Total'
    df = df[df['Season'].str.strip() != 'Total'].copy()
    
    # Map district names
    df['District'] = df['District'].str.strip().str.upper().map(DISTRICT_MAP)
    
    # Map seasons: Kharif -> Kharif, Summer -> Rabi
    season_map = {
        'Kharif': 'Kharif',
        'Summer': 'Rabi'
    }
    df['Season'] = df['Season'].str.strip().map(season_map)
    
    # Units conversion: Area in Lakh Hectares -> Hectares, Production in Lakh Tonnes -> Tonnes
    df['Area'] = df['Area-2024-25'] * 100000
    df['Production'] = df['Production-2024-25'] * 100000
    
    # Yield in kg/ha -> MT/ha
    df['Yield_MTha'] = df['Yield-2024-25'] / 1000.0
    
    df['Year'] = 2024
    
    return df[['District', 'Year', 'Season', 'Area', 'Production', 'Yield_MTha']]

def main():
    df_hist = load_and_clean_historical()
    df_recent = load_and_clean_recent()
    
    # Combine datasets
    df_combined = pd.concat([df_hist, df_recent], ignore_index=True)
    
    # Filter to 19-year span (2006 to 2024)
    # 2025 removed entirely — all rows were synthetic (interpolated).
    df_combined = df_combined[(df_combined['Year'] >= 2006) & (df_combined['Year'] <= 2024)]
    
    # Generate complete grid of Districts, Years, and Seasons
    years = list(range(2006, 2025))
    seasons = ['Kharif', 'Rabi']
    
    grid = []
    for district in STANDARD_DISTRICTS:
        for year in years:
            for season in seasons:
                grid.append({'District': district, 'Year': year, 'Season': season})
    df_grid = pd.DataFrame(grid)
    
    # Merge combined data onto grid
    df_final = pd.merge(df_grid, df_combined, on=['District', 'Year', 'Season'], how='left')
    
    # Track which rows are interpolated
    df_final['Is_Interpolated'] = df_final['Yield_MTha'].isna()
    
    # Sort for interpolation
    df_final.sort_values(['District', 'Season', 'Year'], inplace=True)
    
    # Interpolate Area and Production per district and season
    df_final['Area'] = df_final.groupby(['District', 'Season'])['Area'].transform(lambda x: x.interpolate(limit_direction='both'))
    df_final['Production'] = df_final.groupby(['District', 'Season'])['Production'].transform(lambda x: x.interpolate(limit_direction='both'))
    
    # Recalculate Yield in MT/ha after interpolation
    df_final['Yield_MTha'] = df_final['Production'] / df_final['Area']
    df_final.loc[df_final['Area'] == 0, 'Yield_MTha'] = 0.0
    
    # Unit Conversion: Yield (MT/ha) -> Yield (Q/Acre)
    # Formula: Yield (Q/Acre) = (Yield (MT/ha) * 10) / 2.471
    df_final['Yield_Q_Acre'] = (df_final['Yield_MTha'] * 10) / 2.471
    
    # Calculate Q1 (25th Percentile) of Yield (Q/Acre) per District and Season
    # Group by District and Season, calculate Q1 of the non-interpolated yields if possible,
    # or of all yields if necessary. We will use all yields to ensure we have a robust threshold.
    df_q1 = df_final.groupby(['District', 'Season'])['Yield_Q_Acre'].quantile(0.25).reset_index()
    df_q1.rename(columns={'Yield_Q_Acre': 'Q1_Threshold'}, inplace=True)
    
    # Merge Q1 Thresholds back
    df_final = pd.merge(df_final, df_q1, on=['District', 'Season'], how='left')
    
    # Label Failure Anomaly
    df_final['Failure_Anomaly'] = (df_final['Yield_Q_Acre'] < df_final['Q1_Threshold']).astype(int)
    
    # Save harmonized data
    df_final.to_csv(output_path, index=False)
    print(f"Success! Harmonized dataset saved to {output_path}")
    print(df_final.head())
    print("\nSummary of failure anomalies:")
    print(df_final['Failure_Anomaly'].value_counts())

if __name__ == '__main__':
    main()
