import json
import os
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

SCHEMES = {
    "HDFC Top 100 Direct": "125497",
    "SBI Bluechip": "119551",
    "ICICI Bluechip": "120503",
    "Nippon Large Cap": "118632",
    "Axis Bluechip": "119092",
    "Kotak Bluechip": "120841",
}

BASE_DATASETS = [
    "01_fund_master.csv",
    "02_nav_history.csv",
    "03_aum_by_fund_house.csv",
    "04_monthly_sip_inflows.csv",
    "05_category_inflows.csv",
    "06_industry_folio_count.csv",
    "07_scheme_performance.csv",
    "08_investor_transactions.csv",
    "09_portfolio_holdings.csv",
    "10_benchmark_indices.csv",
]

summary_lines = []

print("\n=== Data Load Summary ===\n")
loaded = {}
for filename in BASE_DATASETS:
    path = RAW_DIR / filename
    if not path.exists():
        print(f"MISSING: {path}")
        summary_lines.append(f"MISSING: {path}")
        continue

    df = pd.read_csv(path)
    loaded[filename] = df

    print(f"Dataset: {filename}")
    print(f"  Path: {path}")
    print(f"  Shape: {df.shape}")
    print("  Dtypes:")
    print(df.dtypes.to_string())
    print("  Head:")
    print(df.head().to_string(index=False))
    print("\n")

    summary_lines.append(f"Dataset {filename}: shape={df.shape}")
    missing_counts = df.isna().sum()
    missing_report = ", ".join(
        [f"{col}={cnt}" for col, cnt in missing_counts.items() if cnt > 0]
    )
    if missing_report:
        summary_lines.append(f"  Missing values: {missing_report}")
    else:
        summary_lines.append("  Missing values: none")


# Fetch live NAVs from mfapi.in and save raw CSVs
print("\n=== Fetching live NAV data ===\n")
fetch_results = []
for scheme_name, scheme_code in SCHEMES.items():
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    payload = response.json()

    meta = payload.get("meta", {})
    actual_code = str(meta.get("scheme_code", scheme_code))
    actual_name = meta.get("scheme_name", scheme_name)
    if actual_code != str(scheme_code):
        print(f"Warning: requested code {scheme_code} returned actual code {actual_code}")
        summary_lines.append(f"Warning: requested {scheme_name} ({scheme_code}) returned actual code {actual_code}")

    nav_records = payload.get("data", [])
    if not isinstance(nav_records, list):
        raise ValueError(f"Unexpected data type for scheme {scheme_name}: {type(nav_records)}")

    sanitized_name = actual_name.replace(" ", "_").replace('/', '_').replace('-', '_')
    csv_path = RAW_DIR / f"nav_live_{actual_code}_{sanitized_name}.csv"
    pd.DataFrame(nav_records).to_csv(csv_path, index=False)
    print(f"Saved live NAV for {actual_name} ({actual_code}) to {csv_path}")

    fetch_results.append((scheme_name, actual_code, len(nav_records), csv_path, actual_name))

summary_lines.append("\nLive NAV fetch results:")
for scheme_name, actual_code, count, csv_path, actual_name in fetch_results:
    summary_lines.append(f"  Requested {scheme_name} ({SCHEMES[scheme_name]}) -> Actual {actual_name} ({actual_code}): {count} records -> {csv_path.name}")


# Fund master exploration
fund_master = loaded.get("01_fund_master.csv")
nav_history = loaded.get("02_nav_history.csv")
print("\n=== Fund Master Exploration ===\n")
if fund_master is not None:
    for field in ["fund_house", "category", "sub_category", "risk_category"]:
        if field in fund_master.columns:
            uniques = fund_master[field].dropna().unique()
            sample = list(uniques[:20])
            print(f"{field}: {len(uniques)} unique values")
            print(f"  Sample: {sample}")
            summary_lines.append(f"{field}: {len(uniques)} unique values")
        else:
            print(f"Field missing in fund master: {field}")
            summary_lines.append(f"Field missing: {field}")

    amfi_col = None
    possible_amfi = [c for c in fund_master.columns if "amfi" in c.lower() or "scheme" in c.lower() and "code" in c.lower()]
    if possible_amfi:
        amfi_col = possible_amfi[0]
    else:
        for c in fund_master.columns:
            if c.lower() in ["amfi code", "scheme code", "amfi_scheme_code"]:
                amfi_col = c
                break

    if amfi_col is None:
        raise KeyError("Could not identify AMFI code column in fund master")

    fund_master_amfi = fund_master[amfi_col].astype(str).str.strip()
    fund_master_amfi = fund_master_amfi[fund_master_amfi.notna() & (fund_master_amfi != "nan")]
    print(f"Identified AMFI column: {amfi_col}")
    print(f"  Unique AMFI codes: {fund_master_amfi.nunique()}")
    lengths = fund_master_amfi.str.len().value_counts().sort_index()
    print(f"  AMFI code lengths: {lengths.to_dict()}")
    prefix_summary = fund_master_amfi.str[:2].value_counts().head(10)
    print(f"  Common AMFI prefixes: {prefix_summary.to_dict()}")
    summary_lines.append(f"AMFI column: {amfi_col}")
    summary_lines.append(f"  Unique AMFI codes: {fund_master_amfi.nunique()}")
    summary_lines.append(f"  Lengths: {lengths.to_dict()}")
    summary_lines.append(f"  Prefix sample: {prefix_summary.to_dict()}")

    if nav_history is not None:
        nav_amfi_col = None
        for c in nav_history.columns:
            if "amfi" in c.lower() or "scheme" in c.lower() and "code" in c.lower():
                nav_amfi_col = c
                break
        if nav_amfi_col is None:
            raise KeyError("Could not identify AMFI code column in nav history")

        nav_history_codes = nav_history[nav_amfi_col].astype(str).str.strip().dropna().unique()
        missing_codes = sorted(set(fund_master_amfi.unique()) - set(nav_history_codes))
        total_fund_master = fund_master_amfi.nunique()
        total_missing = len(missing_codes)
        print(f"\nAMFI validation: {total_missing} missing of {total_fund_master} fund master codes")
        if total_missing:
            print("Missing sample codes:")
            print(missing_codes[:20])
        else:
            print("All AMFI codes from fund master appear in nav history.")
        summary_lines.append(f"AMFI validation: {total_missing} missing of {total_fund_master} codes")
        if total_missing:
            summary_lines.append(f"Missing sample: {missing_codes[:20]}")

    else:
        print("NAV history not loaded, skipping AMFI validation.")
        summary_lines.append("NAV history not loaded; AMFI validation skipped.")
else:
    print("Fund master not loaded; skipping fund master exploration.")
    summary_lines.append("Fund master not loaded; exploration skipped.")


# Write the data quality summary report
summary_file = REPORTS_DIR / "data_quality_summary.txt"
summary_lines.insert(0, "=== Data Quality Summary ===")
summary_lines.insert(1, "")
summary_lines.append("")
with open(summary_file, "w", encoding="utf-8") as f:
    f.write("\n".join(summary_lines))

print(f"\nSummary written to {summary_file}")
