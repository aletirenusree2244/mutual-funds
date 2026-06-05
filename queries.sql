-- 1) Top 5 fund houses by latest AUM
SELECT fund_house, aum_crore
FROM fact_aum AS f1
WHERE date = (SELECT MAX(date) FROM fact_aum)
ORDER BY aum_crore DESC
LIMIT 5;

-- 2) Average NAV per month for each fund
SELECT amfi_code, strftime('%Y-%m', date) AS year_month, AVG(nav) AS avg_nav
FROM fact_nav
GROUP BY amfi_code, year_month
ORDER BY amfi_code, year_month;

-- 3) SIP YoY growth (total SIP amount per year and % growth)
WITH year_sip AS (
  SELECT strftime('%Y', transaction_date) AS year, SUM(amount_inr) AS total_sip
  FROM fact_transactions
  WHERE transaction_type = 'SIP'
  GROUP BY year
)
SELECT y.year, y.total_sip,
       ROUND((y.total_sip - LAG(y.total_sip) OVER (ORDER BY y.year)) * 100.0 / NULLIF(LAG(y.total_sip) OVER (ORDER BY y.year),0),2) AS pct_change_yoy
FROM year_sip y
ORDER BY y.year;

-- 4) Transactions by state (count and total amount)
SELECT state, COUNT(*) AS tx_count, SUM(amount_inr) AS total_amount
FROM fact_transactions
GROUP BY state
ORDER BY total_amount DESC;

-- 5) Funds with expense_ratio outside 0.1% - 2.5%
SELECT amfi_code, scheme_name, expense_ratio_pct
FROM fact_performance
WHERE expense_ratio_pct IS NOT NULL AND (expense_ratio_pct < 0.1 OR expense_ratio_pct > 2.5)
ORDER BY expense_ratio_pct DESC;

-- 6) Top 10 funds by 3-year return
SELECT amfi_code, scheme_name, return_3yr_pct
FROM fact_performance
ORDER BY return_3yr_pct DESC
LIMIT 10;

-- 7) Quarterly AUM growth per fund house (latest vs previous quarter)
WITH ordered AS (
  SELECT fund_house, date, aum_crore,
    ROW_NUMBER() OVER (PARTITION BY fund_house ORDER BY date DESC) AS rn
  FROM fact_aum
)
SELECT cur.fund_house,
       cur.aum_crore AS latest_aum,
       prev.aum_crore AS prev_aum,
       ROUND((cur.aum_crore - prev.aum_crore) * 100.0 / NULLIF(prev.aum_crore,0),2) AS pct_change
FROM ordered cur
LEFT JOIN ordered prev ON cur.fund_house = prev.fund_house AND prev.rn = cur.rn + 1
WHERE cur.rn = 1;

-- 8) Redemption ratio per fund (redemption amount / total transaction amount)
SELECT amfi_code,
  SUM(CASE WHEN transaction_type = 'Redemption' THEN amount_inr ELSE 0 END) AS redemption_amount,
  SUM(amount_inr) AS total_amount,
  ROUND(100.0 * SUM(CASE WHEN transaction_type = 'Redemption' THEN amount_inr ELSE 0 END) / NULLIF(SUM(amount_inr),0),2) AS redemption_pct
FROM fact_transactions
GROUP BY amfi_code
ORDER BY redemption_pct DESC
LIMIT 20;

-- 9) Monthly SIP inflow YoY change using monthly SIP inflows table
SELECT month AS year_month, SUM(sip_inflow_crore) AS sip_inflow_crore
FROM "04_monthly_sip_inflows"
GROUP BY month
ORDER BY month;

-- 10) NAV volatility (stddev) for the last 12 months per fund
WITH latest AS (
  SELECT MAX(date) AS max_date FROM fact_nav
), windowed AS (
  SELECT n.*
  FROM fact_nav n, latest l
  WHERE date >= date(l.max_date, '-12 months')
)
SELECT amfi_code, ROUND(STDDEV_POP(nav),4) AS nav_stddev
FROM windowed
GROUP BY amfi_code
ORDER BY nav_stddev DESC
LIMIT 20;
