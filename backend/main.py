import os
import math
import numpy as np
import pandas as pd
import httpx
import sys
from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import the orchestrator (routes queries to the right model)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'code', 'phase-2-training'))
from orchestrator import run, QueryType
from llm_client import parse_intent, format_advisory

app = FastAPI(
    title="Cognitive Digital Twin (CDT) API",
    description="Odisha Crop Yield and Failure Prediction Engine API — routed via custom Python DAG orchestrator",
    version="2.5.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "sources", "data", "final_dataset.csv"
)

try:
    if os.path.exists(DATA_PATH):
        df_dataset = pd.read_csv(DATA_PATH)
        print(f"Dataset loaded successfully with {len(df_dataset)} rows.")
    else:
        df_dataset = pd.DataFrame()
except Exception as e:
    df_dataset = pd.DataFrame()
    print(f"Error loading dataset: {e}")


class SimulationRequest(BaseModel):
    district: str
    season: str
    year: int
    precip_modifiers: List[float]
    temp_modifiers: List[float]
    wetness_modifiers: List[float]
    humidity_modifiers: List[float]

class PredictionResponse(BaseModel):
    district: str
    season: str
    year: int
    query_type: str
    predicted_yield: Optional[float] = None
    yield_source: Optional[str] = None
    failure_probability: Optional[float] = None
    failure_source: Optional[str] = None
    failure_anomaly: Optional[int] = None
    attention_weights: Optional[List[float]] = None
    active_triggers: List[str] = []
    monte_carlo_distribution: Optional[List[float]] = None
    monte_carlo_std: Optional[float] = None
    confidence_interval: Optional[Dict[str, float]] = None
    is_mocked: bool = False

class AskRequest(BaseModel):
    query: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


def telemetry_to_flat48(telemetry: Dict[str, List[float]]) -> np.ndarray:
    arr = np.zeros(48, dtype=np.float32)
    for vi, var in enumerate(['PRECTOTCORR', 'T2M', 'RH2M', 'GWETROOT']):
        for w in range(12):
            arr[vi + 4 * w] = telemetry[var][w]
    return arr


def run_orchestrator(district, season, year, telemetry, query_type_str='full_diagnosis'):
    w48 = telemetry_to_flat48(telemetry)
    qt = QueryType(query_type_str) if query_type_str in [e.value for e in QueryType] else QueryType.FULL_DIAGNOSIS
    return run(district, season, year, w48, query_type=qt)


# ===================================================================
# INFO / STATUS
# ===================================================================

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Cognitive Digital Twin (CDT) API v2.5",
        "dataset_loaded": not df_dataset.empty,
        "total_records": len(df_dataset) if not df_dataset.empty else 0,
        "orchestrator": "Custom Python DAG with 3 model nodes (LSTM, XGBoost, stacking meta-learner)",
        "query_types": [e.value for e in QueryType]
    }


# ===================================================================
# HISTORICAL DATA ENDPOINTS
# ===================================================================

@app.get("/api/districts")
def get_districts():
    if df_dataset.empty:
        return {
            "districts": [
                "Angul", "Balasore", "Bargarh", "Bhadrak", "Bolangir", "Boudh",
                "Cuttack", "Deogarh", "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur",
                "Jajpur", "Jharsuguda", "Kalahandi", "Kandhamal", "Kendrapara", "Keonjhar",
                "Khurda", "Koraput", "Malkangiri", "Mayurbhanj", "Nabarangpur", "Nayagarh",
                "Nuapada", "Puri", "Rayagada", "Sambalpur", "Sonepur", "Sundargarh"
            ]
        }
    return {"districts": sorted(df_dataset["District"].unique().tolist())}


@app.get("/api/history/{district}/{season}")
def get_historical_yields(district: str, season: str):
    if df_dataset.empty:
        raise HTTPException(status_code=404, detail="Dataset not loaded")
    filtered = df_dataset[
        (df_dataset["District"].str.lower() == district.lower()) &
        (df_dataset["Season"].str.lower() == season.lower())
    ]
    if filtered.empty:
        return {"records": []}
    records = filtered.sort_values("Year").to_dict(orient="records")
    clean_records = [
        {
            "year": r["Year"],
            "area": r["Area"],
            "production": r["Production"],
            "yield_q_acre": r["Yield_Q_Acre"],
            "failure_anomaly": r["Failure_Anomaly"]
        }
        for r in records
    ]
    return {"records": clean_records}


@app.get("/api/telemetry/{district}/{year}/{season}")
def get_telemetry(district: str, year: int, season: str):
    if df_dataset.empty:
        raise HTTPException(status_code=404, detail="Dataset not loaded")
    filtered = df_dataset[
        (df_dataset["District"].str.lower() == district.lower()) &
        (df_dataset["Year"] == year) &
        (df_dataset["Season"].str.lower() == season.lower())
    ]
    if filtered.empty:
        raise HTTPException(status_code=404, detail="Record not found")
    row = filtered.iloc[0]
    weeks = {}
    for var in ["PRECTOTCORR", "T2M", "RH2M", "GWETROOT"]:
        weeks[var] = [float(row[f"W{w}_{var}"]) for w in range(1, 13)]
    return {
        "district": row["District"],
        "year": int(row["Year"]),
        "season": row["Season"],
        "yield_q_acre": float(row["Yield_Q_Acre"]),
        "failure_anomaly": int(row["Failure_Anomaly"]),
        "telemetry": weeks
    }


# ===================================================================
# PREDICTION ENDPOINTS — routed through the orchestrator
# ===================================================================

@app.get("/api/predict/{district}/{year}/{season}", response_model=PredictionResponse)
def get_prediction(
    district: str,
    year: int,
    season: str,
    query_type: str = Query('full_diagnosis',
                            description="Model routing: yield_forecast | failure_risk | temporal_analysis | what_if | full_diagnosis")
):
    is_mocked = False
    try:
        data = get_telemetry(district, year, season)
        telemetry = data["telemetry"]
    except HTTPException:
        is_mocked = True
        telemetry = {
            "PRECTOTCORR": [10.0 + (i * 2) % 30 for i in range(12)],
            "T2M": [28.0 + math.sin(i) * 2 for i in range(12)],
            "RH2M": [75.0 + math.cos(i) * 10 for i in range(12)],
            "GWETROOT": [0.6 - i * 0.02 for i in range(12)]
        }

    result = run_orchestrator(district, season, year, telemetry, query_type)
    result["is_mocked"] = is_mocked
    return PredictionResponse(**result)


@app.post("/api/simulate", response_model=PredictionResponse)
def simulate_scenario(request: SimulationRequest, query_type: str = Query('what_if',
                              description="Model routing for simulation scenarios")):
    is_mocked = False
    try:
        base_data = get_telemetry(request.district, request.year, request.season)
        base_telemetry = base_data["telemetry"]
    except HTTPException:
        is_mocked = True
        base_telemetry = {
            "PRECTOTCORR": [10.0 + (i * 2) % 30 for i in range(12)],
            "T2M": [28.0 + math.sin(i) * 2 for i in range(12)],
            "RH2M": [75.0 + math.cos(i) * 10 for i in range(12)],
            "GWETROOT": [0.6 - i * 0.02 for i in range(12)]
        }

    sim_telemetry = {
        "PRECTOTCORR": [max(0.0, base_telemetry["PRECTOTCORR"][i] * request.precip_modifiers[i]) for i in range(12)],
        "T2M": [max(-10.0, base_telemetry["T2M"][i] + request.temp_modifiers[i]) for i in range(12)],
        "RH2M": [min(100.0, max(0.0, base_telemetry["RH2M"][i] + request.humidity_modifiers[i])) for i in range(12)],
        "GWETROOT": [min(1.0, max(0.0, base_telemetry["GWETROOT"][i] + request.wetness_modifiers[i])) for i in range(12)]
    }

    result = run_orchestrator(request.district, request.season, request.year, sim_telemetry, query_type)
    result["is_mocked"] = is_mocked
    return PredictionResponse(**result)


# ===================================================================
# LLM-POWERED ASK ENDPOINT
# ===================================================================

@app.post("/api/ask")
def ask_llm(request: AskRequest):
    """
    Natural language query endpoint.
    1. Optionally resolve lat/lon to nearest district
    2. Parse intent via Groq (district, season, year, query_type)
    3. Fill gaps from resolved coordinates
    4. Run orchestrator
    5. Format advisory via Groq
    """
    district = None
    season = None
    year = None

    # Resolve lat/lon to nearest district if provided
    if request.latitude is not None and request.longitude is not None:
        district = find_nearest_district(request.latitude, request.longitude)

    # Parse intent via Groq
    parsed = parse_intent(request.query)
    district = parsed.get("district") or district
    season = parsed.get("season") or season
    year = parsed.get("year") or year
    query_type = parsed.get("query_type", "full_diagnosis")

    # Defaults if still missing
    if not district:
        return {"advisory": "Please specify a district name.", "query_type": query_type, "district": None}
    if not season:
        season = "Kharif"
    if not year:
        year = 2024

    # Get telemetry and run orchestrator
    is_mocked = False
    try:
        data = get_telemetry(district, year, season)
        telemetry = data["telemetry"]
    except HTTPException:
        is_mocked = True
        telemetry = {
            "PRECTOTCORR": [10.0 + (i * 2) % 30 for i in range(12)],
            "T2M": [28.0 + math.sin(i) * 2 for i in range(12)],
            "RH2M": [75.0 + math.cos(i) * 10 for i in range(12)],
            "GWETROOT": [0.6 - i * 0.02 for i in range(12)]
        }

    result = run_orchestrator(district, season, year, telemetry, query_type)
    result["is_mocked"] = is_mocked
    advisory = format_advisory(result)

    return {
        "advisory": advisory,
        "query_type": query_type,
        "district": district,
        "season": season,
        "year": year,
        "data": result
    }


# ===================================================================
# COORDINATE-BASED ENDPOINTS
# ===================================================================

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

class CoordinateRequest(BaseModel):
    latitude: float
    longitude: float
    year: int
    season: str

class CoordinateTelemetryResponse(BaseModel):
    latitude: float
    longitude: float
    year: int
    season: str
    nearest_district: str
    telemetry: Dict[str, List[float]]
    source: str
    is_mocked: bool = False

class CoordinateSimulationRequest(BaseModel):
    latitude: float
    longitude: float
    year: int
    season: str
    precip_modifiers: List[float]
    temp_modifiers: List[float]
    wetness_modifiers: List[float]
    humidity_modifiers: List[float]

class CoordinatePredictRequest(BaseModel):
    latitude: float
    longitude: float
    year: int
    season: str


def find_nearest_district(lat: float, lon: float) -> str:
    min_dist = float('inf')
    nearest = "Ganjam"
    for name, (dlat, dlon) in DISTRICT_COORDS.items():
        dist = math.sqrt((lat - dlat) ** 2 + (lon - dlon) ** 2)
        if dist < min_dist:
            min_dist = dist
            nearest = name
    return nearest


def get_season_dates(year: int, season: str):
    if season.lower() == 'kharif':
        return f"{year}0615", f"{year}0906"
    else:
        return f"{year}1101", f"{year + 1}0123"


async def fetch_nasa_power_telemetry(lat: float, lon: float, year: int, season: str):
    start_date, end_date = get_season_dates(year, season)
    url = (
        f"https://power.larc.nasa.gov/api/temporal/daily/point"
        f"?parameters=PRECTOTCORR,T2M,RH2M,GWETROOT"
        f"&community=AG"
        f"&longitude={lon:.4f}"
        f"&latitude={lat:.4f}"
        f"&start={start_date}"
        f"&end={end_date}"
        f"&format=JSON"
    )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
        params = data.get("properties", {}).get("parameter", {})
        result = {}
        for var_name in ["PRECTOTCORR", "T2M", "RH2M", "GWETROOT"]:
            daily_values = [v if v > -900 else 0.0 for v in list(params.get(var_name, {}).values())]
            weekly = []
            days_per_week = max(1, len(daily_values) // 12)
            for w in range(12):
                chunk = daily_values[w * days_per_week: min((w + 1) * days_per_week, len(daily_values))]
                if chunk:
                    weekly.append(round(sum(chunk), 2) if var_name == "PRECTOTCORR" else round(sum(chunk) / len(chunk), 2))
                else:
                    weekly.append(0.0)
            result[var_name] = weekly
        return result
    except Exception as e:
        print(f"NASA POWER API error: {e}")
        return None


@app.post("/api/telemetry/coordinate", response_model=CoordinateTelemetryResponse)
async def get_coordinate_telemetry(request: CoordinateRequest):
    nearest = find_nearest_district(request.latitude, request.longitude)
    nasa_data = await fetch_nasa_power_telemetry(request.latitude, request.longitude, request.year, request.season)
    if nasa_data:
        return CoordinateTelemetryResponse(
            latitude=request.latitude, longitude=request.longitude,
            year=request.year, season=request.season,
            nearest_district=nearest, telemetry=nasa_data, source="nasa_power"
        )
    try:
        district_data = get_telemetry(nearest, request.year, request.season)
        return CoordinateTelemetryResponse(
            latitude=request.latitude, longitude=request.longitude,
            year=request.year, season=request.season,
            nearest_district=nearest, telemetry=district_data["telemetry"], source="interpolated"
        )
    except HTTPException:
        lat_factor = (request.latitude - 18.0) / 4.5
        telemetry = {
            "PRECTOTCORR": [round(15.0 + math.sin(i * 0.8 + lat_factor) * 25.0 + (40 if i == 5 else 0), 2) for i in range(12)],
            "T2M": [round(27.5 + math.cos(i * 0.6) * 3.0 - lat_factor * 2.0, 2) for i in range(12)],
            "RH2M": [round(72.0 + math.sin(i * 1.2) * 12.0 + lat_factor * 5.0, 2) for i in range(12)],
            "GWETROOT": [round(min(1.0, max(0.0, 0.65 - i * 0.025 + lat_factor * 0.1)), 2) for i in range(12)]
        }
        return CoordinateTelemetryResponse(
            latitude=request.latitude, longitude=request.longitude,
            year=request.year, season=request.season,
            nearest_district=nearest, telemetry=telemetry, source="interpolated", is_mocked=True
        )


class CoordinatePredictResponse(PredictionResponse):
    latitude: float
    longitude: float
    nearest_district: str

@app.post("/api/predict/coordinate", response_model=CoordinatePredictResponse)
async def predict_coordinate(request: CoordinatePredictRequest,
                             query_type: str = Query('full_diagnosis', description="Model routing")):
    nearest = find_nearest_district(request.latitude, request.longitude)
    is_mocked = False
    try:
        data = get_telemetry(nearest, request.year, request.season)
        telemetry = data["telemetry"]
    except HTTPException:
        is_mocked = True
        telemetry = {
            "PRECTOTCORR": [10.0 + (i * 2) % 30 for i in range(12)],
            "T2M": [28.0 + math.sin(i) * 2 for i in range(12)],
            "RH2M": [75.0 + math.cos(i) * 10 for i in range(12)],
            "GWETROOT": [0.6 - i * 0.02 for i in range(12)]
        }
    result = run_orchestrator(nearest, request.season, request.year, telemetry, query_type)
    result["is_mocked"] = is_mocked
    return CoordinatePredictResponse(latitude=request.latitude, longitude=request.longitude,
                                     nearest_district=nearest, **result)


@app.post("/api/simulate/coordinate")
async def simulate_coordinate(request: CoordinateSimulationRequest,
                              query_type: str = Query('what_if', description="Model routing for coordinate simulations")):
    base_req = CoordinateRequest(
        latitude=request.latitude, longitude=request.longitude,
        year=request.year, season=request.season
    )
    base_response = await get_coordinate_telemetry(base_req)
    base_telemetry = base_response.telemetry
    nearest = base_response.nearest_district

    sim_telemetry = {
        "PRECTOTCORR": [max(0.0, base_telemetry["PRECTOTCORR"][i] * request.precip_modifiers[i]) for i in range(12)],
        "T2M": [max(-10.0, base_telemetry["T2M"][i] + request.temp_modifiers[i]) for i in range(12)],
        "RH2M": [min(100.0, max(0.0, base_telemetry["RH2M"][i] + request.humidity_modifiers[i])) for i in range(12)],
        "GWETROOT": [min(1.0, max(0.0, base_telemetry["GWETROOT"][i] + request.wetness_modifiers[i])) for i in range(12)]
    }

    result = run_orchestrator(nearest, request.season, request.year, sim_telemetry, query_type)
    result["is_mocked"] = base_response.is_mocked
    return {
        **result,
        "latitude": request.latitude,
        "longitude": request.longitude,
        "nearest_district": nearest,
        "source": base_response.source,
        "telemetry": sim_telemetry
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
