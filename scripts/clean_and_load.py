from pathlib import Path
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "capstone_project" / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
DB_PATH = ROOT / "bluestock_mf.db"

NAV_FILE = "02_nav_history.csv"
TX_FILE = "08_investor_transactions.csv"
PERF_FILE = "07_scheme_performance.csv"
FUND_MASTER_FILE = "01_fund_master.csv"
AUM_FILE = "03_aum_by_fund_house.csv"

TRANSACTION_TYPE_MAP = {
    "sip": "SIP",
    "lumpsum": "Lumpsum",
    "lump sum": "Lumpsum",
    "redemption": "Redemption",
    "redeem": "Redemption"
}
VALID_KYC = {"Verified", "Pending"}


def ensure_dirs():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def parse_date_series(series):
    return pd.to_datetime(series, errors="coerce", utc=False)


def parse_month_series(series):
    months = series.astype(str).str.strip()
    parsed = pd.to_datetime(months + "-01", format="%Y-%m-%d", errors="coerce")
    parsed = parsed.fillna(pd.to_datetime(months, errors="coerce"))
    return parsed


def normalize_string_columns(df):
    for col in df.select_dtypes(include=["string", "object"]).columns:
        df[col] = df[col].astype(str).str.strip()
    return df


def clean_nav_history():
    df = pd.read_csv(RAW_DIR / NAV_FILE)
    df = normalize_string_columns(df)
    df["date"] = parse_date_series(df["date"])
    df = df.dropna(subset=["amfi_code", "date", "nav"])
    df = df[df["nav"] > 0]
    df = df.drop_duplicates(subset=["amfi_code", "date"], keep="last")
    df = df.sort_values(["amfi_code", "date"]).reset_index(drop=True)

    completed = []
    for amfi_code, group in df.groupby("amfi_code", sort=False):
        calendar = pd.date_range(start=group["date"].min(), end=group["date"].max(), freq="D")
        calendar_df = group.set_index("date").reindex(calendar)
        calendar_df["amfi_code"] = amfi_code
        calendar_df["nav"] = calendar_df["nav"].ffill()
        calendar_df = calendar_df.reset_index().rename(columns={"index": "date"})
        completed.append(calendar_df[["amfi_code", "date", "nav"]])

    result = pd.concat(completed, ignore_index=True)
    result = result.dropna(subset=["nav"]).sort_values(["amfi_code", "date"]).reset_index(drop=True)
    return result


def clean_transactions():
    df = pd.read_csv(RAW_DIR / TX_FILE)
    df = normalize_string_columns(df)
    df["transaction_date"] = parse_date_series(df["transaction_date"])
    df = df.dropna(subset=["transaction_date", "amfi_code", "transaction_type", "amount_inr"])

    df["transaction_type"] = (
        df["transaction_type"].astype(str)
        .str.strip()
        .str.lower()
        .replace(TRANSACTION_TYPE_MAP)
    )
    df["transaction_type"] = (
        df["transaction_type"].where(df["transaction_type"].isin(TRANSACTION_TYPE_MAP.values()))
        .fillna(df["transaction_type"].astype(str).str.title())
    )

    df = df[df["transaction_type"].isin(["SIP", "Lumpsum", "Redemption"])]
    df = df[pd.to_numeric(df["amount_inr"], errors="coerce") > 0].copy()
    df["kyc_status"] = df["kyc_status"].astype(str).str.title()
    df["kyc_status"] = df["kyc_status"].where(df["kyc_status"].isin(VALID_KYC), "Unknown")
    df = df.sort_values(["transaction_date", "amfi_code", "investor_id"]).reset_index(drop=True)
    return df


def clean_scheme_performance():
    df = pd.read_csv(RAW_DIR / PERF_FILE)
    df = normalize_string_columns(df)
    numeric_cols = [
        "return_1yr_pct",
        "return_3yr_pct",
        "return_5yr_pct",
        "benchmark_3yr_pct",
        "alpha",
        "beta",
        "sharpe_ratio",
        "sortino_ratio",
        "std_dev_ann_pct",
        "max_drawdown_pct",
        "aum_crore",
        "expense_ratio_pct",
        "morningstar_rating"
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    expense_flag = (df["expense_ratio_pct"] < 0.1) | (df["expense_ratio_pct"] > 2.5)
    numeric_missing = df[numeric_cols].isna().any(axis=1)
    df["anomaly_flag"] = (expense_flag | numeric_missing).astype(bool)
    return df


def clean_fund_master():
    df = pd.read_csv(RAW_DIR / FUND_MASTER_FILE)
    df = normalize_string_columns(df)
    df["launch_date"] = parse_date_series(df["launch_date"])
    df["expense_ratio_pct"] = pd.to_numeric(df["expense_ratio_pct"], errors="coerce")
    df["exit_load_pct"] = pd.to_numeric(df["exit_load_pct"], errors="coerce")
    df["min_sip_amount"] = pd.to_numeric(df["min_sip_amount"], errors="coerce")
    df["min_lumpsum_amount"] = pd.to_numeric(df["min_lumpsum_amount"], errors="coerce")
    return df


def clean_aum_by_fund_house():
    df = pd.read_csv(RAW_DIR / AUM_FILE)
    df = normalize_string_columns(df)
    df["date"] = parse_date_series(df["date"])
    df["aum_lakh_crore"] = pd.to_numeric(df["aum_lakh_crore"], errors="coerce")
    df["aum_crore"] = pd.to_numeric(df["aum_crore"], errors="coerce")
    df["num_schemes"] = pd.to_numeric(df["num_schemes"], errors="coerce", downcast="integer")
    return df


def clean_monthly_sip_inflows():
    path = RAW_DIR / "04_monthly_sip_inflows.csv"
    df = pd.read_csv(path)
    df = normalize_string_columns(df)
    df["month"] = parse_month_series(df["month"])
    df["sip_inflow_crore"] = pd.to_numeric(df["sip_inflow_crore"], errors="coerce")
    df["active_sip_accounts_crore"] = pd.to_numeric(df["active_sip_accounts_crore"], errors="coerce")
    df["new_sip_accounts_lakh"] = pd.to_numeric(df["new_sip_accounts_lakh"], errors="coerce")
    df["sip_aum_lakh_crore"] = pd.to_numeric(df["sip_aum_lakh_crore"], errors="coerce")
    df["yoy_growth_pct"] = pd.to_numeric(df["yoy_growth_pct"], errors="coerce")
    return df


def clean_category_inflows():
    path = RAW_DIR / "05_category_inflows.csv"
    df = pd.read_csv(path)
    df = normalize_string_columns(df)
    df["month"] = parse_month_series(df["month"])
    df["net_inflow_crore"] = pd.to_numeric(df["net_inflow_crore"], errors="coerce")
    return df


def clean_industry_folio_count():
    path = RAW_DIR / "06_industry_folio_count.csv"
    df = pd.read_csv(path)
    df = normalize_string_columns(df)
    df["month"] = parse_month_series(df["month"])
    for col in ["total_folios_crore", "equity_folios_crore", "debt_folios_crore", "hybrid_folios_crore", "others_folios_crore"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def clean_portfolio_holdings():
    path = RAW_DIR / "09_portfolio_holdings.csv"
    df = pd.read_csv(path)
    df = normalize_string_columns(df)
    df["portfolio_date"] = parse_date_series(df["portfolio_date"])
    df["weight_pct"] = pd.to_numeric(df["weight_pct"], errors="coerce")
    df["market_value_cr"] = pd.to_numeric(df["market_value_cr"], errors="coerce")
    df["current_price_inr"] = pd.to_numeric(df["current_price_inr"], errors="coerce")
    return df


def clean_benchmark_indices():
    path = RAW_DIR / "10_benchmark_indices.csv"
    df = pd.read_csv(path)
    df = normalize_string_columns(df)
    df["date"] = parse_date_series(df["date"])
    df["close_value"] = pd.to_numeric(df["close_value"], errors="coerce")
    return df


def serialize_date_columns(df):
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            if col == "month":
                df[col] = df[col].dt.strftime("%Y-%m")
            else:
                df[col] = df[col].dt.strftime("%Y-%m-%d")
    return df


def write_cleaned_csv(df, filename):
    df_copy = serialize_date_columns(df.copy())
    path = PROCESSED_DIR / filename
    df_copy.to_csv(path, index=False)
    return len(df_copy)


def load_cleaned_tables(engine, cleaned_files):
    counts = {}
    for filename in cleaned_files:
        table_name = Path(filename).stem
        path = PROCESSED_DIR / filename
        df = pd.read_csv(path)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        if "transaction_date" in df.columns:
            df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
        if "launch_date" in df.columns:
            df["launch_date"] = pd.to_datetime(df["launch_date"], errors="coerce")
        if "portfolio_date" in df.columns:
            df["portfolio_date"] = pd.to_datetime(df["portfolio_date"], errors="coerce")
        if "month" in df.columns:
            try:
                df["month"] = pd.to_datetime(df["month"].astype(str).str.strip() + "-01", errors="coerce").dt.strftime("%Y-%m")
            except Exception:
                pass
        df.to_sql(table_name, engine, if_exists="replace", index=False)
        counts[table_name] = len(df)
    return counts


def build_date_dim(engine):
    query = "SELECT date FROM ("
    query += " UNION ALL ".join([
        "SELECT date FROM 01_fund_master WHERE 0=1"  # placeholder; we will use actual union below
    ])
    # Instead of SQL union on an unknown dataset list, build date dim in pandas.
    date_values = set()
    for table in ["02_nav_history", "03_aum_by_fund_house", "10_benchmark_indices", "09_portfolio_holdings"]:
        df = pd.read_sql(f"SELECT * FROM '{table}'", engine)
        for col in df.columns:
            if col.endswith("date") or col == "date":
                date_values.update(pd.to_datetime(df[col], errors="coerce").dropna().dt.date.astype(str).tolist())
            elif col == "month":
                date_values.update(pd.to_datetime(df[col].astype(str).str.strip() + "-01", errors="coerce").dropna().dt.date.astype(str).tolist())
    date_index = pd.to_datetime(sorted(date_values))
    df_date = pd.DataFrame({"date": date_index})
    df_date["year"] = df_date["date"].dt.year
    df_date["quarter"] = df_date["date"].dt.quarter
    df_date["month"] = df_date["date"].dt.month
    df_date["day"] = df_date["date"].dt.day
    df_date["weekday"] = df_date["date"].dt.day_name()
    df_date["is_weekend"] = df_date["date"].dt.weekday >= 5
    df_date["year_month"] = df_date["date"].dt.strftime("%Y-%m")
    df_date.to_sql("dim_date", engine, if_exists="replace", index=False)
    return len(df_date)


def build_dim_fund(engine):
    df = pd.read_sql("SELECT * FROM '01_fund_master'", engine)
    if "launch_date" in df.columns:
        df["launch_date"] = pd.to_datetime(df["launch_date"], errors="coerce")
    df = df.rename(columns={
        "sebi_category_code": "sebi_code"
    })
    df.to_sql("dim_fund", engine, if_exists="replace", index=False)
    return len(df)


def build_star_tables(engine):
    nav_df = pd.read_sql("SELECT * FROM '02_nav_history'", engine, parse_dates=["date"])
    nav_df = nav_df.sort_values(["amfi_code", "date"]).reset_index(drop=True)
    nav_df.insert(0, "nav_id", nav_df.index + 1)
    nav_df.to_sql("fact_nav", engine, if_exists="replace", index=False)

    tx_df = pd.read_sql("SELECT * FROM '08_investor_transactions'", engine, parse_dates=["transaction_date"])
    tx_df = tx_df.sort_values(["transaction_date", "amfi_code", "investor_id"]).reset_index(drop=True)
    tx_df.insert(0, "transaction_id", tx_df.index + 1)
    tx_df.to_sql("fact_transactions", engine, if_exists="replace", index=False)

    perf_df = pd.read_sql("SELECT * FROM '07_scheme_performance'", engine)
    perf_df.insert(0, "performance_id", perf_df.index + 1)
    perf_df.to_sql("fact_performance", engine, if_exists="replace", index=False)

    aum_df = pd.read_sql("SELECT * FROM '03_aum_by_fund_house'", engine, parse_dates=["date"])
    aum_df = aum_df.sort_values(["date", "fund_house"]).reset_index(drop=True)
    aum_df.insert(0, "aum_id", aum_df.index + 1)
    aum_df.to_sql("fact_aum", engine, if_exists="replace", index=False)
    return {
        "fact_nav": len(nav_df),
        "fact_transactions": len(tx_df),
        "fact_performance": len(perf_df),
        "fact_aum": len(aum_df)
    }


from sqlalchemy import text

def verify_counts(engine, expected_counts):
    verified = {}
    with engine.connect() as conn:
        for table, expected in expected_counts.items():
            result = conn.execute(text(f"SELECT COUNT(*) FROM '{table}'"))
            actual = result.scalar()
            verified[table] = {"expected": expected, "actual": actual, "match": actual == expected}
    return verified


def main():
    ensure_dirs()
    cleaned_counts = {}

    cleaned_counts["01_fund_master"] = write_cleaned_csv(clean_fund_master(), "01_fund_master.csv")
    cleaned_counts["02_nav_history"] = write_cleaned_csv(clean_nav_history(), "02_nav_history.csv")
    cleaned_counts["03_aum_by_fund_house"] = write_cleaned_csv(clean_aum_by_fund_house(), "03_aum_by_fund_house.csv")
    cleaned_counts["04_monthly_sip_inflows"] = write_cleaned_csv(clean_monthly_sip_inflows(), "04_monthly_sip_inflows.csv")
    cleaned_counts["05_category_inflows"] = write_cleaned_csv(clean_category_inflows(), "05_category_inflows.csv")
    cleaned_counts["06_industry_folio_count"] = write_cleaned_csv(clean_industry_folio_count(), "06_industry_folio_count.csv")
    cleaned_counts["07_scheme_performance"] = write_cleaned_csv(clean_scheme_performance(), "07_scheme_performance.csv")
    cleaned_counts["08_investor_transactions"] = write_cleaned_csv(clean_transactions(), "08_investor_transactions.csv")
    cleaned_counts["09_portfolio_holdings"] = write_cleaned_csv(clean_portfolio_holdings(), "09_portfolio_holdings.csv")
    cleaned_counts["10_benchmark_indices"] = write_cleaned_csv(clean_benchmark_indices(), "10_benchmark_indices.csv")

    print("Cleaned files and row counts:")
    for table, count in cleaned_counts.items():
        print(f"  {table}: {count}")

    engine = create_engine(f"sqlite:///{DB_PATH}")
    cleaned_table_counts = load_cleaned_tables(engine, [f"{name}.csv" for name in [
        "01_fund_master", "02_nav_history", "03_aum_by_fund_house", "04_monthly_sip_inflows",
        "05_category_inflows", "06_industry_folio_count", "07_scheme_performance",
        "08_investor_transactions", "09_portfolio_holdings", "10_benchmark_indices"
    ]])
    print("Loaded cleaned tables into SQLite:")
    for table, count in cleaned_table_counts.items():
        print(f"  {table}: {count}")

    dim_date_count = build_date_dim(engine)
    dim_fund_count = build_dim_fund(engine)
    star_counts = build_star_tables(engine)
    print(f"Built dim_date: {dim_date_count}")
    print(f"Built dim_fund: {dim_fund_count}")
    for table, count in star_counts.items():
        print(f"Built {table}: {count}")

    star_expected = {**cleaned_table_counts, **{"dim_date": dim_date_count, "dim_fund": dim_fund_count, **star_counts}}
    verification = verify_counts(engine, star_expected)
    print("Verification results:")
    for table, detail in verification.items():
        print(f"  {table}: expected={detail['expected']} actual={detail['actual']} match={detail['match']}")

    engine.dispose()
    print(f"Database created at {DB_PATH}")


if __name__ == "__main__":
    main()
