import csv
import os
import re
import requests
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(ROOT, "data", "processed")
RAW_DIR = os.path.join(ROOT, "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

print("Project root:", ROOT)
print("Processed data directory:", PROCESSED_DIR)
print("Raw data directory:", RAW_DIR)
print()

csv_files = sorted([f for f in os.listdir(PROCESSED_DIR) if f.lower().endswith('.csv')])
print(f"Found {len(csv_files)} CSV files in data/processed")
print()

loaded = {}
for csv_file in csv_files:
    path = os.path.join(PROCESSED_DIR, csv_file)
    df = pd.read_csv(path)
    loaded[csv_file] = df
    print(f"=== {csv_file} ===")
    print("shape:", df.shape)
    print("dtypes:")
    print(df.dtypes)
    print("head:")
    print(df.head(5).to_string(index=False))
    missing = df.isna().sum()
    if missing.any():
        print("missing values (>0):")
        print(missing[missing > 0].to_string())
    else:
        print("missing values: none")
    dup = df.duplicated().sum()
    print("duplicate rows:", dup)
    print()

# Exploratory metadata for fund master
fund_master_name = "01_fund_master.csv"
nav_history_name = "02_nav_history.csv"
print("===== Fund master summary =====")
if fund_master_name in loaded:
    fm = loaded[fund_master_name]
    candidate_columns = [c for c in fm.columns if re.search(r'code|scheme|amfi|sc', c, flags=re.I)]
    print("candidate code-related columns:", candidate_columns)
    for col in [c for c in fm.columns if c.lower() in ['fund_house', 'fund house', 'fund_house_name', 'fund_house_name', 'house_name', 'fundhouse']]:
        if col in fm.columns:
            print(f"Unique fund houses ({col}):", fm[col].nunique())
            print(fm[col].dropna().unique()[:20])
    for col in [c for c in fm.columns if re.search(r'category|sub[-_ ]category|risk', c, flags=re.I)]:
        if col in fm.columns:
            print(f"Unique values for {col}: {fm[col].nunique()}")
            print(fm[col].dropna().unique()[:20])
    print()
else:
    print("Fund master CSV not loaded")

print("===== NAV history summary =====")
if nav_history_name in loaded:
    nh = loaded[nav_history_name]
    print("NAV history columns:", list(nh.columns)[:10])
    print("Unique columns count:", len(nh.columns))
    print()
else:
    print("NAV history CSV not loaded")

# Determine AMFI scheme code fields
def detect_code_column(df, name):
    candidates = [c for c in df.columns if re.search(r'amfi|scheme.*code|sch.*code|code', c, flags=re.I)]
    print(f"{name} code candidates:", candidates)
    return candidates

fund_master_codes = []
nav_history_codes = []
if fund_master_name in loaded:
    fm_candidates = detect_code_column(loaded[fund_master_name], "Fund master")
    if fm_candidates:
        fm_code_col = fm_candidates[0]
        fund_master_codes = loaded[fund_master_name][fm_code_col].dropna().astype(str).str.strip()
        print("Sample fund master codes:", fund_master_codes.head(10).tolist())
        if fund_master_codes.str.match(r'^\d+$').all():
            print("Fund master codes are numeric strings")
    print()
if nav_history_name in loaded:
    nh_candidates = detect_code_column(loaded[nav_history_name], "NAV history")
    if nh_candidates:
        nh_code_col = nh_candidates[0]
        nav_history_codes = loaded[nav_history_name][nh_code_col].dropna().astype(str).str.strip()
        print("Sample nav history codes:", nav_history_codes.head(10).tolist())
        if nav_history_codes.str.match(r'^\d+$').all():
            print("NAV history codes are numeric strings")
    print()

if fund_master_codes is not None and nav_history_codes is not None and len(fund_master_codes) and len(nav_history_codes):
    fund_master_set = set(fund_master_codes.unique())
    nav_history_set = set(nav_history_codes.unique())
    missing_in_nav = sorted(fund_master_set - nav_history_set)
    missing_in_fm = sorted(nav_history_set - fund_master_set)
    print("Fund master codes total:", len(fund_master_set))
    print("NAV history codes total:", len(nav_history_set))
    print("Codes in fund master but missing from nav history:", len(missing_in_nav))
    print("Codes in nav history but missing from fund master:", len(missing_in_fm))
    if missing_in_nav:
        print("First missing fund master codes:", missing_in_nav[:20])
    if missing_in_fm:
        print("First codes in nav history not in fund master:", missing_in_fm[:20])
    print()

# Fetch live NAVs for requested schemes and save raw CSVs
scheme_list = [
    ("HDFC Top 100 Direct", 125497),
    ("SBI Bluechip", 119551),
    ("ICICI Bluechip", 120503),
    ("Nippon Large Cap", 118632),
    ("Axis Bluechip", 119092),
    ("Kotak Bluechip", 120841),
]
combined_rows = []
for scheme_name, scheme_code in scheme_list:
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    print(f"Fetching {scheme_name} ({scheme_code}) from {url}")
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    payload = resp.json()
    if "data" not in payload or "meta" not in payload:
        raise ValueError(f"Unexpected JSON structure for {scheme_code}")
    meta = payload["meta"]
    data_items = payload["data"]
    if not isinstance(data_items, list) or len(data_items) == 0:
        raise ValueError(f"No NAV history found for {scheme_code}")
    fieldnames = ["scheme_name", "scheme_code"] + sorted(meta.keys()) + sorted({k for item in data_items for k in item.keys()})
    raw_name = f"raw_nav_{scheme_code}_{scheme_name.lower().replace(' ', '_').replace('/', '_')}.csv"
    raw_path = os.path.join(RAW_DIR, raw_name)
    print("Saving raw NAV CSV to", raw_path)
    with open(raw_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for item in data_items:
            row = {**{k: meta.get(k, None) for k in meta}, **item}
            row["scheme_name"] = scheme_name
            row["scheme_code"] = scheme_code
            writer.writerow(row)
            combined_rows.append(row)

combined_path = os.path.join(RAW_DIR, "fetched_nav_history.csv")
print("Saving combined NAV fetch file to", combined_path)
if combined_rows:
    all_fields = sorted({k for row in combined_rows for k in row.keys()})
    with open(combined_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=all_fields)
        writer.writeheader()
        writer.writerows(combined_rows)
    print("Combined file rows:", len(combined_rows))

print("\nData quality summary:")
if 'fund_master' in locals() and 'nav_history' in locals():
    print("AMFI scheme code lookup completed.")
    if missing_in_nav:
        print(f"Warning: {len(missing_in_nav)} AMFI scheme codes appear in fund_master but not in nav_history.")
    else:
        print("All fund_master AMFI scheme codes exist in nav_history.")
else:
    print("Could not validate AMFI codes because fund_master or nav_history was not loaded.")

print("Script execution complete.")
