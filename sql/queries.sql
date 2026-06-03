-- 1. Top 5 funds by latest AUM from scheme performance
SELECT f.scheme_name,
       f.fund_house,
       p.aum_crore
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
ORDER BY p.aum_crore DESC
LIMIT 5;

-- 2. Average NAV per month across all funds
SELECT strftime('%Y-%m', n.date) AS year_month,
       ROUND(AVG(n.nav), 4) AS avg_nav
FROM fact_nav n
GROUP BY year_month
ORDER BY year_month;

-- 3. SIP YoY transaction growth by year
SELECT strftime('%Y', t.transaction_date) AS year,
       SUM(CASE WHEN t.transaction_type = 'SIP' THEN t.amount_inr ELSE 0 END) AS sip_amount,
       LAG(SUM(CASE WHEN t.transaction_type = 'SIP' THEN t.amount_inr ELSE 0 END)) OVER (ORDER BY strftime('%Y', t.transaction_date)) AS prior_year_sip,
       CASE
           WHEN LAG(SUM(CASE WHEN t.transaction_type = 'SIP' THEN t.amount_inr ELSE 0 END)) OVER (ORDER BY strftime('%Y', t.transaction_date)) > 0
           THEN ROUND((SUM(CASE WHEN t.transaction_type = 'SIP' THEN t.amount_inr ELSE 0 END) - LAG(SUM(CASE WHEN t.transaction_type = 'SIP' THEN t.amount_inr ELSE 0 END)) OVER (ORDER BY strftime('%Y', t.transaction_date))) * 100.0 / LAG(SUM(CASE WHEN t.transaction_type = 'SIP' THEN t.amount_inr ELSE 0 END)) OVER (ORDER BY strftime('%Y', t.transaction_date)) , 2)
           ELSE NULL
       END AS yoy_growth_pct
FROM fact_transactions t
GROUP BY year
ORDER BY year;

-- 4. Transaction count and amount by investor state
SELECT state,
       COUNT(*) AS transaction_count,
       SUM(amount_inr) AS total_amount_inr,
       SUM(CASE WHEN transaction_type = 'SIP' THEN amount_inr ELSE 0 END) AS sip_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_inr DESC
LIMIT 20;

-- 5. Funds with expense ratio below 1%
SELECT f.scheme_name,
       f.fund_house,
       p.expense_ratio_pct
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.expense_ratio_pct < 1.0
ORDER BY p.expense_ratio_pct ASC;

-- 6. Top 5 funds by Sharpe ratio
SELECT f.scheme_name,
       f.fund_house,
       p.sharpe_ratio
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
ORDER BY p.sharpe_ratio DESC
LIMIT 5;

-- 7. Monthly transaction amount by city tier
SELECT strftime('%Y-%m', transaction_date) AS year_month,
       city_tier,
       COUNT(*) AS transaction_count,
       SUM(amount_inr) AS total_amount_inr
FROM fact_transactions
GROUP BY year_month, city_tier
ORDER BY year_month, city_tier;

-- 8. Funds with the largest max drawdown
SELECT f.scheme_name,
       f.fund_house,
       p.max_drawdown_pct
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
ORDER BY p.max_drawdown_pct ASC
LIMIT 5;

-- 9. Average NAV for top 5 funds by AUM
WITH top_funds AS (
    SELECT amfi_code
    FROM fact_performance
    ORDER BY aum_crore DESC
    LIMIT 5
)
SELECT f.scheme_name,
       strftime('%Y-%m', n.date) AS year_month,
       ROUND(AVG(n.nav), 4) AS avg_nav
FROM fact_nav n
JOIN dim_fund f ON n.amfi_code = f.amfi_code
JOIN top_funds t ON n.amfi_code = t.amfi_code
GROUP BY f.scheme_name, year_month
ORDER BY f.scheme_name, year_month;

-- 10. AUM growth change by fund house
SELECT a.fund_house,
       strftime('%Y-%m', a.date) AS year_month,
       SUM(a.aum_crore) AS total_aum_crore
FROM fact_aum a
GROUP BY a.fund_house, year_month
ORDER BY a.fund_house, year_month;
