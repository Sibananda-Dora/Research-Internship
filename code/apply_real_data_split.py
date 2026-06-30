import pandas as pd
import numpy as np
import joblib
import os
import shutil

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

print('Loading final_dataset and new Rice Data...')
df = pd.read_csv(os.path.join(BASE, 'sources', 'data', 'final_dataset.csv'))

# Load new data and bypass any weird header corruption
rice_df = pd.read_csv(os.path.join(BASE, 'sources', 'data', 'Rice_Data_2026-06-28.csv'), names=['State', 'District', 'Year', 'Area (Ha)', 'Production (Tonnes)', 'Yield (Kg/ha)'])
# Drop rows where 'Year' is not numeric (e.g., the corrupted lines and header lines)
rice_df['Year'] = pd.to_numeric(rice_df['Year'], errors='coerce')
rice_df = rice_df.dropna(subset=['Year'])

rice_df['District'] = rice_df['District'].astype(str).str.strip().str.upper()

DISTRICT_MAP = {
    'ANUGUL': 'Angul', 'ANGUL': 'Angul', 'BALANGIR': 'Balangir', 'BALESHWAR': 'Balasore',
    'BALASORE': 'Balasore', 'BARGARH': 'Bargarh', 'BHADRAK': 'Bhadrak', 'BOUDH': 'Boudh',
    'CUTTACK': 'Cuttack', 'DEOGARH': 'Deogarh', 'DHENKANAL': 'Dhenkanal', 'GAJAPATI': 'Gajapati',
    'GANJAM': 'Ganjam', 'JAGATSINGHAPUR': 'Jagatsinghpur', 'JAGATSINGHPUR': 'Jagatsinghpur',
    'JAJAPUR': 'Jajpur', 'JAJPUR': 'Jajpur', 'JHARSUGUDA': 'Jharsuguda', 'KALAHANDI': 'Kalahandi',
    'KANDHAMAL': 'Kandhamal', 'KENDRAPARA': 'Kendrapara', 'KENDUJHAR': 'Keonjhar', 'KEONJHAR': 'Keonjhar',
    'KHORDHA': 'Khurda', 'KHURDA': 'Khurda', 'KORAPUT': 'Koraput', 'MALKANGIRI': 'Malkangiri',
    'MAYURBHANJ': 'Mayurbhanj', 'NABARANGPUR': 'Nabarangpur', 'NAYAGARH': 'Nayagarh',
    'NUAPADA': 'Nuapada', 'PURI': 'Puri', 'RAYAGADA': 'Rayagada', 'SAMBALPUR': 'Sambalpur',
    'SONEPUR': 'Sonepur', 'SUNDARGARH': 'Sundargarh'
}
rice_df['District'] = rice_df['District'].map(DISTRICT_MAP)

print('Loading XGBoost Regressor to predict weather-informed ratios...')
xgb_reg = joblib.load(os.path.join(BASE, 'sources', 'models', 'xgb_regressor_cdt.pkl'))
weather_cols = [c for c in df.columns if c.startswith('W')]

for idx, row in rice_df.iterrows():
    if pd.isna(row['District']):
        continue
    dist = row['District']
    year = int(row['Year'])
    true_area = float(row['Area (Ha)'])
    true_prod = float(row['Production (Tonnes)'])
    
    idx_k = df[(df['District']==dist) & (df['Year']==year) & (df['Season']=='Kharif')].index
    idx_r = df[(df['District']==dist) & (df['Year']==year) & (df['Season']=='Rabi')].index
    
    if len(idx_k) == 0 or len(idx_r) == 0:
        continue
        
    hist = df[(df['District']==dist) & (df['Year'] < 2020) & (~df['Is_Interpolated'])]
    area_k_sum = hist[hist['Season']=='Kharif']['Area'].sum()
    area_r_sum = hist[hist['Season']=='Rabi']['Area'].sum()
    ratio_area_k = area_k_sum / (area_k_sum + area_r_sum) if (area_k_sum + area_r_sum) > 0 else 0.9
    
    area_k = true_area * ratio_area_k
    area_r = true_area * (1 - ratio_area_k)
    
    k_weather = df.loc[idx_k, weather_cols].values
    r_weather = df.loc[idx_r, weather_cols].values
    
    pred_y_k = max(xgb_reg.predict(k_weather)[0], 0.1)
    pred_y_r = max(xgb_reg.predict(r_weather)[0], 0.1)
    
    pred_mt_k = pred_y_k * 2.471 / 10
    pred_mt_r = pred_y_r * 2.471 / 10
    
    expected_prod_k = area_k * pred_mt_k
    expected_prod_r = area_r * pred_mt_r
    
    if expected_prod_k + expected_prod_r > 0:
        ratio_prod_k = expected_prod_k / (expected_prod_k + expected_prod_r)
    else:
        ratio_prod_k = ratio_area_k
        
    prod_k = true_prod * ratio_prod_k
    prod_r = true_prod * (1 - ratio_prod_k)
    
    yield_mt_k = prod_k / area_k if area_k > 0 else 0
    yield_mt_r = prod_r / area_r if area_r > 0 else 0
    
    df.loc[idx_k, 'Area'] = area_k
    df.loc[idx_k, 'Production'] = prod_k
    df.loc[idx_k, 'Yield_MTha'] = yield_mt_k
    df.loc[idx_k, 'Yield_Q_Acre'] = yield_mt_k * 10 / 2.471
    df.loc[idx_k, 'Is_Interpolated'] = False
    
    df.loc[idx_r, 'Area'] = area_r
    df.loc[idx_r, 'Production'] = prod_r
    df.loc[idx_r, 'Yield_MTha'] = yield_mt_r
    df.loc[idx_r, 'Yield_Q_Acre'] = yield_mt_r * 10 / 2.471
    df.loc[idx_r, 'Is_Interpolated'] = False

df_q1 = df[df['Is_Interpolated']==False].groupby(['District', 'Season'])['Yield_Q_Acre'].quantile(0.25).reset_index()
df_q1.rename(columns={'Yield_Q_Acre': 'New_Q1'}, inplace=True)
df = pd.merge(df, df_q1, on=['District', 'Season'], how='left')

df['Q1_Threshold'] = df['New_Q1'].fillna(df['Q1_Threshold'])
df.drop('New_Q1', axis=1, inplace=True)
df['Failure_Anomaly'] = (df['Yield_Q_Acre'] < df['Q1_Threshold']).astype(int)

print('\n=== OUTLIER CHECK ===')
outliers = df[(df['Yield_Q_Acre'] > 40) | (df['Yield_Q_Acre'] < 0)]
if not outliers.empty:
    print(f'Warning! Found {len(outliers)} highly anomalous yields (negative or >40 Q/Acre).')
    print(outliers[['District', 'Year', 'Season', 'Yield_Q_Acre']])
else:
    print('Clean! No severe mathematical outliers detected in the newly injected data.')

df.to_csv(os.path.join(BASE, 'sources', 'data', 'final_dataset.csv'), index=False)
print('\nSuccessfully updated final_dataset.csv!')
