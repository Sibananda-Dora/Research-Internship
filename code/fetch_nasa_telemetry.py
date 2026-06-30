import os
import time
import requests
import pandas as pd

# Coordinates for the 30 districts of Odisha (from nasa_power_ingest.py)
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

PARAMETERS = "PRECTOTCORR,T2M,RH2M,GWETROOT"
BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sources", "data", "telemetry")

def fetch_and_save_all():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    start_date = "19810101"
    end_date = "20261231"
    
    print("Starting NASA POWER Data Ingestion for 30 Districts (1981-2026)...")
    
    for district, coords in DISTRICTS.items():
        output_file = os.path.join(OUTPUT_DIR, f"{district.lower()}_daily.csv")
        
        print(f"[{district}] Fetching telemetry (Lat: {coords[0]}, Lon: {coords[1]})...")
        
        params = {
            "parameters": PARAMETERS,
            "community": "AG",
            "longitude": coords[1],
            "latitude": coords[0],
            "start": start_date,
            "end": end_date,
            "format": "JSON"
        }
        
        retries = 3
        success = False
        while retries > 0 and not success:
            try:
                response = requests.get(BASE_URL, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    # Parse parameters
                    records = data['properties']['parameter']
                    df = pd.DataFrame(records)
                    df['Date'] = df.index
                    df['District'] = district
                    
                    # Save to CSV
                    df.to_csv(output_file, index=False)
                    print(f"[{district}] Success! Saved to {output_file}")
                    success = True
                else:
                    print(f"[{district}] Error: HTTP {response.status_code}. Retrying...")
                    retries -= 1
                    time.sleep(2)
            except Exception as e:
                print(f"[{district}] Exception: {e}. Retrying...")
                retries -= 1
                time.sleep(2)
                
        if not success:
            print(f"[{district}] Failed to fetch data after 3 retries.")
        
        # Respectful delay between requests
        time.sleep(1)

if __name__ == '__main__':
    fetch_and_save_all()
