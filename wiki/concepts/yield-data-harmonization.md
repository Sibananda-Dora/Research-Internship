# Yield Data Harmonization

This concept defines the mathematical and engineering steps to transform raw government statistics into training-ready labels for the Cognitive Digital Twin (CDT) engine. Part of **Layer 2: Data Acquisition Layer** in the [[Cognitive Digital Twin — Architecture]].

## 1. Unit Conversion
Raw statistics in Odisha are typically reported in **Tonnes per Hectare (MT/ha)** or **Kg per Hectare (kg/ha)**. The CPDT spec requires **Quintals per Acre**.

**Conversion Matrix**:
- $1 \text{ MT/ha} = 10 \text{ Quintals/ha}$
- $1 \text{ Hectare} \approx 2.471 \text{ Acres}$
- **Formula**: $\text{Yield (Q/Acre)} = \frac{\text{Yield (MT/ha)} \times 10}{2.471}$

## 2. Statistical Labeling (Q1 Logic)
To train the binary anomaly detection engine, we must synthesize failure markers from historical distributions.

- **Baseline**: 20-year yield history per district.
- **Calculation**: $Q_1$ (25th Percentile) of the yield distribution.
- **Labeling**:
    - `Failure_Anomaly = 1` if $\text{Yield} < Q_1$
    - `Failure_Anomaly = 0` if $\text{Yield} \ge Q_1$

## 3. Implementation and Gap Resolution (2020-2024)
The data gaps for 2020–2023 and 2025 were successfully resolved in [harmonize_yield.py](file:///C:/Users/Asus/Desktop/Research/Research-Wiki/code/harmonize_yield.py) using **linear interpolation** grouped by `District` and `Season`. 
- **Spelling Standardization**: Mapped administrative name discrepancies (e.g. `ANUGUL` to `Angul`, `BALESHWAR` to `Balasore`, `KENDUJHAR` to `Keonjhar`, `KHORDHA` to `Khurda`) to match the 30 standard centroids.
- **Division by Zero Protection**: For districts/seasons where no crop was sown (Area = 0.0, e.g. Deogarh and Nayagarh Rabi 2024/2025), Yield is explicitly set to `0.0` instead of yielding `NaN`.
- **Final Yield Distribution**:
  - **Total crop profiles**: 1200 rows (30 districts × 20 years × 2 seasons).
  - **Crop Failure Anomalies**: 284 cases ($23.6\%$).
  - **Standard Profiles**: 916 cases ($76.4\%$).
  - **Output File**: Saved to [harmonized_yield.csv](file:///C:/Users/Asus/Desktop/Research/Research-Wiki/sources/data/harmonized_yield.csv).

## Sources
- [[CPDT-Crop-Failure-Prediction Spec]]
- [[Odisha Pilot]]
- [harmonize_yield.py](file:///C:/Users/Asus/Desktop/Research/Research-Wiki/code/harmonize_yield.py)
- [harmonized_yield.csv](file:///C:/Users/Asus/Desktop/Research/Research-Wiki/sources/data/harmonized_yield.csv)
