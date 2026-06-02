# Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Prepare Your Data
Place your CSV datasets in the `data/raw/` directory:
```
capstone_project/data/raw/
├── fund_master.csv
├── nav_history.csv
└── [other CSV files]
```

### Step 2: Start Jupyter Notebook
Open a terminal/PowerShell in the project directory:
```bash
cd c:\Users\chinnu\Downloads\chinnu\capstone_project
jupyter notebook
```

### Step 3: Open the Notebook
- Navigate to `notebooks/`
- Open `01_mutual_fund_analysis.ipynb`
- Click the first cell (imports)

### Step 4: Run Cells in Order
Click "Run" or press **Shift+Enter** for each cell:
1. **Cell 1:** Imports libraries ✓
2. **Cell 2:** Load CSV files
3. **Cell 3:** Fetch live NAV data
4. **Cell 4:** Explore fund master
5. **Cell 5:** Validate AMFI codes
6. **Cell 6:** View summary

### Step 5: Check Reports
Generated reports appear in:
- `reports/data_quality_report_YYYYMMDD_HHMMSS.json`

---

## 📊 What the Notebook Does

| Cell | Task | Output |
|------|------|--------|
| 1 | Setup environment | Library check ✓ |
| 2 | Load CSVs | Shape, dtypes, anomalies |
| 3 | API data | NAV CSVs saved |
| 4 | Fund analysis | Unique values, structure |
| 5 | Validate data | Quality report |
| 6 | Summary | Findings & next steps |

---

## 🔧 Common Commands

### View Project Structure
```bash
Get-ChildItem -Recurse capstone_project
```

### Check Installed Packages
```bash
pip list | findstr /E "pandas|numpy|matplotlib"
```

### Update Requirements
```bash
pip freeze > requirements.txt
```

### Run Single Python Script
```bash
python script_name.py
```

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `notebooks/01_mutual_fund_analysis.ipynb` | Main analysis notebook |
| `config.py` | Utility functions |
| `sql/sample_queries.sql` | Database queries |
| `README.md` | Full documentation |
| `requirements.txt` | Dependencies |
| `SETUP_SUMMARY.md` | Setup details |

---

## ⚠️ Troubleshooting

### "No CSV files found"
✓ Place CSV files in `data/raw/` directory

### "Module not found" error
✓ Run `pip install -r requirements.txt`

### Jupyter won't start
✓ Run `pip install jupyter`

### API timeout
✓ Check internet connection, API may be slow

### Memory error with large files
✓ Process in chunks using pandas `.read_csv(chunksize=10000)`

---

## 📝 Sample CSV Column Names

Fund Master expected columns:
- Code / Scheme Code / AMFI Code
- Scheme Name
- Fund House
- Category
- Sub-Category
- Risk Grade

NAV History expected columns:
- Scheme Code / Code
- Date
- NAV
- [other fields]

---

## 🎯 Next Steps

1. ✓ Project setup complete
2. → Place CSV files
3. → Run notebook cells
4. → Analyze reports
5. → Create custom analysis notebooks

---

## 💡 Tips

- **Save early, save often** - Jupyter auto-saves but always use Ctrl+S
- **Run cells in order** - They build on each other
- **Check console output** - Anomalies and warnings show up there
- **Export data** - Use `df.to_csv()` to save processed data

---

**Happy Analyzing! 📊**
