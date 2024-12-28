import requests
import pandas as pd
from datetime import datetime
import time

def fetch_binance_data(symbol, interval, start_time, end_time=None, limit=1000):
    """
    Fetch historical kline/candlestick data from Binance public API
    
    Parameters:
    symbol (str): Trading pair symbol (e.g., 'BTCUSDT')
    interval (str): Kline interval (e.g., '1h', '1d', '1m')
    start_time (str): Start time in 'YYYY-MM-DD' format
    end_time (str): End time in 'YYYY-MM-DD' format (optional)
    limit (int): Number of records to fetch (max 1000)
    
    Returns:
    pandas.DataFrame: Historical data with OHLCV values
    """
    # Convert dates to timestamps
    start_ts = int(datetime.strptime(start_time, '%Y-%m-%d').timestamp() * 1000)
    if end_time:
        end_ts = int(datetime.strptime(end_time, '%Y-%m-%d').timestamp() * 1000)
    else:
        end_ts = int(time.time() * 1000)
    
    # Binance API endpoint
    base_url = "https://api.binance.com/api/v3/klines"
    
    # Parameters for the request
    params = {
        'symbol': symbol.upper(),
        'interval': interval,
        'startTime': start_ts,
        'endTime': end_ts,
        'limit': limit
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise exception for bad status codes
        
        # Convert response to DataFrame
        df = pd.DataFrame(response.json(), columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignored'
        ])
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Convert string values to float
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
            
        # Set timestamp as index
        df.set_index('timestamp', inplace=True)
        
        # Keep only essential columns
        return df[['open', 'high', 'low', 'close', 'volume']]
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Example usage
if __name__ == "__main__":
    # Example: Fetch BTC/USDT daily data for the last month
    data = fetch_binance_data(
        symbol='BTCUSDT',
        interval='1d',
        start_time='2024-01-01',
        end_time='2024-01-31'
    )
    
    if data is not None:
        print(data.head())