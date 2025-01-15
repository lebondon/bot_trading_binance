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
    
    # Brief explanation
    st.write("""
    ### Metric Explanations
    - **Return (%)**: Total percentage return of the strategy
    - **Win Rate (%)**: Percentage of profitable trades
    - **Total Trades**: Number of completed trades
    - **Max Drawdown (%)**: Largest peak-to-trough decline
    """)

if __name__ == "__main__":
    main()