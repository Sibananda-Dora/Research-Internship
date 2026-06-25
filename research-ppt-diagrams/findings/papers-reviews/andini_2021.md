### Climate Prediction Using RNN LSTM to Estimate Agricultural Products Based on Koppen Classification (Andini & Utomo, 2021)

1. **Brief Description:** This study focuses on predicting climate variables to optimize agricultural product estimation and mitigate the risk of crop failure due to incompatible climate conditions.
2. **Dataset Used:** A climate time-series dataset structured around the Köppen climate classification system.
3. **Proposed Methodology:** The researchers implemented a Recurrent Neural Network (RNN) architecture utilizing Long Short-Term Memory (LSTM) cells (with 48 input neurons), optimized via the Adam optimizer over 200 epochs.
4. **Key Outcomes:** The methodology successfully achieved high predictive accuracy, yielding a Mean Absolute Percentage Error (MAPE) of just 3.29% for 1-month-ahead climate forecasting.
5. **Research Gaps:** The model's temporal depth is limited to forecasting just one month ahead, rather than projecting a full 12-week agricultural season. Additionally, it omits critical sub-surface environmental features like root zone soil wetness (`GWETROOT`), which are essential for robust biophysical stress modeling.
