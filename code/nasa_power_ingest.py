import requests
import json
import pandas as pd
import time
from datetime import datetime, timedelta

# --- CONFIGURATION ---
# District Centroid Point Mapping (Odisha)
DISTRICTS = {
    "Angul": [20.8444, 85.1511],
    "Balangir": [20.7121, 83.4893],
    "Balasore": [21.4942, 86.9317],
    "Bargarh": [21.3331, 83.6149],
    "Bhadrak": [21.0574, 86.5051],
    "Boudh": [20.8403, 84.3276],
    "Cuttack": [20.4625, 85.8830],
    "Deogarh": [21.5323, 84.7317],
    "Dhenkanal": [20.6621, 85.5976],
    "Gajapati": [18.8105, 84.1485],
    "Ganjam": [19.3150, 84.7941],
    "Jagatsinghpur": [20.2721, 86.1717],
    "Jajpur": [20.8521, 86.3317],
    "Jharsuguda": [21.8574, 84.0276],
    "Kalahandi": [19.7214, 83.0276],
    "Kandhamal": [20.2317, 84.2185],
    "Kendrapara": [20.5021, 86.4117],
    "Keonjhar": [21.6276, 85.5817],
    "Khurda": [20.1821, 85.6217],
    "Koraput": [18.8125, 82.7117],
    "Malkangiri": [18.3521, 81.8817],
    "Mayurbhanj": [21.9321, 86.7517],
    "Nabarangpur": [19.2321, 82.3517],
    "Nayagarh": [20.1321, 85.1017],
    "Nuapada": [20.3321, 82.5217],
    "Puri": [19.8125, 85.8317],
    "Rayagada": [19.1721, 83.4217],
    "Sambalpur": [21.4625, 83.9817],
    "Sonepur": [21.0321, 83.9117],
    "Sundargarh": [22.1221, 84.0317]
}

# The 4 Primary Climate Variables from CPDT Spec
# PRECTOTCORR: Precip, T2M: Temp, RH2M: Humidity, GWETROOT: Soil Wetness
PARAMETERS = "PRECTOTCORR,T2M,RH2M,GWETROOT"

BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

def fetch_nasa_data(lat, lon, start_year, end_year):
    """
    Fetches daily data for a specific point from NASA POWER.
    """
    start_date = f"{start_year}0101"
    end_date = f"{end_year}1231"
    
    params = {
        "parameters": PARAMETERS,
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": start_date,
        "end": end_date,
        "format": "JSON"
    }
    
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def process_to_dataframe(data, district_name):
    """
    Processes daily JSON data into a flattened pandas DataFrame.
    """
    if not data:
        return None
    
    records = data['properties']['parameter']
    df = pd.DataFrame(records)
    df['district'] = district_name
    df['date'] = df.index
    return df

if __name__ == "__main__":
    print("Initializing NASA POWER Ingestion Node for Odisha Pilot Engine...")
    
    # Example: Fetching 2023 data for Ganjam as a test
    test_district = "Ganjam"
    coords = DISTRICTS[test_district]
    
    print(f"Requesting Telemetry: {test_district} (Lat: {coords[0]}, Lon: {coords[1]})")
    raw_data = fetch_nasa_data(coords[0], coords[1], 2023, 2023)
    
    if raw_data:
        processed_df = process_to_dataframe(raw_data, test_district)
        # Ensure output directory exists
        output_path = f"sources/data/{test_district.lower()}_2023_telemetry.csv"
        processed_df.to_csv(output_path, index=False)
        print(f"Success! Data saved to {output_path}")
    else:
        print("Failed to fetch data. Check connection or API status.")
