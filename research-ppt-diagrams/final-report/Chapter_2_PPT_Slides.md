# Literature Review (For PPT Slides)

## Slide 1: Review of Existing Models
*   **(Andini, 2021): LSTM Climate Forecasting**
    *   *Pro:* High accuracy for 1-month-ahead weather.
    *   *Gap:* Too short-term (1 month); ignores critical soil moisture.
*   **(Arya, 2026): Hybrid Time-Series for Rice**
    *   *Pro:* 98.4% R² yield accuracy using deep learning.
    *   *Gap:* "Black-box" architecture; lacks AI explainability for failure causes.
*   **(Banerjee, 2024): IoT Digital Twin**
    *   *Pro:* Mirrors physical farm environment to boost yield.
    *   *Gap:* Relies on expensive physical sensors; unscalable for rural farmers.

## Slide 2: Review of Existing Models (Cont.)
*   **(Yan, 2025): Hybrid ML (RF + XGBoost)**
    *   *Pro:* Highly accurate yield volume prediction.
    *   *Gap:* Predicts absolute volume (t/ha), doesn't trigger binary "disaster/failure" alerts.
*   **(Kenneth, 2026): Satellite Telemetry + Monte Carlo**
    *   *Pro:* Uses NASA POWER data to model weather uncertainty.
    *   *Gap:* Ignores biological stress (pests); lacks an automated Decision Support System.

## Slide 3: The Research Gap We Solved
1.  **Prediction Labeling:** Shifted from predicting just volume to classifying actionable "Failure Anomalies".
2.  **Scalability:** Eliminated expensive IoT sensors by using 100% free global satellite data.
3.  **Explainability:** Added a Groq LLM layer to translate opaque Deep Learning into plain-English advice.
