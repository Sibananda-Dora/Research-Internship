import os, math, threading
import numpy as np
import pandas as pd
import httpx
import sys
import time
import json
from typing import List, Optional, Dict, Tuple
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

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

    @field_validator('precip_modifiers', 'temp_modifiers', 'wetness_modifiers', 'humidity_modifiers')
    @classmethod
    def check_modifier_length(cls, v):
        if len(v) != 12:
            raise ValueError(f'Each modifier list must have exactly 12 entries, got {len(v)}')
        return v

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
    trace: Optional[Dict] = None
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
# MOCK TELEMETRY HELPER (used as fallback by multiple endpoints)
# ===================================================================

def _mock_telemetry():
    return {
        "PRECTOTCORR": [10.0 + (i * 2) % 30 for i in range(12)],
        "T2M": [28.0 + math.sin(i) * 2 for i in range(12)],
        "RH2M": [75.0 + math.cos(i) * 10 for i in range(12)],
        "GWETROOT": [0.6 - i * 0.02 for i in range(12)]
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
        telemetry = _mock_telemetry()

    try:
        result = run_orchestrator(district, season, year, telemetry, query_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
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
        base_telemetry = _mock_telemetry()

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
        district = find_district_by_boundary(request.latitude, request.longitude)

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
        telemetry = _mock_telemetry()

    result = run_orchestrator(district, season, year, telemetry, query_type)
    result["is_mocked"] = is_mocked
    advisory = format_advisory(
        result,
        attention_weights=result.get("attention_weights"),
        telemetry=telemetry,
    )

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


# ---------------------------------------------------------------------------
# District boundary resolver (point-in-polygon)
# ---------------------------------------------------------------------------
# Load the Odisha district boundary GeoJSON once at startup so lat/lng can be
# resolved to the exact district it falls inside (instead of nearest centroid).
# A point outside every district boundary resolves to "Unknown".
def _load_district_geojson():
    path = os.path.join(os.path.dirname(__file__), "odisha_districts.geojson")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[warn] could not load odisha_districts.geojson: {e}")
        return {"features": []}


DISTRICT_GEOJSON = _load_district_geojson()


def _point_in_ring(lat: float, lon: float, ring: List[List[float]]) -> bool:
    """Ray-casting algorithm: True if (lat, lon) is inside the ring.

    GeoJSON ring coords are [lon, lat]; the ray extends to the right (+lon).
    """
    inside = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        if ((y1 > lat) != (y2 > lat)) and (lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1):
            inside = not inside
    return inside


def _iter_exterior_rings(geom: dict):
    """Yield exterior rings ([lon, lat] point lists) for a Polygon or MultiPolygon."""
    gtype = geom.get("type")
    if gtype == "MultiPolygon":
        for polygon in geom.get("coordinates", []):
            if polygon:
                yield polygon[0]
    elif gtype == "Polygon":
        for polygon in [geom.get("coordinates", [])]:
            if polygon:
                yield polygon[0]


def find_district_by_boundary(lat: float, lon: float) -> str:
    """Return the district a lat/lng falls inside, or 'Unknown' if outside Odisha.

    Handles both Polygon (28 districts) and MultiPolygon (2 districts) geometry.
    """
    for feat in DISTRICT_GEOJSON.get("features", []):
        name = feat.get("properties", {}).get("name")
        geom = feat.get("geometry") or {}
        for ring in _iter_exterior_rings(geom):
            if _point_in_ring(lat, lon, ring):
                return name
    return "Unknown"


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

    @field_validator('precip_modifiers', 'temp_modifiers', 'wetness_modifiers', 'humidity_modifiers')
    @classmethod
    def check_modifier_length(cls, v):
        if len(v) != 12:
            raise ValueError(f'Each modifier list must have exactly 12 entries, got {len(v)}')
        return v

class CoordinatePredictRequest(BaseModel):
    latitude: float
    longitude: float
    year: int
    season: str

class RealtimeCoordinateRequest(BaseModel):
    latitude: float
    longitude: float
    district: Optional[str] = None
    year: int = 2024
    season: str = "Kharif"


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
    nearest = find_district_by_boundary(request.latitude, request.longitude)
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
    nearest = find_district_by_boundary(request.latitude, request.longitude)
    is_mocked = False
    try:
        data = get_telemetry(nearest, request.year, request.season)
        telemetry = data["telemetry"]
    except HTTPException:
        is_mocked = True
        telemetry = _mock_telemetry()
    try:
        result = run_orchestrator(nearest, request.season, request.year, telemetry, query_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
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


# ===================================================================
# REAL-TIME WEATHER MONITOR (Open-Meteo + Temporal Interpolation)
# ===================================================================

# Cache for interpolation: {lat_lng_key: {"t0": timestamp, "v0": {...}, "t1": timestamp, "v1": {...}}}
realtime_cache: Dict[str, dict] = {}

def _get_climatology(district: str, season: str):
    """20-year average weekly telemetry for a district/season."""
    if df_dataset.empty:
        return None
    sub = df_dataset[
        (df_dataset["District"].str.lower() == district.lower()) &
        (df_dataset["Season"].str.lower() == season.lower())
    ]
    if sub.empty:
        return None
    result = {}
    for var in ["PRECTOTCORR", "T2M", "RH2M", "GWETROOT"]:
        vals = []
        for w in range(1, 13):
            col = f"W{w}_{var}"
            vals.append(round(float(sub[col].mean()), 2) if col in sub.columns else 0.0)
        result[var] = vals
    return result

def _interpolate_snapshot(old: dict, new: dict, t0: float, t1: float, now: float) -> dict:
    frac = (now - t0) / (t1 - t0) if t1 > t0 else 1.0
    frac = max(0.0, min(1.0, frac))
    return {
        "T2M": round(old["T2M"] + (new["T2M"] - old["T2M"]) * frac, 2),
        "RH2M": round(old["RH2M"] + (new["RH2M"] - old["RH2M"]) * frac, 2),
        "GWETROOT": round(old["GWETROOT"] + (new["GWETROOT"] - old["GWETROOT"]) * frac, 4),
        "PRECTOTCORR": new["PRECTOTCORR"],
    }

import datetime as dt

def _aggregate_hourly_to_weekly(hourly_data: dict, season_start: dt.date) -> tuple:
    """Aggregate 16-day hourly forecast into weekly averages relative to season start.
    Returns (weekly_dict, forecast_week_mask) where forecast_week_mask[wk] = True if forecast covers that week."""
    times = hourly_data.get("time", [])
    vars_h = {"T2M": "temperature_2m", "RH2M": "relative_humidity_2m", "PRECTOTCORR": "precipitation"}
    weekly = {"PRECTOTCORR": [0]*12, "T2M": [0]*12, "RH2M": [0]*12, "GWETROOT": [0]*12}
    counts = [0]*12
    mask = [False]*12

    for i, t_str in enumerate(times):
        try:
            h = dt.datetime.fromisoformat(t_str)
        except ValueError:
            h = dt.datetime.strptime(t_str, "%Y-%m-%dT%H:%M")
        d = h.date()
        days_from = (d - season_start).days
        if not (0 <= days_from < 84):
            continue
        wk = days_from // 7
        for k, api_key in vars_h.items():
            vals = hourly_data.get(api_key, [])
            if i < len(vals) and vals[i] is not None:
                weekly[k][wk] += float(vals[i])
        counts[wk] += 1
        mask[wk] = True

    for wk in range(12):
        if counts[wk] > 0:
            for k in ["T2M", "RH2M"]:
                weekly[k][wk] = round(weekly[k][wk] / counts[wk], 2)
            weekly["PRECTOTCORR"][wk] = round(weekly["PRECTOTCORR"][wk], 2)

    return weekly, mask


@app.post("/api/realtime/coordinate")
async def realtime_coordinate(request: RealtimeCoordinateRequest):
    cache_key = f"{request.latitude:.4f}_{request.longitude:.4f}"
    now = time.time()
    provided = (request.district or "").strip()
    # A pinned/field coordinate may carry a non-district label (e.g. "Unknown").
    # Resolve to the nearest valid district so the prediction pipeline (which
    # raises on cold-start districts) still produces a result.
    district = provided if provided in DISTRICT_COORDS else find_district_by_boundary(request.latitude, request.longitude)
    year = request.year
    season = request.season
    today = dt.date.today()
    season_month = 6 if season.lower() == "kharif" else 11
    season_day = 15 if season.lower() == "kharif" else 1
    season_start = dt.date(year, season_month, season_day)
    current_week = max(0, min(11, (today - season_start).days // 7))

    # 1. Fetch Open-Meteo (current + 16-day hourly) in one call
    snapshot = None
    is_mocked = False
    forecast_weekly = None
    forecast_mask = None
    data = None

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": request.latitude,
                    "longitude": request.longitude,
                    "current": "temperature_2m,relative_humidity_2m,precipitation",
                    "hourly": "temperature_2m,relative_humidity_2m,precipitation,soil_moisture_9_to_27cm",
                    "timezone": "auto",
                    "forecast_days": 16,
                }
            )
            resp.raise_for_status()
            data = resp.json()

        current = data.get("current", {})
        hourly = data.get("hourly", {})
        soil_hourly = hourly.get("soil_moisture_9_to_27cm", []) if hourly else []
        # Use hourly forecast precipitation for current hour (accumulated mm, not instantaneous rate)
        hourly_precip = hourly.get("precipitation", []) if hourly else []
        precip = hourly_precip[0] if hourly_precip else current.get("precipitation", 0)
        snapshot = {
            "T2M": current.get("temperature_2m", 30),
            "RH2M": current.get("relative_humidity_2m", 70),
            "PRECTOTCORR": precip,
            "GWETROOT": soil_hourly[0] if soil_hourly else 0.5,
        }

        # Aggregate hourly forecast to weekly
        forecast_weekly, forecast_mask = _aggregate_hourly_to_weekly(hourly, season_start)

        # Update cache for interpolation
        cached_entry = realtime_cache.get(cache_key)
        if cached_entry:
            realtime_cache[cache_key] = {
                "t0": cached_entry.get("t1", now), "v0": cached_entry.get("v1", snapshot),
                "t1": now, "v1": snapshot,
            }
        else:
            realtime_cache[cache_key] = {"t0": now, "v0": snapshot, "t1": now, "v1": snapshot}

    except Exception as e:
        cached_entry = realtime_cache.get(cache_key)
        if cached_entry:
            snapshot = _interpolate_snapshot(
                cached_entry["v0"], cached_entry["v1"],
                cached_entry["t0"], cached_entry["t1"], now
            )
        else:
            snapshot = {"T2M": 30, "RH2M": 70, "PRECTOTCORR": 0, "GWETROOT": 0.5}
        is_mocked = True

    # 2. Build blended 12-week profile
    # Base: 20-year climatology
    clim = _get_climatology(district, season)
    if clim:
        weekly = {var: list(clim[var]) for var in ["PRECTOTCORR", "T2M", "RH2M", "GWETROOT"]}
        week_sources = ["climatology"] * 12
    else:
        weekly = {
            "PRECTOTCORR": [round(10 + 15 * math.sin(i * math.pi / 11), 2) for i in range(12)],
            "T2M": [round(27 + 5 * math.sin(i * math.pi / 11 - 0.3), 2) for i in range(12)],
            "RH2M": [round(70 + 15 * math.sin(i * math.pi / 11 + 0.5), 2) for i in range(12)],
            "GWETROOT": [round(max(0, min(1, 0.5 + 0.2 * math.sin(i * math.pi / 11 - 0.4))), 4) for i in range(12)],
        }
        week_sources = ["synthetic"] * 12

    # Overlay forecast where available
    if forecast_weekly and forecast_mask:
        for wk in range(12):
            if forecast_mask[wk]:
                for var in ["T2M", "RH2M", "PRECTOTCORR"]:
                    if forecast_weekly[var][wk] is not None:
                        weekly[var][wk] = forecast_weekly[var][wk]
                week_sources[wk] = "forecast"

    # Overlay today's snapshot at current week (highest priority)
    week_sources[current_week] = "now"
    weekly["T2M"][current_week] = round(snapshot["T2M"], 2)
    weekly["RH2M"][current_week] = round(snapshot["RH2M"], 2)
    # NOTE: keep PRECTOTCORR as a weekly-scale value (climatology/forecast) for
    # the current week so the 12-week chart bar matches the other weeks' scale.
    # The instantaneous snapshot precip is still shown in the real-time gauge via
    # `telemetry.PRECTOTCORR` (frontend), which is correct for a current reading.
    weekly["GWETROOT"][current_week] = round(snapshot["GWETROOT"], 4)

    # 3. Run prediction on blended profile
    try:
        # Pass weekly dict — run_orchestrator calls telemetry_to_flat48 internally
        result = run_orchestrator(district, season, year, weekly, query_type_str="full_diagnosis")
    except Exception as e:
        result = None

    return {
        "telemetry": snapshot,
        "telemetry_weekly": weekly,
        "week_sources": week_sources,
        "current_week": current_week,
        "prediction": result,
        "fetched_at": dt.datetime.fromtimestamp(
            realtime_cache.get(cache_key, {}).get("t1", now)
        ).isoformat() if cache_key in realtime_cache else None,
        "nearest_district": district,
        "is_mocked": is_mocked,
        "season_source": "climatology",
    }


# ===================================================================
# PIPELINE UPDATE ENDPOINTS
# ===================================================================

import uuid, traceback
from update_pipeline import (
    check_new_data, run_pipeline, get_current_version,
    get_dataset_info, DEFAULT_STEPS
)

pipeline_tasks: Dict[str, dict] = {}
DEMO_CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "sources", "data", "new_yield_2025_demo.csv"
)


def _pipeline_worker(task_id: str, csv_path: str):
    def status_callback(status):
        if isinstance(status, dict):
            pipeline_tasks[task_id].update(status)
        elif isinstance(status, str):
            pipeline_tasks[task_id]["step"] = status

    try:
        pipeline_tasks[task_id]["status"] = "running"
        result = run_pipeline(csv_path, status_callback=status_callback)
        pipeline_tasks[task_id].update(result)
        pipeline_tasks[task_id]["status"] = "success"
    except Exception as e:
        pipeline_tasks[task_id]["status"] = "failed"
        pipeline_tasks[task_id]["error"] = str(e)
        pipeline_tasks[task_id]["traceback"] = traceback.format_exc()


class PipelineCheckResponse(BaseModel):
    new_data: bool
    latest_year: Optional[int] = None
    total_records: int = 0
    new_records: int = 0
    new_years: List[int] = []
    file_path: Optional[str] = None


@app.get("/api/pipeline/check")
def check_pipeline():
    result = check_new_data(csv_path=DEMO_CSV_PATH)
    return PipelineCheckResponse(**result)


@app.post("/api/pipeline/update")
def trigger_pipeline_update():
    if not os.path.exists(DEMO_CSV_PATH):
        raise HTTPException(status_code=404, detail="Demo CSV not found. Generate one first.")

    check = check_new_data(csv_path=DEMO_CSV_PATH)
    if not check.get("new_data"):
        raise HTTPException(status_code=400, detail="No new data found to process.")

    task_id = str(uuid.uuid4())
    pipeline_tasks[task_id] = {
        "task_id": task_id,
        "status": "queued",
        "step": "queued",
        "progress": 0,
        "total_steps": len(DEFAULT_STEPS),
        "created_at": time.time()
    }

    thread = threading.Thread(target=_pipeline_worker, args=(task_id, DEMO_CSV_PATH), daemon=True)
    thread.start()

    return {"task_id": task_id, "status": "queued"}


@app.get("/api/pipeline/status/{task_id}")
def get_pipeline_status(task_id: str):
    task = pipeline_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return {
        "task_id": task["task_id"],
        "status": task["status"],
        "step": task.get("step", "unknown"),
        "progress": task.get("progress", 0),
        "error": task.get("error"),
        "train_output": task.get("train_output", "")[-200:] if task.get("train_output") else None,
    }


class PipelineVersionResponse(BaseModel):
    version: str
    last_trained: Optional[str] = None
    metrics: dict = {}
    total_records: int = 0


@app.get("/api/pipeline/version")
def get_pipeline_version():
    version_data = get_current_version()
    dataset_info = get_dataset_info() if not df_dataset.empty else {}
    return PipelineVersionResponse(
        version=version_data.get("version", "1.0"),
        last_trained=version_data.get("last_trained"),
        metrics=version_data.get("metrics", {}),
        total_records=dataset_info.get("total_records", 0)
    )


@app.get("/demo-new-data")
def serve_demo_csv():
    """Serves the demo CSV for testing the pipeline check flow."""
    if not os.path.exists(DEMO_CSV_PATH):
        raise HTTPException(status_code=404, detail="Demo CSV not found.")
    import csv
    rows = []
    with open(DEMO_CSV_PATH) as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return {"data": rows, "count": len(rows), "source": "demo_2025_kharif"}


# ===================================================================
# REAL-TIME HISTORICAL REPLAY STREAM (WebSocket Direct)
# ===================================================================
import asyncio
import csv
from collections import deque

main_loop = None

@app.on_event("startup")
def startup_event():
    global main_loop
    try:
        main_loop = asyncio.get_running_loop()
    except RuntimeError:
        main_loop = None

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

# Stream sessions
stream_sessions: Dict[str, dict] = {}
_session_counter = 0

SEASON_START = {"Kharif": "0615", "Rabi": "1101"}

def _generate_synthetic_daily(district: str, year: int, season: str):
    import math, random
    rng = random.Random(hash(f"{district}{year}{season}"))
    month, day = int(SEASON_START[season][:2]), int(SEASON_START[season][2:])
    start_dt = dt.datetime(year, month, day)
    days = 120 if season == "Kharif" else 84
    data = []
    for i in range(days):
        dt = start_dt + __import__('datetime').timedelta(days=i)
        progress = i / days
        data.append({
            "date": dt.strftime("%Y%m%d"),
            "PRECTOTCORR": round(max(0, 8 + rng.gauss(0, 5) + 20 * math.sin(progress * math.pi)), 2),
            "T2M": round(27 + 5 * math.sin(progress * math.pi - 0.3) + rng.gauss(0, 0.8), 2),
            "RH2M": round(70 + 15 * math.sin(progress * math.pi + 0.5) + rng.gauss(0, 4), 2),
            "GWETROOT": round(max(0, min(1, 0.5 + 0.2 * math.sin(progress * math.pi - 0.4) + rng.gauss(0, 0.04))), 4),
        })
    return data

def _load_daily_data(district: str, year: int, season: str):
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           "sources", "data", "telemetry", f"{district.lower()}_daily.csv")
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            data = []
            for r in reader:
                if "date" not in r and "Date" in r:
                    r["date"] = r.pop("Date")
                data.append(r)
            return data
    print(f"[STREAM] CSV not found: {csv_path}, using synthetic data")
    return _generate_synthetic_daily(district, year, season)

def _prefill_buffer(daily_data, start_idx):
    buf = deque(maxlen=84)
    prefill_start = max(0, start_idx - 84)
    for i in range(prefill_start, start_idx):
        d = daily_data[i]
        buf.append([float(d["PRECTOTCORR"]), float(d["T2M"]), float(d["RH2M"]), float(d["GWETROOT"])])
    while len(buf) < 84 and daily_data:
        d = daily_data[0]
        buf.appendleft([float(d["PRECTOTCORR"]), float(d["T2M"]), float(d["RH2M"]), float(d["GWETROOT"])])
    return buf

def _buffer_to_weekly(buf):
    t = {"PRECTOTCORR": [], "T2M": [], "RH2M": [], "GWETROOT": []}
    lst = list(buf)
    for w in range(12):
        week = lst[w*7 : (w+1)*7]
        t["PRECTOTCORR"].append(round(sum(r[0] for r in week), 2))
        t["T2M"].append(round(sum(r[1] for r in week) / 7, 2))
        t["RH2M"].append(round(sum(r[2] for r in week) / 7, 2))
        t["GWETROOT"].append(round(sum(r[3] for r in week) / 7, 2))
    return t

def _season_weekly(daily_data, start_idx, current_idx):
    """Season-anchored 12-week aggregates for DISPLAY only.

    Week w = the season's own days [start_idx + 7w, start_idx + 7(w+1)).
    Unlike _buffer_to_weekly (which cuts a sliding 84-day window), these
    buckets are fixed to the season, so a week's value is final the moment
    that week completes and never drifts as later weeks arrive.

    Behaviour during replay:
    - Future week (not started)        -> null (no bar drawn yet)
    - In-progress week (partial days)  -> running aggregate of days seen so
      far, so the bar grows/shrinks live as the week accumulates
    - Completed week (all 7 days done) -> fixed full aggregate (never moves)
    """
    t = {"PRECTOTCORR": [], "T2M": [], "RH2M": [], "GWETROOT": []}
    for w in range(12):
        s = start_idx + w * 7
        e = start_idx + (w + 1) * 7
        last_day = e - 1
        if s > current_idx:
            # Future week, not started yet.
            t["PRECTOTCORR"].append(None)
            t["T2M"].append(None)
            t["RH2M"].append(None)
            t["GWETROOT"].append(None)
            continue
        if last_day > current_idx:
            # In-progress week: aggregate only the days seen so far.
            chunk = daily_data[s:current_idx + 1]
        else:
            # Completed week: aggregate all 7 days (fixed).
            chunk = daily_data[s:e]
        if not chunk:
            t["PRECTOTCORR"].append(None)
            t["T2M"].append(None)
            t["RH2M"].append(None)
            t["GWETROOT"].append(None)
            continue
        prec = sum(float(r["PRECTOTCORR"]) for r in chunk)
        t2m = sum(float(r["T2M"]) for r in chunk) / len(chunk)
        rh = sum(float(r["RH2M"]) for r in chunk) / len(chunk)
        gw = sum(float(r["GWETROOT"]) for r in chunk) / len(chunk)
        t["PRECTOTCORR"].append(round(prec, 2))
        t["T2M"].append(round(t2m, 2))
        t["RH2M"].append(round(rh, 2))
        t["GWETROOT"].append(round(gw, 4))
    return t

def virtual_sensor_worker(session_id: str, district: str, year: int, season: str, speed: float):
    global stream_sessions
    session = stream_sessions.get(session_id)
    if not session:
        return

    daily_data = _load_daily_data(district, year, season)
    start_str = f"{year}{SEASON_START.get(season, '0615')}"
    # Bound the replay to the fixed season window (e.g. Kharif Jun15-Sep6,
    # Rabi Nov1-Jan23), not the entire 1981-2026 CSV. Otherwise `total` spans
    # hundreds of post-season days and the progress counter is meaningless.
    _, end_str = get_season_dates(year, season)
    start_idx = end_idx = None
    for i, d in enumerate(daily_data):
        if d["date"] == start_str:
            start_idx = i
        if d["date"] == end_str:
            end_idx = i
        if start_idx is not None and end_idx is not None:
            break

    if start_idx is None:
        start_idx = 0
    if end_idx is None:
        # Synthetic fallback / missing end date: clamp to ~12 weeks.
        end_idx = min(start_idx + 83, len(daily_data) - 1)

    buf = _prefill_buffer(daily_data, start_idx)
    session["total"] = end_idx - start_idx + 1
    session["progress"] = 0

    for i in range(start_idx, end_idx + 1):
        sess = stream_sessions.get(session_id)
        if not sess or sess.get("status") == "stopped":
            break
        while sess.get("status") == "paused":
            time.sleep(0.5)
            sess = stream_sessions.get(session_id)
            if not sess or sess["status"] == "stopped":
                return

        d = daily_data[i]
        buf.append([float(d["PRECTOTCORR"]), float(d["T2M"]), float(d["RH2M"]), float(d["GWETROOT"])])
        # Rolling 84-day window feeds the model (trained-feature consistency).
        model_telemetry = _buffer_to_weekly(buf)
        # Season-anchored weeks feed the UI so each week's value is fixed once complete.
        display_telemetry = _season_weekly(daily_data, start_idx, i)
        result = run_orchestrator(district, season, year, model_telemetry, "full_diagnosis")

        sess["current_date"] = d["date"]
        sess["progress"] = i - start_idx + 1

        out_msg = json.dumps({
            "type": "REAL_TIME_UPDATE",
            "date": d["date"],
            "district": district,
            "season": season,
            "year": year,
            "telemetry": display_telemetry,
            "prediction": result,
        })
        if main_loop is not None:
            asyncio.run_coroutine_threadsafe(manager.broadcast(out_msg), main_loop)

        actual_speed = stream_sessions.get(session_id, {}).get("speed", speed)
        time.sleep(actual_speed)

    if session_id in stream_sessions:
        stream_sessions[session_id]["status"] = "stopped"

    complete_msg = json.dumps({
        "type": "REPLAY_COMPLETE",
        "session_id": session_id,
        "district": district,
        "season": season,
        "year": year,
    })
    if main_loop is not None:
        asyncio.run_coroutine_threadsafe(manager.broadcast(complete_msg), main_loop)

class StreamStartRequest(BaseModel):
    district: str = "Ganjam"
    year: int = 2024
    season: str = "Kharif"
    speed: float = 1.5

    @field_validator("speed")
    @classmethod
    def speed_positive(cls, v):
        if v <= 0:
            raise ValueError("speed must be positive")
        return v

class StreamSessionRequest(BaseModel):
    session_id: str

class StreamSpeedRequest(BaseModel):
    session_id: str
    speed: float = 1.5

@app.post("/api/stream/start")
def start_stream(request: StreamStartRequest):
    global _session_counter, stream_sessions
    district = request.district
    year = request.year
    season = request.season
    speed = request.speed

    _session_counter += 1
    session_id = f"stream_{_session_counter}_{int(time.time())}"
    stream_sessions[session_id] = {
        "status": "playing", "district": district, "year": year,
        "season": season, "speed": speed, "progress": 0, "total": 0,
        "current_date": None, "created_at": time.time(),
    }

    t = threading.Thread(target=virtual_sensor_worker,
                         args=(session_id, district, year, season, speed), daemon=True)
    t.start()
    stream_sessions[session_id]["thread"] = t
    return {"session_id": session_id, "status": "playing"}

@app.post("/api/stream/stop")
def stop_stream(request: StreamSessionRequest):
    session_id = request.session_id
    if session_id and session_id in stream_sessions:
        stream_sessions[session_id]["status"] = "stopped"
        return {"status": "stopped", "session_id": session_id}
    for sid in list(stream_sessions.keys()):
        stream_sessions[sid]["status"] = "stopped"
    return {"status": "stopped", "sessions_stopped": len(stream_sessions)}

@app.post("/api/stream/pause")
def pause_stream(request: StreamSessionRequest):
    session_id = request.session_id
    if session_id in stream_sessions:
        stream_sessions[session_id]["status"] = "paused"
        return {"status": "paused"}
    return {"error": "Session not found"}

@app.post("/api/stream/resume")
def resume_stream(request: StreamSessionRequest):
    session_id = request.session_id
    if session_id in stream_sessions:
        stream_sessions[session_id]["status"] = "playing"
        return {"status": "playing"}
    return {"error": "Session not found"}

@app.post("/api/stream/speed")
def set_stream_speed(request: StreamSpeedRequest):
    session_id = request.session_id
    speed = request.speed
    if session_id and session_id in stream_sessions:
        stream_sessions[session_id]["speed"] = speed
        return {"status": "ok", "speed": speed}
    return {"error": "Session not found"}

@app.get("/api/stream/status/{session_id}")
def get_stream_status(session_id: str):
    sess = stream_sessions.get(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session_id,
        "status": sess["status"],
        "district": sess["district"],
        "year": sess["year"],
        "season": sess["season"],
        "speed": sess["speed"],
        "current_date": sess["current_date"],
        "progress": sess["progress"],
        "total": sess["total"],
    }

@app.websocket("/ws/farm-stream")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)

