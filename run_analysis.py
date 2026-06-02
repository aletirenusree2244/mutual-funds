#!/usr/bin/env python
import pandas as pd
import numpy as np
import requests
import json
import os
import warnings
from datetime import datetime
from pathlib import Path

warnings.filterwarnings('ignore')

BASE_DIR = Path('.')
DATA_RAW_DIR = BASE_DIR / 'data' / 'raw'
DATA_PROCESSED_DIR = BASE_DIR / 'data' / 'processed'
REPORTS_DIR = BASE_DIR / 'reports'

for d in [DATA_RAW_DIR, DATA_PROCESSED_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

print('Project directories:')
print(f'  raw: {DATA_RAW_DIR.resolve()}')
print(f'  reports: {REPORTS_DIR.resolve()}')

# Discover CSVs
csv_files = sorted(DATA_RAW_DIR.glob('*.csv'))
print(f'Found {len(csv_files)} CSV file(s) in data/raw')

datasets = {}
anomalies = {}

for csv_file in csv_files:
    print('\n' + '='*60)
    print(f'Loading: {csv_file.name}')
    try:
        df = pd.read_csv(csv_file)
        # Normalize dataset key: prefer meaningful names without leading numbers
        stem = csv_file.stem
        key = stem
        if 'fund_master' in stem.lower():
            key = 'fund_master'
        elif 'nav_history' in stem.lower():
            key = 'nav_history'
        else:
            # remove leading numeric prefix like '01_' if present
            key = stem
            if '_' in stem and stem.split('_')[0].isdigit():
                key = '_'.join(stem.split('_')[1:])
        datasets[key] = df
        print(f'  shape: {df.shape}')
        print('  dtypes:')
        print(df.dtypes)
        print('  head:')
        print(df.head().to_string())
        print('  missing values:', df.isnull().sum().sum())
        print('  duplicate rows:', df.duplicated().sum())
        anomalies[csv_file.stem] = {
            'missing_values': int(df.isnull().sum().sum()),
            'duplicates': int(df.duplicated().sum()),
            'columns': list(df.columns)
        }
    except Exception as e:
        print('  ERROR loading:', str(e))

# Fetch NAVs
primary_schemes = {
    '125497': 'HDFC_Top_100_Direct',
    '119551': 'SBI_Bluechip',
    '120503': 'ICICI_Bluechip',
    '118632': 'Nippon_Large_Cap',
    '119092': 'Axis_Bluechip',
    '120841': 'Kotak_Bluechip'
}

nav_combined = []
for code, name in primary_schemes.items():
    url = f'https://api.mfapi.in/mf/{code}'
    print(f'Fetching {name} ({code}) from {url}...')
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if 'data' in data:
            nav_df = pd.DataFrame(data['data'])
            nav_df['scheme_code'] = code
            nav_df['scheme_name'] = name
            nav_df['fetched_at'] = datetime.now().isoformat()
            nav_df['date'] = pd.to_datetime(nav_df['date'], format='%d-%m-%Y', errors='coerce')
            nav_df['nav'] = pd.to_numeric(nav_df['nav'], errors='coerce')
            out_file = DATA_RAW_DIR / f'nav_{code}_{name}.csv'
            nav_df.to_csv(out_file, index=False)
            print(f'  Saved {len(nav_df)} rows to {out_file.name}')
            nav_combined.append(nav_df)
        else:
            print('  No data field in response')
    except Exception as e:
        print('  ERROR fetching:', str(e))

if nav_combined:
    combined = pd.concat(nav_combined, ignore_index=True)
    combined_file = DATA_RAW_DIR / f"nav_combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    combined.to_csv(combined_file, index=False)
    print('Combined NAV saved to', combined_file.name)
else:
    print('No NAV data fetched')

# Explore fund_master
if 'fund_master' in datasets:
    fm = datasets['fund_master']
    print('\nFund Master shape:', fm.shape)
    # Candidate column names (case sensitive as in provided CSVs)
    candidates = ['Fund House', 'fund_house', 'Category', 'category', 'Sub-Category', 'sub_category', 'Risk Grade', 'risk_grade']
    for col in candidates:
        if col in fm.columns:
            print(f"\nColumn: {col} - unique: {fm[col].nunique()}")
            print(fm[col].value_counts().head(5).to_string())
    # code column detection
    code_col = None
    for col in fm.columns:
        if 'code' in col.lower():
            code_col = col
            break
    print('\nDetected code column:', code_col)
else:
    print('\nfund_master not loaded')

# Validate AMFI codes
report = {'timestamp': datetime.now().isoformat(), 'validations': {}}
if 'fund_master' in datasets and 'nav_history' in datasets:
    fm = datasets['fund_master']
    nh = datasets['nav_history']
    fm_code_col = next((c for c in fm.columns if 'code' in c.lower()), None)
    nh_code_col = next((c for c in nh.columns if 'code' in c.lower()), None)
    if fm_code_col and nh_code_col:
        fm_codes = set(fm[fm_code_col].dropna().astype(str).unique())
        nh_codes = set(nh[nh_code_col].dropna().astype(str).unique())
        matching = fm_codes & nh_codes
        report['validations']['amfi'] = {
            'fm_codes': len(fm_codes),
            'nh_codes': len(nh_codes),
            'matching': len(matching),
            'match_pct': round(len(matching)/len(fm_codes)*100,2) if fm_codes else 0,
            'orphan_fm': list(sorted(fm_codes - nh_codes))[:5],
            'orphan_nh': list(sorted(nh_codes - fm_codes))[:5]
        }
        # save report
        report_file = REPORTS_DIR / f"data_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file,'w') as f:
            json.dump(report, f, indent=2)
        print('Report saved to', report_file.name)
    else:
        print('Could not find code columns in one of the datasets')
else:
    print('Skipping AMFI validation - fund_master or nav_history missing')

print('\nDone')
