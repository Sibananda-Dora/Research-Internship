# Source: CPDT-Crop-Failure-Prediction Spec

**Title**: Development of a Cyber-Physical Digital Twin Framework for Joint Crop Yield Forecasting and Climate-Induced Failure Anomaly Detection
**Identity**: CPDT-Crop-Failure-Prediction (Odisha Pilot Engine)
**Status**: Core Architecture

## Summary
This specification defines a Cyber-Physical Digital Twin (CPDT) for the Odisha region. It utilizes a dual-track ML/DL approach (Random Forest and LSTM-Attention) to predict both continuous crop yield and binary failure anomalies. The system is orchestrated via a LangGraph DAG to ensure deterministic execution and prevent LLM hallucinations.

## Key Takeaways
- **Spatial Focus**: 30 Districts of Odisha.
- **Temporal Focus**: 20 years of historical data (2006-2026).
- **Data Engine**: NASA POWER API (12-week daily telemetry).
- **Modeling**: 
    - Track A: Tabular Random Forest.
    - Track B: Sequential 3D Tensor LSTM with Temporal Attention.
- **Failure Logic**: Statistical $Q_1$ (25th percentile) thresholding.
- **Safety**: Hard numerical guardrails for the Expert Advisory LLM.

## Related Pages
- [[CPDT Architecture]]
- [[Odisha Pilot]]
- [[LSTM-Attention Model]]
- [[NASA POWER Integration]]

## Sources
- `sources/papers/project_spec.md`
