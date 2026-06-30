# Comparative Analysis: CPDT vs. Global Research (2026)

This page maps the CPDT (Odisha Pilot Engine) against the current state-of-the-art identified in recent literature.

## 1. Feature Comparison Matrix

| Feature | Prev. Research (2021-2025) | Kenneth (2026) | **CPDT (Odisha)** |
| :--- | :--- | :--- | :--- |
| **Data Engine** | Local Sensors / FAO | NASA POWER | NASA POWER + UPAg |
| **Prediction** | Continuous Yield | Yield + Uncertainty | **Yield + Binary Failure** |
| **Time Horizon** | 1 Month | 6 Years History | **12-Week Rolling Tensor** |
| **Explainability** | Black Box | Statistical | **LangGraph Agent Advisor** |
| **Resolution** | Farm or National | Regional | **District-Stratified (Odisha)** |

## 2. Our Strategic Edge

### Addressing the "Label Gap"
Most research focuses on predicting *volume* (t/ha). CPDT introduces the **$Q_1$ Thresholding Logic**, creating the first objective "Failure Anomaly" dataset for Odisha. This allows for classification modeling which is more actionable for disaster relief than mere yield deviation.

### Solving the "Explainability Gap"
The research (Arya 2026, Yan 2025) identifies the lack of trust in "Black Box" predictions. CPDT uses **Temporal Attention Heatmaps** and an **LLM Expert Advisory Node** to translate math into agricultural advice.

### Macro-to-Micro Bridge
While Kenneth (2026) uses NASA data at scale, CPDT bridges this with **Root Zone Soil Wetness (GWETROOT)** and regional **Pest-Risk Indices** derived from Humidity/Temp thresholds—proxying the biotic factors Kenneth ignored.

## Sources
- [[Arya-2026]]
- [[Yan-2025]]
- [[Kenneth-2026]]
- [[Odisha Pilot]]
