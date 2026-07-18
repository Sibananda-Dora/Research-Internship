# Algorithm 1: Data Ingestion & Harmonization Pipeline (`prepare_data.py`)

## Visual Flowchart (Mermaid)

```mermaid
flowchart TD
    in1[(Raw Yield CSVs)]
    in2[(NASA POWER\nTelemetry CSVs)]
    
    subgraph DistrictLoop["For each of the 30 Districts"]
        direction TB
        A["Load & Standardize"] --> B
        B["Extract 84-Day Window\nper (Year, Season)"] --> C
        C["Aggregate daily to 12 weekly means\n4 weather vars"] --> D
        D["Append Static Features:\nd_idx, season, yr-2006"] --> E
        E["Compute Q1 Threshold per District\nFailure = Yield < Q1"]
    end
    
    in1 --> DistrictLoop
    in2 --> DistrictLoop
    
    DistrictLoop --> Out["Save to prepared_data/\nX_seq, y_yield, y_fail, scalers"]
```

## Brief

**Input:** Govt yield CSVs + NASA POWER daily telemetry (4 vars).
**Output:** Synchronized tensors `X_seq (1113, 84, 4)`, `y_yield`, `y_fail`, scalers.

**Steps:**
1. Extract 84-day window per (district, year, season) — Kharif: Jun 15, Rabi: Nov 1
2. Aggregate 84 daily records → 12 weekly means per variable
3. Append static features: `[district_idx, season_onehot, year-2006]`
4. Compute Q₁ (25th percentile) threshold per district×season → label `failure = yield < Q₁`
5. Scale features → save tensors + encoders

**Key novelty:** Absolute year offset (`year-2006`) preserves temporal generalization across post-COVID yield regime shifts. Dual-target engineering prepares data for both regression (yield) and classification (failure) simultaneously.
