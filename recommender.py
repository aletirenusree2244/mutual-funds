"""
Fund Recommender System - Advanced Mutual Fund Recommendation Engine
=====================================================================

This module provides a risk-based fund recommendation system that suggests
the top funds based on investor risk appetite and Sharpe ratio performance.

Author: Advanced Analytics Team
Date: 2025
"""

import pandas as pd
import numpy as np
from typing import Union, List, Dict


class FundRecommender:
    """
    Risk-based fund recommendation system for mutual funds.
    
    This recommender takes into account:
    - Investor risk appetite (Low/Moderate/High)
    - Fund risk category
    - Sharpe ratio (risk-adjusted returns)
    - Annual return and volatility
    """
    
    # Risk category mapping
    RISK_MAPPING = {
        'Low': ['Low'],
        'Moderate': ['Low', 'Moderate'],
        'High': ['Moderate', 'High']
    }
    
    def __init__(self, var_cvar_data: pd.DataFrame, fund_master: pd.DataFrame):
        """
        Initialize the recommender with fund data.
        
        Parameters
        ----------
        var_cvar_data : pd.DataFrame
            DataFrame containing VaR, CVaR, returns, and volatility for each fund.
            Must have columns: amfi_code, scheme_name, risk_category, 
            Annual_Return, Annual_Volatility
        fund_master : pd.DataFrame
            Master fund data with scheme details
        """
        self.var_cvar_data = var_cvar_data.copy()
        self.fund_master = fund_master.copy()
        self._calculate_sharpe_ratios()
    
    def _calculate_sharpe_ratios(self):
        """Calculate Sharpe ratio for each fund."""
        self.var_cvar_data['sharpe_ratio'] = self.var_cvar_data.apply(
            lambda row: row['Annual_Return'] / row['Annual_Volatility'] 
            if row['Annual_Volatility'] > 0 else 0,
            axis=1
        )
    
    def recommend(self, risk_appetite: str, top_n: int = 3, 
                  return_format: str = 'dataframe') -> Union[pd.DataFrame, List[Dict]]:
        """
        Get fund recommendations based on risk appetite.
        
        Parameters
        ----------
        risk_appetite : str
            Investor risk appetite: 'Low', 'Moderate', or 'High'
        top_n : int, optional
            Number of top recommendations (default: 3)
        return_format : str, optional
            Format of output: 'dataframe' or 'list' (default: 'dataframe')
        
        Returns
        -------
        pd.DataFrame or List[Dict]
            Top N recommended funds sorted by Sharpe ratio
            
        Raises
        ------
        ValueError
            If risk_appetite is not valid or top_n <= 0
        """
        
        if risk_appetite not in self.RISK_MAPPING:
            raise ValueError(
                f"Invalid risk appetite '{risk_appetite}'. "
                f"Choose from: {list(self.RISK_MAPPING.keys())}"
            )
        
        if top_n <= 0:
            raise ValueError("top_n must be greater than 0")
        
        # Filter by risk category
        target_categories = self.RISK_MAPPING[risk_appetite]
        filtered_funds = self.var_cvar_data[
            self.var_cvar_data['risk_category'].isin(target_categories)
        ].copy()
        
        # Sort by Sharpe ratio descending
        filtered_funds = filtered_funds.sort_values('sharpe_ratio', ascending=False)
        
        # Get top N
        recommendations = filtered_funds.head(top_n)[[
            'amfi_code', 'scheme_name', 'risk_category', 
            'Annual_Return', 'Annual_Volatility', 'sharpe_ratio'
        ]].copy()
        
        if return_format == 'list':
            return recommendations.to_dict('records')
        else:
            return recommendations
    
    def get_recommendation_details(self, risk_appetite: str, 
                                   top_n: int = 3) -> pd.DataFrame:
        """
        Get detailed recommendation information including performance metrics.
        
        Parameters
        ----------
        risk_appetite : str
            Investor risk appetite: 'Low', 'Moderate', or 'High'
        top_n : int, optional
            Number of top recommendations (default: 3)
        
        Returns
        -------
        pd.DataFrame
            Detailed fund information with formatted columns
        """
        
        recommendations = self.recommend(risk_appetite, top_n, return_format='dataframe')
        
        # Merge with additional data if available
        details = recommendations.copy()
        details.columns = [
            'AMFI Code', 'Scheme Name', 'Risk Category',
            'Annual Return (%)', 'Volatility (%)', 'Sharpe Ratio'
        ]
        
        # Add ranking
        details.insert(0, 'Rank', range(1, len(details) + 1))
        
        return details
    
    def compare_recommendations(self) -> Dict[str, pd.DataFrame]:
        """
        Get recommendations for all three risk appetites.
        
        Returns
        -------
        Dict[str, pd.DataFrame]
            Dictionary with keys 'Low', 'Moderate', 'High' and 
            corresponding recommendation DataFrames
        """
        
        comparisons = {}
        for risk_appetite in self.RISK_MAPPING.keys():
            comparisons[risk_appetite] = self.get_recommendation_details(
                risk_appetite, top_n=3
            )
        
        return comparisons
    
    def print_recommendations(self, risk_appetite: str, top_n: int = 3) -> None:
        """
        Print recommendations in a formatted table.
        
        Parameters
        ----------
        risk_appetite : str
            Investor risk appetite: 'Low', 'Moderate', or 'High'
        top_n : int, optional
            Number of top recommendations (default: 3)
        """
        
        print(f"\n{'═' * 100}")
        print(f"FUND RECOMMENDATIONS - RISK APPETITE: {risk_appetite.upper()}")
        print(f"{'═' * 100}")
        
        details = self.get_recommendation_details(risk_appetite, top_n)
        print(details.to_string(index=False))
        print()
    
    def get_fund_profile(self, amfi_code: int) -> Dict:
        """
        Get detailed profile of a specific fund.
        
        Parameters
        ----------
        amfi_code : int
            AMFI code of the fund
        
        Returns
        -------
        Dict
            Comprehensive fund information
        """
        
        fund_data = self.var_cvar_data[self.var_cvar_data['amfi_code'] == amfi_code]
        
        if fund_data.empty:
            return {"error": f"Fund with AMFI code {amfi_code} not found"}
        
        fund = fund_data.iloc[0]
        
        return {
            'amfi_code': fund['amfi_code'],
            'scheme_name': fund['scheme_name'],
            'risk_category': fund['risk_category'],
            'annual_return': round(fund['Annual_Return'], 2),
            'annual_volatility': round(fund['Annual_Volatility'], 2),
            'sharpe_ratio': round(fund['sharpe_ratio'], 2),
            'var_95pct': round(fund['VaR_95pct'], 2),
            'cvar': round(fund['CVaR'], 2)
        }


def create_recommendation_report(var_cvar_data: pd.DataFrame, 
                                 fund_master: pd.DataFrame,
                                 output_file: str = 'recommendation_report.csv') -> pd.DataFrame:
    """
    Create a comprehensive recommendation report for all risk appetites.
    
    Parameters
    ----------
    var_cvar_data : pd.DataFrame
        Fund performance data
    fund_master : pd.DataFrame
        Fund master data
    output_file : str, optional
        File to save the report (default: 'recommendation_report.csv')
    
    Returns
    -------
    pd.DataFrame
        Complete recommendation report
    """
    
    recommender = FundRecommender(var_cvar_data, fund_master)
    
    # Get all recommendations
    recommendations = []
    for risk_appetite in ['Low', 'Moderate', 'High']:
        for rank, (_, fund) in enumerate(
            recommender.recommend(risk_appetite, top_n=3).iterrows(), 1
        ):
            recommendations.append({
                'Risk_Appetite': risk_appetite,
                'Rank': rank,
                'AMFI_Code': fund['amfi_code'],
                'Scheme_Name': fund['scheme_name'],
                'Annual_Return_pct': round(fund['Annual_Return'], 2),
                'Volatility_pct': round(fund['Annual_Volatility'], 2),
                'Sharpe_Ratio': round(fund['sharpe_ratio'], 2)
            })
    
    report = pd.DataFrame(recommendations)
    
    if output_file:
        report.to_csv(output_file, index=False)
        print(f"✓ Recommendation report saved to {output_file}")
    
    return report


# Example usage
if __name__ == "__main__":
    # This would be used as:
    # recommender = FundRecommender(var_cvar_data, fund_master)
    # recommendations = recommender.recommend('Moderate', top_n=3)
    # recommender.print_recommendations('High')
    
    print("Fund Recommender Module - Ready to use")
    print("Import this module to create fund recommendations")
