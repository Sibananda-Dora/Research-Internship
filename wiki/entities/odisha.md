# Odisha Pilot

**Entity**: State-level Pilot Region
**Scope**: Odisha, India

## Administrative Units
The framework operates at the **District-Stratified Resolution**, covering all 30 districts of Odisha. 

### Why District-Level?
- Village-level coordinates lack sufficient target datasets (yield history).
- Meteorological grids (NASA POWER) are optimized for this resolution.

## Historical Depth
- **Years**: 2006 - 2024 (19-year span).
- **Seasons**: Kharif and Rabi (mapped from Summer).
- **Data Points**: 1,087 distinct profiles (30 districts × 19 years × 2 seasons, minus 53 Rabi rows with no cultivation).

## Yield Targets
- **Historical**: Directorate of Economics and Statistics (DE&S) Odisha - "Five Decades of Odisha Agriculture Statistics".
- **Recent (2020-2024)**: Unified Portal for Agricultural Statistics ([[UPAg Portal]]), DESAgri (`aps.dac.gov.in`), and `DES-District-Data-For-2024-25.csv`.
- **Status**: Fully harmonized and integrated with NASA POWER daily climate telemetry.
- **Final Dataset**: [final_dataset.csv](../../sources/data/final_dataset.csv) (1,087 rows, 58 columns, zero interpolated rows).

## Sources
- [[CPDT-Crop-Failure-Prediction Spec]]
- [[Yield Data Harmonization]]
- [[NASA POWER Integration]]
