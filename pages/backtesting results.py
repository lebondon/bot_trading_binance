import streamlit as st
import pandas as pd
import numpy as np

def get_backtesting_data():
    """Generate the backtesting data directly."""
    df = pd.DataFrame({
        'Strategy': ['Moving Average', 'RSI', 'Bollinger Bands', 'MACD', 'Stochastic'],
        'Return (%)': [34.04, 72.66, 21.40, 27.25, 28.76],
        'Win Rate (%)': [55.3, 62.8, 48.9, 52.4, 63.67],
        'Total Trades': [120, 95, 150, 110, 140],
        'Max Drawdown (%)': [-15.2, -9.4, -18.6, -14.8, -16.2]
    })
    return df

def main():
    st.title("Trading Strategy Backtesting Results")
    
    st.write("""
    ## Overview
    This page shows a simplified analysis of trading strategy performance 
    for BTC/USDT trading from January 2024 to March 2024.
    """)
    
    # Get the backtesting data
    results = get_backtesting_data()
    
    # Display the dataframe
    st.dataframe(results)
    
    # Metric explanations
    st.write("""
    ### Metric Explanations

    
    - **Return (%)**: Total percentage return of the strategy
        - Calculation: ((Final Capital - Initial Capital) / Initial Capital) * 100
        - Measures the overall profitability of the strategy
        - For example, a 34.04% return means \$100,000 would grow to \$134,040

    ---

    - **Win Rate (%)**: Percentage of trades that resulted in a profit
        - Calculation: (Number of Profitable Trades / Total Trades) * 100
        - Shows how often the strategy makes winning trades
        - A win rate above 50% indicates more winning trades than losing trades

    ---

    - **Total Trades**: Number of completed trades
        - Counts each completed buy and sell pair as one trade
        - Higher numbers indicate more active trading
        - Helps evaluate strategy frequency and transaction costs

    ---

    - **Max Drawdown (%)**: Largest peak-to-trough decline in portfolio value
        - Calculation: ((Peak Value - Lowest Value) / Peak Value) * 100
        - Measures the biggest historical loss from a peak
        - Important for understanding worst-case risk scenarios
    """)

if __name__ == "__main__":
    main()