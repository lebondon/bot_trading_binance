import pandas as pd
import numpy as np
from pathlib import Path

def calculate_bollinger_bands(df, window=20, num_std=2):
    """
    Calculate Bollinger Bands for the price data.
    
    Parameters:
    - df: DataFrame with datetime and avg_price columns
    - window: Window size for moving average (default 20 periods)
    - num_std: Number of standard deviations (default 2)
    
    Returns:
    - DataFrame with middle, upper, and lower bands
    """
    # Sort by datetime to ensure correct calculation
    df = df.sort_values('datetime')
    
    # Calculate middle band (moving average)
    df['middle_band'] = df['avg_price'].rolling(window=window).mean()
    
    # Calculate standard deviation
    rolling_std = df['avg_price'].rolling(window=window).std()
    
    # Calculate upper and lower bands
    df['upper_band'] = df['middle_band'] + (rolling_std * num_std)
    df['lower_band'] = df['middle_band'] - (rolling_std * num_std)
    
    return df

def process_trade_data(file_path, window=20, num_std=2):
    """
    Process trade data and calculate Bollinger Bands.
    """
    print(f"Reading data from {file_path}")
    df = pd.read_parquet(file_path)
    
    print("\nInitial data shape:", df.shape)
    print("\nTime range:", df['datetime'].min(), "to", df['datetime'].max())
    
    # Calculate Bollinger Bands
    print(f"\nCalculating Bollinger Bands (window={window}, std={num_std})")
    df_with_bands = calculate_bollinger_bands(df, window=window, num_std=num_std)
    
    # Save results
    output_path = file_path.parent / "btcusdt_with_bands.parquet"
    df_with_bands.to_parquet(output_path, compression='zstd')
    
    print("\nResults Preview:")
    print(df_with_bands[['datetime', 'avg_price', 'middle_band', 
                        'upper_band', 'lower_band']].head(10))
    
    print("\nSummary Statistics:")
    print("Average Middle Band:", df_with_bands['middle_band'].mean())
    print("Average Upper Band:", df_with_bands['upper_band'].mean())
    print("Average Lower Band:", df_with_bands['lower_band'].mean())
    print("\nOutput saved to:", output_path)

if __name__ == "__main__":
    # Configure parameters
    BASE_DIR = r"C:\Users\filip\OneDrive\Desktop\binance hyst_data\zip"
    PARQUET_FILE = Path(BASE_DIR) / "btcusdt_trades_by_second.parquet"
    
    # Process data with 20-period window and 2 standard deviations
    process_trade_data(PARQUET_FILE, window=20, num_std=2)