import os
import pandas as pd
import numpy as np
from scipy.stats import linregress
import matplotlib.pyplot as plt

# Config
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(ROOT, 'data', 'processed')
NAV_FILE = os.path.join(DATA_DIR, '02_nav_history.csv')
MASTER_FILE = os.path.join(DATA_DIR, '01_fund_master.csv')
BENCH_FILE = os.path.join(DATA_DIR, '10_benchmark_indices.csv')
OUT_DIR = os.path.join(ROOT, 'reports')
FIG_DIR = os.path.join(OUT_DIR, 'figures')
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

Rf_annual = 0.065
trading_days = 252

print('Loading data...')
nav = pd.read_csv(NAV_FILE, parse_dates=['date'])
master = pd.read_csv(MASTER_FILE, parse_dates=['launch_date'], dayfirst=False)
bench = pd.read_csv(BENCH_FILE, parse_dates=['date'])

# Prepare benchmark series: pivot by index_name
bench_pivot = bench.pivot(index='date', columns='index_name', values='close_value').sort_index()

# Prepare NAV: ensure sorted
nav = nav.sort_values(['amfi_code', 'date'])

# Compute daily returns per fund
nav['daily_return'] = nav.groupby('amfi_code')['nav'].pct_change()

# Save a quick distribution check (overall)
plt.figure(figsize=(8,4))
nav['daily_return'].dropna().hist(bins=200)
plt.title('Daily return distribution (all funds)')
plt.xlabel('Daily return')
plt.savefig(os.path.join(FIG_DIR, 'daily_return_distribution_all_funds.png'), dpi=150)
plt.close()

# Get list of funds to analyze (intersection with master)
funds = nav['amfi_code'].unique()
N = len(funds)
print(f'Found {N} funds in NAV data')

# Build a dataframe to hold metrics
rows = []

# Helper to get CAGR
def compute_cagr(series, years):
    # series: pd.Series indexed by date with nav
    if series.empty:
        return np.nan
    end_date = series.index.max()
    start_date = end_date - pd.DateOffset(years=years)
    # take first observation on or after start_date
    start_idx = series.index.searchsorted(start_date)
    if start_idx >= len(series):
        # not enough history
        return np.nan
    start_val = series.iloc[start_idx]
    end_val = series.iloc[-1]
    if start_val <= 0:
        return np.nan
    return (end_val / start_val) ** (1.0 / years) - 1

# Precompute benchmark daily returns (NIFTY100 and NIFTY50)
bench_returns = bench_pivot.pct_change()

for code in funds:
    df = nav[nav['amfi_code'] == code].set_index('date').sort_index()
    r = df['daily_return'].dropna()
    if r.empty:
        continue
    mean_daily = r.mean()
    std_daily = r.std()
    # excess mean daily
    excess_daily = mean_daily - Rf_annual / trading_days
    sharpe = (excess_daily / std_daily) * np.sqrt(trading_days) if std_daily>0 else np.nan
    # Sortino
    neg = r[r < 0]
    if len(neg) > 0:
        downside_std = neg.std()
        sortino = (excess_daily / downside_std) * np.sqrt(trading_days) if downside_std>0 else np.nan
    else:
        sortino = np.nan
    # CAGR
    nav_series = df['nav']
    cagr_1 = compute_cagr(nav_series, 1)
    cagr_3 = compute_cagr(nav_series, 3)
    cagr_5 = compute_cagr(nav_series, 5)
    # Alpha/Beta vs NIFTY100
    # align dates with bench_returns
    bench_col = None
    for candidate in ['NIFTY100', 'NIFTY 100', 'NIFTY_100', 'NIFTY100 TRI', 'NIFTY 100 TRI']:
        if candidate in bench_returns.columns:
            bench_col = candidate
            break
    if bench_col is None and 'NIFTY100' in bench_pivot.columns:
        bench_col = 'NIFTY100'
    if bench_col is None:
        # fallback to NIFTY50
        bench_col = 'NIFTY50' if 'NIFTY50' in bench_returns.columns else bench_returns.columns[0]

    merged = pd.DataFrame({'fund': r, 'bench': bench_returns[bench_col]}).dropna()
    if len(merged) >= 30:
        lr = linregress(merged['bench'].values, merged['fund'].values)
        beta = lr.slope
        alpha_annual = lr.intercept * trading_days
    else:
        beta = np.nan
        alpha_annual = np.nan

    # Max drawdown and date range
    running_max = nav_series.cummax()
    drawdown = nav_series / running_max - 1
    mdd = drawdown.min()
    if not np.isnan(mdd):
        trough_date = drawdown.idxmin()
        # peak before trough
        peak_date = nav_series[:trough_date].idxmax()
    else:
        trough_date = None
        peak_date = None

    # Tracking error vs NIFTY100 over last 3 years
    end_date = nav_series.index.max()
    start_3y = end_date - pd.DateOffset(years=3)
    fund_ret_3y = r[r.index >= start_3y]
    bench_ret_3y = bench_returns[bench_col][bench_returns[bench_col].index >= start_3y]
    te = np.nan
    if not fund_ret_3y.empty and not bench_ret_3y.empty:
        merged3 = pd.DataFrame({'fund': fund_ret_3y, 'bench': bench_ret_3y}).dropna()
        if len(merged3) > 10:
            te = merged3['fund'].sub(merged3['bench']).std() * np.sqrt(trading_days)

    # expense ratio
    exp_row = master[master['amfi_code'] == code]
    expense = exp_row['expense_ratio_pct'].iloc[0] if not exp_row.empty else np.nan
    scheme_name = exp_row['scheme_name'].iloc[0] if not exp_row.empty else str(code)

    rows.append({
        'amfi_code': code,
        'scheme_name': scheme_name,
        'cagr_1yr': cagr_1,
        'cagr_3yr': cagr_3,
        'cagr_5yr': cagr_5,
        'sharpe': sharpe,
        'sortino': sortino,
        'alpha_annual': alpha_annual,
        'beta': beta,
        'max_drawdown': mdd,
        'drawdown_trough_date': trough_date,
        'drawdown_peak_date': peak_date,
        'expense_ratio_pct': expense,
        'tracking_error_3yr': te
    })

metrics = pd.DataFrame(rows).set_index('amfi_code')

# Ranks for scorecard
metrics['rank_cagr_3yr'] = metrics['cagr_3yr'].rank(ascending=False, method='min')
metrics['rank_sharpe'] = metrics['sharpe'].rank(ascending=False, method='min')
metrics['rank_alpha'] = metrics['alpha_annual'].rank(ascending=False, method='min')
# expense: lower is better -> inverse rank
metrics['rank_expense_inv'] = metrics['expense_ratio_pct'].rank(ascending=True, method='min')
# max drawdown: less negative is better -> inverse rank
metrics['rank_mdd_inv'] = metrics['max_drawdown'].rank(ascending=False, method='min')

# Convert ranks to percentiles (0-100)
M = len(metrics)
if M > 1:
    metrics['score_cagr_3yr'] = (M - metrics['rank_cagr_3yr']) / (M - 1) * 100
    metrics['score_sharpe'] = (M - metrics['rank_sharpe']) / (M - 1) * 100
    metrics['score_alpha'] = (M - metrics['rank_alpha']) / (M - 1) * 100
    metrics['score_expense'] = (M - metrics['rank_expense_inv']) / (M - 1) * 100
    metrics['score_mdd'] = (M - metrics['rank_mdd_inv']) / (M - 1) * 100
else:
    metrics['score_cagr_3yr'] = 0
    metrics['score_sharpe'] = 0
    metrics['score_alpha'] = 0
    metrics['score_expense'] = 0
    metrics['score_mdd'] = 0

# Composite score
metrics['fund_score_0_100'] = (
    0.30 * metrics['score_cagr_3yr'] +
    0.25 * metrics['score_sharpe'] +
    0.20 * metrics['score_alpha'] +
    0.15 * metrics['score_expense'] +
    0.10 * metrics['score_mdd']
)

# Rank funds by fund_score
metrics['final_rank'] = metrics['fund_score_0_100'].rank(ascending=False, method='min')

# Save outputs
metrics.to_csv(os.path.join(OUT_DIR, 'fund_metrics.csv'))
metrics.sort_values('final_rank').to_csv(os.path.join(OUT_DIR, 'fund_scorecard.csv'))
print('Saved metrics to reports/')

# Benchmark comparison chart: top 5 funds vs NIFTY50 and NIFTY100 over 3 years
top5 = metrics.sort_values('final_rank').head(5).index.astype(int).tolist()
end = nav['date'].max()
start = end - pd.DateOffset(years=3)

plt.figure(figsize=(12,6))
# plot benchmarks
if 'NIFTY50' in bench_pivot.columns:
    series = bench_pivot['NIFTY50']
    series = series[(series.index >= start) & (series.index <= end)]
    if not series.empty:
        series = series / series.iloc[0]
        plt.plot(series.index, series.values, label='NIFTY50')
if 'NIFTY100' in bench_pivot.columns:
    series = bench_pivot['NIFTY100']
    series = series[(series.index >= start) & (series.index <= end)]
    if not series.empty:
        series = series / series.iloc[0]
        plt.plot(series.index, series.values, label='NIFTY100')

for code in top5:
    df = nav[nav['amfi_code'] == code].set_index('date').sort_index()
    s = df['nav'][(df.index >= start) & (df.index <= end)]
    if s.empty:
        continue
    s = s / s.iloc[0]
    name = master[master['amfi_code'] == code]['scheme_name'].iloc[0] if not master[master['amfi_code'] == code].empty else str(code)
    plt.plot(s.index, s.values, label=name)

plt.legend(loc='best')
plt.title('Top 5 funds vs NIFTY50 / NIFTY100 (3Y normalized)')
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'top5_vs_bench_3y.png'), dpi=150)
plt.close()

# Save top5 tracking error vs NIFTY100
te_rows = []
for code in top5:
    code = int(code)
    df = nav[nav['amfi_code'] == code].set_index('date').sort_index()
    r = df['nav'].pct_change()
    bench_r = bench_returns['NIFTY100'] if 'NIFTY100' in bench_returns.columns else bench_returns.iloc[:,0]
    merged = pd.DataFrame({'fund': r, 'bench': bench_r}).dropna()
    merged = merged[merged.index >= (merged.index.max() - pd.DateOffset(years=3))]
    if len(merged) > 10:
        tracking_err = merged['fund'].sub(merged['bench']).std() * np.sqrt(trading_days)
    else:
        tracking_err = np.nan
    te_rows.append({'amfi_code': code, 'tracking_error_3yr': tracking_err})

pd.DataFrame(te_rows).to_csv(os.path.join(OUT_DIR, 'top5_tracking_errors.csv'), index=False)

print('Done.')
