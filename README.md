# Mutual Fund Analysis - Capstone Project

A comprehensive data analysis project for mutual fund scheme performance, NAV tracking, and data validation using Python and pandas.

## Project Structure

```
capstone_project/
├── data/
│   ├── raw/           # Raw CSV datasets and API responses
│   └── processed/     # Cleaned and processed data ready for analysis
├── notebooks/         # Jupyter notebooks for analysis and exploration
├── sql/              # SQL scripts for database queries
├── dashboard/        # Dashboard and visualization files
├── reports/          # Generated reports and validation results
├── requirements.txt  # Python package dependencies
├── .gitignore       # Git ignore configuration
└── README.md        # This file
```

## Setup Instructions

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Git (optional, for version control)

### Installation

1. **Navigate to project directory:**
   ```bash
   cd capstone_project
   ```

2. **Create virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Dependencies

All required packages are listed in `requirements.txt`:
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing
- **matplotlib**: Data visualization
- **seaborn**: Statistical data visualization
- **plotly**: Interactive visualizations
- **sqlalchemy**: SQL toolkit
- **requests**: HTTP library for API calls
- **scipy**: Scientific computing
- **jupyter**: Interactive notebooks

## Usage

### Running the Analysis Notebook

1. **Start Jupyter:**
   ```bash
   jupyter notebook
   ```

2. **Open the notebook:**
   Navigate to `notebooks/01_mutual_fund_analysis.ipynb`

3. **Execute cells:**
   Run cells in order to perform data loading, exploration, and validation

### Data Loading

Place CSV datasets in the `data/raw/` directory. The notebook expects files such as:
- `fund_master.csv` - Fund scheme master data
- `nav_history.csv` - NAV historical data
- Additional CSV datasets as needed

### API Integration

The notebook fetches live NAV data from [mfapi.in](https://mfapi.in) for:
- HDFC Top 100 Direct (125497)
- SBI Bluechip (119551)
- ICICI Bluechip (120503)
- Nippon Large Cap (118632)
- Axis Bluechip (119092)
- Kotak Bluechip (120841)

Retrieved data is automatically saved to `data/raw/` directory.

## Features

### Data Analysis
- Load and explore multiple CSV datasets
- Display shape, data types, and sample data
- Identify and report anomalies and missing values

### Live NAV Fetching
- Fetch current NAV from mutual fund API
- Parse JSON responses
- Save data as CSV files

### Fund Master Exploration
- Analyze fund houses and categories
- Explore sub-categories and risk grades
- Understand AMFI scheme code structure

### Data Validation
- Cross-validate AMFI codes between datasets
- Identify orphaned records
- Generate data quality reports
- Calculate matching percentages

### Reporting
- Automated validation reports in JSON format
- Quality metrics and statistics
- Timestamp tracking for reproducibility

## AMFI Code Structure

AMFI (Association of Mutual Funds in India) scheme codes are 6-digit numeric identifiers assigned to each mutual fund scheme. The structure includes:
- **Code Range**: 100000-999999
- **Uniqueness**: Each code uniquely identifies a scheme
- **Usage**: Used across regulators, distributors, and platforms

## Data Quality Checks

The notebook performs comprehensive validation:
1. **Missing Values**: Identifies null/NaN values in key columns
2. **Duplicates**: Detects duplicate records
3. **Code Validation**: Ensures scheme codes exist in expected datasets
4. **Data Integrity**: Cross-validates relationships between datasets

## Generated Reports

Reports are saved in the `reports/` directory with timestamps:
- `data_quality_report_YYYYMMDD_HHMMSS.json`

Reports include:
- Dataset loading summary
- AMFI code validation results
- Orphaned record counts
- Match percentages
- Data quality metrics

## Common Issues & Solutions

### Issue: "No CSV files found in data/raw directory"
**Solution:** Place your CSV datasets in the `data/raw/` folder and re-run the data loading cell

### Issue: API rate limiting (Too many requests)
**Solution:** Add delays between API calls or use cached data

### Issue: Memory errors with large datasets
**Solution:** Process data in chunks or filter by date range

## Performance Tips

- Use `pandas.read_csv(..., dtype={...})` to optimize memory usage
- Filter data before plotting to reduce visualization load
- Use chunking for very large datasets
- Save processed data to reduce re-processing time

## Extending the Analysis

### Add New Schemes
Update the `primary_schemes` dictionary in the notebook with new AMFI codes

### Custom Analysis
Create new notebooks in the `notebooks/` directory following the naming convention `NN_description.ipynb`

### Database Integration
Use SQL scripts in `sql/` directory for data warehousing and complex queries

## Version History

- **v1.0** (2026-06-02): Initial project setup with data loading and API integration

## Contributing

Guidelines for contributing:
1. Create new notebooks for analyses
2. Document findings in reports/
3. Follow naming conventions: `NN_description.ipynb`
4. Update README with new features

## License

This project is for educational purposes.

## Support

For issues or questions:
1. Check the data quality report
2. Review the notebook execution logs
3. Verify API connectivity to mfapi.in
4. Check data file formats and locations

## References

- [MFAPI Documentation](https://mfapi.in)
- [AMFI](https://www.amfiindia.com/)
- [Pandas Documentation](https://pandas.pydata.org/)
- [Jupyter Documentation](https://jupyter.org/)

---

**Last Updated:** June 2, 2026
**Project Status:** Active Development
