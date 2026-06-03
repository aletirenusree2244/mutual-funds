# Data Dictionary

## Files and Sources
- `01_fund_master.csv`: Fund master metadata for each AMFI code.
- `02_nav_history.csv`: Daily NAV history for each scheme.
- `03_aum_by_fund_house.csv`: Quarterly AUM by fund house.
- `04_monthly_sip_inflows.csv`: Monthly SIP inflows and SIP account counts.
- `05_category_inflows.csv`: Monthly net inflows by category.
- `06_industry_folio_count.csv`: Monthly folio counts across product categories.
- `07_scheme_performance.csv`: Scheme performance metrics and expense ratios.
- `08_investor_transactions.csv`: Investor-level transaction activity.
- `09_portfolio_holdings.csv`: Portfolio holdings snapshot by AMFI code.
- `10_benchmark_indices.csv`: Benchmark index closing values.

## Column Definitions

### 01_fund_master.csv
- `amfi_code` (INTEGER): Unique scheme identifier.
- `fund_house` (TEXT): Asset management company name.
- `scheme_name` (TEXT): Mutual fund scheme full name.
- `category` (TEXT): High-level asset class.
- `sub_category` (TEXT): Scheme segment such as Large Cap.
- `plan` (TEXT): Plan type such as Regular or Direct.
- `launch_date` (DATE): Scheme launch date.
- `benchmark` (TEXT): Reference benchmark index.
- `expense_ratio_pct` (REAL): Scheme expense ratio percent.
- `exit_load_pct` (REAL): Exit load percent.
- `min_sip_amount` (REAL): Minimum SIP amount in INR.
- `min_lumpsum_amount` (REAL): Minimum lumpsum amount in INR.
- `fund_manager` (TEXT): Scheme fund manager.
- `risk_category` (TEXT): Risk classification.
- `sebi_category_code` (TEXT): SEBI category code.

### 02_nav_history.csv
- `amfi_code` (INTEGER): Scheme identifier.
- `date` (DATE): NAV date.
- `nav` (REAL): Net asset value.

### 03_aum_by_fund_house.csv
- `date` (DATE): Reporting date.
- `fund_house` (TEXT): Fund house name.
- `aum_lakh_crore` (REAL): AUM in lakh crores.
- `aum_crore` (REAL): AUM in crores.
- `num_schemes` (INTEGER): Number of schemes in the fund house.

### 04_monthly_sip_inflows.csv
- `month` (TEXT): Reporting month in YYYY-MM.
- `sip_inflow_crore` (REAL): SIP inflow in crores.
- `active_sip_accounts_crore` (REAL): Active SIP accounts in crores.
- `new_sip_accounts_lakh` (REAL): New SIP accounts in lakhs.
- `sip_aum_lakh_crore` (REAL): SIP AUM in lakh crores.
- `yoy_growth_pct` (REAL): Year-over-year growth percent.

### 05_category_inflows.csv
- `month` (TEXT): Reporting month in YYYY-MM.
- `category` (TEXT): Scheme category.
- `net_inflow_crore` (REAL): Net inflows in crores.

### 06_industry_folio_count.csv
- `month` (TEXT): Reporting month in YYYY-MM.
- `total_folios_crore` (REAL): Total folio count in crores.
- `equity_folios_crore` (REAL): Equity folios in crores.
- `debt_folios_crore` (REAL): Debt folios in crores.
- `hybrid_folios_crore` (REAL): Hybrid folios in crores.
- `others_folios_crore` (REAL): Other folios in crores.

### 07_scheme_performance.csv
- `amfi_code` (INTEGER): Scheme identifier.
- `scheme_name` (TEXT): Scheme name.
- `fund_house` (TEXT): Asset management company.
- `category` (TEXT): Scheme category.
- `plan` (TEXT): Plan type.
- `return_1yr_pct` (REAL): 1-year return percent.
- `return_3yr_pct` (REAL): 3-year return percent.
- `return_5yr_pct` (REAL): 5-year return percent.
- `benchmark_3yr_pct` (REAL): 3-year benchmark return percent.
- `alpha` (REAL): Alpha.
- `beta` (REAL): Beta.
- `sharpe_ratio` (REAL): Sharpe ratio.
- `sortino_ratio` (REAL): Sortino ratio.
- `std_dev_ann_pct` (REAL): Annualized standard deviation percent.
- `max_drawdown_pct` (REAL): Maximum drawdown percent.
- `aum_crore` (REAL): AUM in crores.
- `expense_ratio_pct` (REAL): Expense ratio percent.
- `morningstar_rating` (REAL): Morningstar rating.
- `risk_grade` (TEXT): Risk grading.
- `anomaly_flag` (BOOLEAN): True if numeric return values are invalid or expense ratio is outside [0.1, 2.5].

### 08_investor_transactions.csv
- `investor_id` (TEXT): Investor identifier.
- `transaction_date` (DATE): Transaction date.
- `amfi_code` (INTEGER): Scheme identifier.
- `transaction_type` (TEXT): SIP, Lumpsum, or Redemption.
- `amount_inr` (REAL): Transaction amount in INR.
- `state` (TEXT): Investor state.
- `city` (TEXT): Investor city.
- `city_tier` (TEXT): City tier.
- `age_group` (TEXT): Investor age group.
- `gender` (TEXT): Investor gender.
- `annual_income_lakh` (REAL): Annual income in lakhs.
- `payment_mode` (TEXT): Payment mode.
- `kyc_status` (TEXT): KYC status: Verified, Pending, or Unknown.

### 09_portfolio_holdings.csv
- `amfi_code` (INTEGER): Scheme identifier.
- `stock_symbol` (TEXT): Security symbol.
- `stock_name` (TEXT): Security name.
- `sector` (TEXT): Sector name.
- `weight_pct` (REAL): Portfolio weight percent.
- `market_value_cr` (REAL): Market value in crores.
- `current_price_inr` (REAL): Current price in INR.
- `portfolio_date` (DATE): Holdings snapshot date.

### 10_benchmark_indices.csv
- `date` (DATE): Index date.
- `index_name` (TEXT): Index name.
- `close_value` (REAL): Closing index value.

## Star Schema Tables

### dim_fund
- Primary key: `amfi_code`
- Source: `01_fund_master.csv`

### dim_date
- Primary key: `date`
- Derived from all processed date columns.

### fact_nav
- Source: `02_nav_history.csv`
- `nav_id` is the surrogate key.
- Foreign keys: `amfi_code` → `dim_fund`, `date` → `dim_date`.

### fact_transactions
- Source: `08_investor_transactions.csv`
- `transaction_id` is the surrogate key.
- Foreign keys: `amfi_code` → `dim_fund`, `transaction_date` → `dim_date`.

### fact_performance
- Source: `07_scheme_performance.csv`
- `performance_id` is the surrogate key.
- `anomaly_flag` highlights rows with numeric issues or invalid expense ratios.

### fact_aum
- Source: `03_aum_by_fund_house.csv`
- `aum_id` is the surrogate key.
- Foreign key: `date` → `dim_date`.
