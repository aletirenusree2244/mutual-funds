"""
Utility functions and configuration for the Mutual Fund Analysis project
"""

import os
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# Project directories
BASE_DIR = Path(__file__).parent.parent
DATA_RAW_DIR = BASE_DIR / 'data' / 'raw'
DATA_PROCESSED_DIR = BASE_DIR / 'data' / 'processed'
REPORTS_DIR = BASE_DIR / 'reports'
NOTEBOOKS_DIR = BASE_DIR / 'notebooks'

# API Configuration
MFAPI_BASE_URL = "https://api.mfapi.in/mf"
API_TIMEOUT = 10
API_RETRY_ATTEMPTS = 3

# AMFI Schemes Dictionary
AMFI_SCHEMES = {
    '125497': 'HDFC Top 100 Direct',
    '119551': 'SBI Bluechip',
    '120503': 'ICICI Bluechip',
    '118632': 'Nippon Large Cap',
    '119092': 'Axis Bluechip',
    '120841': 'Kotak Bluechip',
}

# Data quality thresholds
MIN_DATA_COMPLETENESS = 95.0  # Minimum % of non-null values
MAX_ALLOWED_DUPLICATES = 0     # Maximum allowed duplicate rows


def ensure_directories():
    """Create all required project directories"""
    directories = [DATA_RAW_DIR, DATA_PROCESSED_DIR, REPORTS_DIR]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def load_csv_file(filepath, **kwargs):
    """
    Load a CSV file with error handling
    
    Parameters:
    - filepath: Path to CSV file
    - **kwargs: Additional arguments for pd.read_csv()
    
    Returns:
    - DataFrame or None if error occurs
    """
    try:
        df = pd.read_csv(filepath, **kwargs)
        return df
    except Exception as e:
        print(f"Error loading {filepath}: {str(e)}")
        return None


def save_csv_file(df, output_path, index=False):
    """
    Save DataFrame to CSV with error handling
    
    Parameters:
    - df: DataFrame to save
    - output_path: Output file path
    - index: Whether to include index
    
    Returns:
    - True if successful, False otherwise
    """
    try:
        df.to_csv(output_path, index=index)
        return True
    except Exception as e:
        print(f"Error saving to {output_path}: {str(e)}")
        return False


def get_data_quality_report(df, name="Dataset"):
    """
    Generate a data quality report for a DataFrame
    
    Parameters:
    - df: DataFrame to analyze
    - name: Name of the dataset
    
    Returns:
    - Dictionary with quality metrics
    """
    report = {
        'name': name,
        'shape': df.shape,
        'total_cells': df.shape[0] * df.shape[1],
        'missing_cells': df.isnull().sum().sum(),
        'missing_percentage': round(df.isnull().sum().sum() / (df.shape[0] * df.shape[1]) * 100, 2),
        'duplicate_rows': df.duplicated().sum(),
        'memory_usage_kb': round(df.memory_usage(deep=True).sum() / 1024, 2),
        'columns': {
            col: {
                'dtype': str(df[col].dtype),
                'null_count': int(df[col].isnull().sum()),
                'unique_count': int(df[col].nunique()),
                'sample_values': df[col].dropna().unique()[:3].tolist()
            } for col in df.columns
        }
    }
    return report


def validate_amfi_codes(fund_master, nav_history, fm_code_col, nh_code_col):
    """
    Validate AMFI codes between two datasets
    
    Parameters:
    - fund_master: Fund master DataFrame
    - nav_history: NAV history DataFrame
    - fm_code_col: Column name for codes in fund_master
    - nh_code_col: Column name for codes in nav_history
    
    Returns:
    - Validation report dictionary
    """
    fm_codes = set(fund_master[fm_code_col].dropna().unique())
    nh_codes = set(nav_history[nh_code_col].dropna().unique())
    
    matching_codes = fm_codes & nh_codes
    orphaned_in_fm = fm_codes - nh_codes
    orphaned_in_nh = nh_codes - fm_codes
    
    match_percentage = (len(matching_codes) / len(fm_codes) * 100) if len(fm_codes) > 0 else 0
    
    report = {
        'timestamp': str(datetime.now()),
        'fund_master_codes': len(fm_codes),
        'nav_history_codes': len(nh_codes),
        'matching_codes': len(matching_codes),
        'match_percentage': round(match_percentage, 2),
        'orphaned_in_fund_master': len(orphaned_in_fm),
        'orphaned_in_nav_history': len(orphaned_in_nh),
        'orphaned_codes_examples_fm': list(sorted(orphaned_in_fm))[:5] if orphaned_in_fm else [],
        'orphaned_codes_examples_nh': list(sorted(orphaned_in_nh))[:5] if orphaned_in_nh else [],
        'validation_status': 'PASS' if match_percentage == 100 else 'FAIL'
    }
    
    return report


def save_report(report_data, report_name="report"):
    """
    Save a report as JSON file
    
    Parameters:
    - report_data: Dictionary with report data
    - report_name: Name of the report
    
    Returns:
    - Path to saved report file
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = REPORTS_DIR / f"{report_name}_{timestamp}.json"
    
    try:
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        return report_file
    except Exception as e:
        print(f"Error saving report: {str(e)}")
        return None


def print_section_header(title, width=70):
    """Print a formatted section header"""
    print(f"\n{'='*width}")
    print(f"{title:^{width}}")
    print(f"{'='*width}")


def print_key_value(key, value, indent=2):
    """Print key-value pair with indentation"""
    print(f"{'':>{indent}}{key}: {value}")
