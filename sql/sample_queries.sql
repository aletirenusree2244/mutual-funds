-- Sample SQL Queries for Mutual Fund Analysis

-- 1. Get unique fund houses and their scheme count
SELECT 
    fund_house,
    COUNT(DISTINCT scheme_code) as scheme_count,
    COUNT(*) as total_records
FROM fund_master
GROUP BY fund_house
ORDER BY scheme_count DESC;

-- 2. Analyze NAV trends for a specific scheme
SELECT 
    scheme_code,
    DATE(date) as nav_date,
    AVG(nav) as avg_nav,
    MIN(nav) as min_nav,
    MAX(nav) as max_nav,
    COUNT(*) as record_count
FROM nav_history
WHERE scheme_code = '125497'  -- HDFC Top 100
GROUP BY scheme_code, DATE(date)
ORDER BY DATE(date) DESC;

-- 3. Find schemes with highest average NAV
SELECT 
    fm.scheme_code,
    fm.scheme_name,
    fm.fund_house,
    ROUND(AVG(nh.nav), 2) as avg_nav,
    COUNT(nh.nav) as nav_records
FROM fund_master fm
JOIN nav_history nh ON fm.scheme_code = nh.scheme_code
GROUP BY fm.scheme_code, fm.scheme_name, fm.fund_house
ORDER BY avg_nav DESC
LIMIT 10;

-- 4. Check for orphaned codes (in nav_history but not in fund_master)
SELECT DISTINCT nh.scheme_code
FROM nav_history nh
LEFT JOIN fund_master fm ON nh.scheme_code = fm.scheme_code
WHERE fm.scheme_code IS NULL;

-- 5. Get category-wise fund distribution
SELECT 
    category,
    sub_category,
    COUNT(*) as fund_count,
    ROUND(AVG(expense_ratio), 2) as avg_expense_ratio
FROM fund_master
GROUP BY category, sub_category
ORDER BY category, fund_count DESC;

-- 6. Recent NAV updates (last 30 days)
SELECT 
    fm.scheme_name,
    nh.date,
    nh.nav,
    LAG(nh.nav) OVER (PARTITION BY nh.scheme_code ORDER BY nh.date) as prev_nav,
    ROUND((nh.nav - LAG(nh.nav) OVER (PARTITION BY nh.scheme_code ORDER BY nh.date)) / 
          LAG(nh.nav) OVER (PARTITION BY nh.scheme_code ORDER BY nh.date) * 100, 2) as nav_change_pct
FROM nav_history nh
JOIN fund_master fm ON nh.scheme_code = fm.scheme_code
WHERE nh.date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
ORDER BY nh.date DESC, fm.scheme_name;

-- 7. Risk grade distribution
SELECT 
    risk_grade,
    COUNT(*) as scheme_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM fund_master), 2) as percentage
FROM fund_master
GROUP BY risk_grade
ORDER BY risk_grade;

-- 8. Schemes by category and risk grade
SELECT 
    category,
    risk_grade,
    COUNT(*) as scheme_count
FROM fund_master
GROUP BY category, risk_grade
ORDER BY category, risk_grade;

-- 9. Top 5 schemes by latest NAV
SELECT 
    fm.scheme_name,
    fm.category,
    nh.nav,
    nh.date,
    fm.risk_grade
FROM nav_history nh
JOIN fund_master fm ON nh.scheme_code = fm.scheme_code
WHERE nh.date = (SELECT MAX(date) FROM nav_history)
ORDER BY nh.nav DESC
LIMIT 5;

-- 10. Data quality check - schemes with missing recent NAV
SELECT 
    fm.scheme_code,
    fm.scheme_name,
    MAX(nh.date) as last_nav_date,
    DATEDIFF(CURDATE(), MAX(nh.date)) as days_since_last_nav
FROM fund_master fm
LEFT JOIN nav_history nh ON fm.scheme_code = nh.scheme_code
GROUP BY fm.scheme_code, fm.scheme_name
HAVING DATEDIFF(CURDATE(), MAX(nh.date)) > 7
ORDER BY days_since_last_nav DESC;
