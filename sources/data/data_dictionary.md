# Data Dictionary: final_dataset.csv
**System target**: Cyber-Physical Digital Twin (CPDT) Spatial-Temporal Dataset  
**Scope**: 30 Districts of Odisha, India (2006 to 2025)

This reference table specifies the data types, measurement units, aggregation methods, and definitions for all 58 columns in [final_dataset.csv](file:///C:/Users/Asus/Desktop/Research/Research-Wiki/sources/data/final_dataset.csv).

| Column Name | Data Type | Units | Aggregation | Description |
| :--- | :--- | :--- | :--- | :--- |
| `District` | String | N/A | N/A | Standard administrative district name in Odisha (30 districts total). |
| `Year` | Integer | N/A | N/A | Crop year (ranging from 2006 to 2025). |
| `Season` | String | N/A | N/A | Crop cultivation season: Kharif or Rabi. |
| `Area` | Float | Hectares (ha) | Sum | Total cultivated area for the district, year, and season. |
| `Production` | Float | Tonnes (MT) | Sum | Total harvested production weight. |
| `Yield_MTha` | Float | Tonnes/Hectare | N/A | Crop productivity rate calculated as Production / Area. |
| `Is_Interpolated` | Boolean | N/A | N/A | Flag indicating if Area/Production were filled via linear interpolation (1 = True, 0 = False). |
| `Yield_Q_Acre` | Float | Quintals/Acre | N/A | Yield converted to Quintals/Acre: (Yield_MTha * 10) / 2.471. |
| `Q1_Threshold` | Float | Quintals/Acre | N/A | 25th percentile (Q1) of Yield_Q_Acre computed historically for this district and season. |
| `Failure_Anomaly` | Integer | N/A | N/A | Anomaly flag: 1 if Yield_Q_Acre < Q1_Threshold, else 0. |
| `W1_PRECTOTCORR` | Float | Millimeters (mm) | Sum | Week 1 cumulative precipitation (total rainfall). |
| `W1_T2M` | Float | Degrees Celsius (°C) | Mean | Week 1 average temperature at 2 meters. |
| `W1_RH2M` | Float | Percent (%) | Mean | Week 1 average relative humidity. |
| `W1_GWETROOT` | Float | Volumetric ratio (0.0-1.0) | Mean | Week 1 average root zone soil wetness. |
| `W2_PRECTOTCORR` | Float | Millimeters (mm) | Sum | Week 2 cumulative precipitation (total rainfall). |
| `W2_T2M` | Float | Degrees Celsius (°C) | Mean | Week 2 average temperature at 2 meters. |
| `W2_RH2M` | Float | Percent (%) | Mean | Week 2 average relative humidity. |
| `W2_GWETROOT` | Float | Volumetric ratio (0.0-1.0) | Mean | Week 2 average root zone soil wetness. |
| `W3_PRECTOTCORR` | Float | Millimeters (mm) | Sum | Week 3 cumulative precipitation (total rainfall). |
| `W3_T2M` | Float | Degrees Celsius (°C) | Mean | Week 3 average temperature at 2 meters. |
| `W3_RH2M` | Float | Percent (%) | Mean | Week 3 average relative humidity. |
| `W3_GWETROOT` | Float | Volumetric ratio (0.0-1.0) | Mean | Week 3 average root zone soil wetness. |
| `W4_PRECTOTCORR` | Float | Millimeters (mm) | Sum | Week 4 cumulative precipitation (total rainfall). |
| `W4_T2M` | Float | Degrees Celsius (°C) | Mean | Week 4 average temperature at 2 meters. |
| `W4_RH2M` | Float | Percent (%) | Mean | Week 4 average relative humidity. |
| `W4_GWETROOT` | Float | Volumetric ratio (0.0-1.0) | Mean | Week 4 average root zone soil wetness. |
| `W5_PRECTOTCORR` | Float | Millimeters (mm) | Sum | Week 5 cumulative precipitation (total rainfall). |
| `W5_T2M` | Float | Degrees Celsius (°C) | Mean | Week 5 average temperature at 2 meters. |
| `W5_RH2M` | Float | Percent (%) | Mean | Week 5 average relative humidity. |
| `W5_GWETROOT` | Float | Volumetric ratio (0.0-1.0) | Mean | Week 5 average root zone soil wetness. |
| `W6_PRECTOTCORR` | Float | Millimeters (mm) | Sum | Week 6 cumulative precipitation (total rainfall). |
| `W6_T2M` | Float | Degrees Celsius (°C) | Mean | Week 6 average temperature at 2 meters. |
| `W6_RH2M` | Float | Percent (%) | Mean | Week 6 average relative humidity. |
| `W6_GWETROOT` | Float | Volumetric ratio (0.0-1.0) | Mean | Week 6 average root zone soil wetness. |
| `W7_PRECTOTCORR` | Float | Millimeters (mm) | Sum | Week 7 cumulative precipitation (total rainfall). |
| `W7_T2M` | Float | Degrees Celsius (°C) | Mean | Week 7 average temperature at 2 meters. |
| `W7_RH2M` | Float | Percent (%) | Mean | Week 7 average relative humidity. |
| `W7_GWETROOT` | Float | Volumetric ratio (0.0-1.0) | Mean | Week 7 average root zone soil wetness. |
| `W8_PRECTOTCORR` | Float | Millimeters (mm) | Sum | Week 8 cumulative precipitation (total rainfall). |
| `W8_T2M` | Float | Degrees Celsius (°C) | Mean | Week 8 average temperature at 2 meters. |
| `W8_RH2M` | Float | Percent (%) | Mean | Week 8 average relative humidity. |
| `W8_GWETROOT` | Float | Volumetric ratio (0.0-1.0) | Mean | Week 8 average root zone soil wetness. |
| `W9_PRECTOTCORR` | Float | Millimeters (mm) | Sum | Week 9 cumulative precipitation (total rainfall). |
| `W9_T2M` | Float | Degrees Celsius (°C) | Mean | Week 9 average temperature at 2 meters. |
| `W9_RH2M` | Float | Percent (%) | Mean | Week 9 average relative humidity. |
| `W9_GWETROOT` | Float | Volumetric ratio (0.0-1.0) | Mean | Week 9 average root zone soil wetness. |
| `W10_PRECTOTCORR` | Float | Millimeters (mm) | Sum | Week 10 cumulative precipitation (total rainfall). |
| `W10_T2M` | Float | Degrees Celsius (°C) | Mean | Week 10 average temperature at 2 meters. |
| `W10_RH2M` | Float | Percent (%) | Mean | Week 10 average relative humidity. |
| `W10_GWETROOT` | Float | Volumetric ratio (0.0-1.0) | Mean | Week 10 average root zone soil wetness. |
| `W11_PRECTOTCORR` | Float | Millimeters (mm) | Sum | Week 11 cumulative precipitation (total rainfall). |
| `W11_T2M` | Float | Degrees Celsius (°C) | Mean | Week 11 average temperature at 2 meters. |
| `W11_RH2M` | Float | Percent (%) | Mean | Week 11 average relative humidity. |
| `W11_GWETROOT` | Float | Volumetric ratio (0.0-1.0) | Mean | Week 11 average root zone soil wetness. |
| `W12_PRECTOTCORR` | Float | Millimeters (mm) | Sum | Week 12 cumulative precipitation (total rainfall). |
| `W12_T2M` | Float | Degrees Celsius (°C) | Mean | Week 12 average temperature at 2 meters. |
| `W12_RH2M` | Float | Percent (%) | Mean | Week 12 average relative humidity. |
| `W12_GWETROOT` | Float | Volumetric ratio (0.0-1.0) | Mean | Week 12 average root zone soil wetness. |
