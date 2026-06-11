# Data Schema Reference

## Fund Master Dataset

### Expected Structure
```
fund_master.csv
Columns:
- Code / Scheme_Code / AMFI_Code
  Type: Integer or String
  Description: Unique AMFI code for the scheme
  
- Scheme_Name / Name
  Type: String
  Description: Official scheme name
  
- Fund_House / Mutual_Fund_House
  Type: String
  Description: Name of the fund house
  Example: HDFC, ICICI, SBI, Axis, Kotak, etc.
  
- Category / Fund_Category
  Type: String
  Description: Fund classification
  Examples: Equity, Debt, Hybrid, Solution Oriented, Other
  
- Sub_Category / Sub_Category_Name
  Type: String
  Description: More specific fund classification
  Examples: Large Cap, Mid Cap, Dividend Yield, Gilt, Credit Opportunity
  
- Risk_Grade / Risk_Rating
  Type: String or Integer
  Description: Risk classification
  Values: Low, Medium, High (or 1-5 scale)
```

### Sample Rows
```
Code,Scheme_Name,Fund_House,Category,Sub_Category,Risk_Grade
125497,HDFC Top 100 Direct,HDFC,Equity,Large Cap,Medium
119551,SBI Bluechip Direct,SBI,Equity,Large Cap,Medium
120503,ICICI Bluechip Direct,ICICI,Equity,Large Cap,Medium
118632,Nippon India Large Cap Direct,Nippon,Equity,Large Cap,Medium
```

---

## NAV History Dataset

### Expected Structure
```
nav_history.csv
Columns:
- Code / Scheme_Code / AMFI_Code
  Type: Integer or String
  Description: Scheme identifier (foreign key to fund_master)
  
- Date / NAV_Date
  Type: Date
  Format: YYYY-MM-DD or DD-MM-YYYY
  Description: NAV valuation date
  
- NAV
  Type: Float/Decimal
  Description: Net Asset Value per unit
  Example: 150.25, 300.50, etc.
  
- (Optional) Repurchase_Price
  Type: Float
  Description: Price at which fund repurchases units
  
- (Optional) Sale_Price / Offer_Price
  Type: Float
  Description: Price at which fund sells units
```

### Sample Rows
```
Code,Date,NAV,Repurchase_Price,Sale_Price
125497,2026-06-02,250.50,250.45,250.55
125497,2026-06-01,250.25,250.20,250.30
119551,2026-06-02,180.75,180.70,180.80
```

---

## AMFI Code Structure

### Format
- **Length:** 6 digits
- **Range:** 100000 - 999999
- **Type:** Numeric identifier
- **Uniqueness:** Each code uniquely identifies one scheme

### Examples
```
125497 - HDFC Top 100 Direct
119551 - SBI Bluechip Direct
120503 - ICICI Bluechip Direct
118632 - Nippon India Large Cap
119092 - Axis Bluechip Direct
120841 - Kotak Bluechip Direct
```

### Database Relationship
```
fund_master.Code (Primary Key)
    ↓
    ↓ One-to-Many
    ↓
nav_history.Code (Foreign Key)
```

---

## API Response Format (mfapi.in)

### Example Response
```json
{
  "meta": {
    "fund_house": "HDFC",
    "scheme_type": "Open Ended Schemes",
    "scheme_category": "Equity",
    "scheme_name": "HDFC Top 100 Direct",
    "isin": "INF111K01287",
    "amfi_code": "125497"
  },
  "status": "SUCCESS",
  "data": [
    {
      "date": "02-06-2026",
      "nav": "250.50"
    },
    {
      "date": "01-06-2026",
      "nav": "250.25"
    }
  ]
}
```

### Parsed CSV Format (After Processing)
```
date,nav,scheme_code,scheme_name,fetched_at
2026-06-02,250.50,125497,HDFC Top 100 Direct,2026-06-02 14:30:45
2026-06-01,250.25,125497,HDFC Top 100 Direct,2026-06-02 14:30:45
```

---

## Notebook Expected Inputs

### Section 2: CSV Loading
**Input:** Files in `data/raw/*.csv`
**Expected columns:** See Fund Master and NAV History schemas above

### Section 3: API Fetch
**Input:** AMFI scheme codes (built-in)
**Expected:** Internet connectivity to api.mfapi.in
**Output:** CSV files in `data/raw/`

### Section 4: Fund Analysis
**Input:** `fund_master.csv` loaded
**Expected columns:** Code, Scheme_Name, Fund_House, Category, Sub_Category, Risk_Grade

### Section 5: Validation
**Inputs:** 
- `fund_master.csv` 
- `nav_history.csv`
**Expected:** Code columns in both

---

## Data Quality Checks

### Null Values Check
```
Column Name: X missing values out of Y total
Formula: (Missing / Total) * 100 = %
Action: Investigate if > 5% in key columns
```

### Duplicate Detection
```
Duplicate rows: X (same values in all columns)
Duplicate codes: Y (same code value, different other fields)
Action: Remove exact duplicates, review code duplicates
```

### Code Validation
```
Matching codes: X out of Y
Match percentage: Z%
Orphaned in FM: Codes in fund_master but not in nav_history
Orphaned in NH: Codes in nav_history but not in fund_master
Action: Investigate if > 5% orphaned
```

---

## Common Data Anomalies

### Issue 1: Date Format Mismatch
**Problem:** Dates stored as "02-06-2026" instead of "2026-06-02"
**Solution:** Use `pd.to_datetime(column, format='%d-%m-%Y')`

### Issue 2: NAV as String
**Problem:** NAV values stored as "250.50" instead of 250.50
**Solution:** Use `pd.to_numeric(column, errors='coerce')`

### Issue 3: Missing NAV Dates
**Problem:** Some schemes have gaps in daily NAV data
**Solution:** Identify missing dates and investigate reasons

### Issue 4: Duplicate Rows
**Problem:** Same code, date, NAV appearing multiple times
**Solution:** `df.drop_duplicates(subset=['Code', 'Date'], keep='first')`

### Issue 5: Scheme Code Type Mismatch
**Problem:** Codes as integers vs strings ("125497" vs 125497)
**Solution:** Convert to string for consistency: `df['Code'] = df['Code'].astype(str)`

---

## SQL Data Types

### Fund Master Table
```sql
CREATE TABLE fund_master (
    code INT PRIMARY KEY,
    scheme_name VARCHAR(255),
    fund_house VARCHAR(100),
    category VARCHAR(100),
    sub_category VARCHAR(100),
    risk_grade VARCHAR(50)
);
```

### NAV History Table
```sql
CREATE TABLE nav_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    code INT,
    date DATE,
    nav DECIMAL(10, 2),
    FOREIGN KEY (code) REFERENCES fund_master(code)
);
```

---

## Import Guidelines

### Column Name Standardization
When loading CSV, standardize column names:
```python
df.columns = df.columns.str.lower().str.strip()
df.columns = df.columns.str.replace(' ', '_')
df.columns = df.columns.str.replace('-', '_')
```

### Data Type Conversion
```python
# Code column
df['code'] = df['code'].astype(str).str.zfill(6)

# Date column
df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y')

# NAV column
df['nav'] = pd.to_numeric(df['nav'], errors='coerce')
```

---

**Reference Version:** 1.0  
**Last Updated:** June 2, 2026
