# NASA POWER Integration

This concept documents the design, scraping architecture, and aggregation logic for integrating environmental telemetry from the NASA POWER API into the Cognitive Digital Twin (CDT) crop yield and failure prediction models. This pipeline forms the core of **Layer 2: Data Acquisition Layer** in the [[Cognitive Digital Twin — Architecture]].

## 1. Scraping Architecture
To minimize API requests and avoid rate limiting, the ingestion is split into two phases:
1. **Raw Cache**: [fetch_nasa_telemetry.py](code/fetch_nasa_telemetry.py) downloads the entire 45-year daily timeline (Jan 1, 1981 to Dec 31, 2026) for each of the 30 district centroids in a single request per district. This results in exactly 30 CSV files containing 16,587 days of daily records cached under `sources/data/telemetry/`.
2. **Feature Extraction**: [merge_telemetry_yield.py](code/merge_telemetry_yield.py) processes the daily records, extracts the crop vegetative windows, aggregates them, and merges them with the yield dataset. The current pipeline in `code/phase-2-training/prepare_data.py` additionally extracts 84-step daily sequences directly from the telemetry CSVs for the LSTM model.

## 2. Vegetative Cycle Windows
For each Crop Year ($Y$), the 12-week (84-day) daily weather window is determined based on the season:
- **Kharif Season**: Represents the main monsoon crop. Sowing/planting starts in mid-June.
  - **Window**: June 15th to September 6th of year $Y$ (inclusive).
  - **Start Date**: `Y-06-15`
  - **End Date**: `Y-09-06`
- **Rabi Season**: Represents the irrigated winter/summer crop. Sowing starts in November.
  - **Window**: November 1st to January 23rd of the following year $Y+1$ (inclusive, 84 days).
  - **Start Date**: `Y-11-01`
  - **End Date**: `(Y+1)-01-23`

## 3. Weekly Aggregation Logic
The daily values within the 84-day window are grouped into 12 consecutive weeks (7 days each). For each week $w \in \{1 \dots 12\}$, features are computed as:
- **PRECTOTCORR** (Precipitation Corrected): Summed over the 7 days (total weekly rainfall in mm).
  $$Ww\text{\_PRECTOTCORR} = \sum_{d=1}^{7} \text{PRECTOTCORR}_d$$
- **T2M** (2-Meter Temperature): Averaged over the 7 days (°C).
  $$Ww\text{\_T2M} = \frac{1}{7} \sum_{d=1}^{7} \text{T2M}_d$$
- **RH2M** (Relative Humidity): Averaged over the 7 days (%).
  $$Ww\text{\_RH2M} = \frac{1}{7} \sum_{d=1}^{7} \text{RH2M}_d$$
- **GWETROOT** (Root Zone Soil Wetness): Averaged over the 7 days (%).
  $$Ww\text{\_GWETROOT} = \frac{1}{7} \sum_{d=1}^{7} \text{GWETROOT}_d$$

## 4. Output Geometry
The merged dataset contains 1,087 district-season profiles (30 districts × 19 years × 2 seasons, minus 53 Rabi rows with no cultivation). Each profile includes 48 weather columns (12 weeks × 4 variables), outputting a final shape of **(1087, 58)**. The LSTM model additionally uses 84-step daily sequences extracted directly from telemetry CSVs, and a separate unlabeled pretraining dataset of 2,700 sequences (30 districts × 45 years × 2 seasons) was extracted for masked autoencoder pretraining.

## Sources
- [[CPDT-Crop-Failure-Prediction Spec]]
- [[Odisha Pilot]]
- [fetch_nasa_telemetry.py](code/fetch_nasa_telemetry.py)
- [merge_telemetry_yield.py](code/merge_telemetry_yield.py)
- [final_dataset.csv](sources/data/final_dataset.csv)
- [prepare_data.py](code/phase-2-training/prepare_data.py) — 84-step daily sequence extraction
- [prepare_pretrain_data.py](code/phase-2-training/prepare_pretrain_data.py) — unlabeled pretraining sequences
