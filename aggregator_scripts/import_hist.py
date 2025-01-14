import requests
import zipfile
import io
import pandas as pd
from datetime import datetime, timedelta

def download_binance_data(symbol, date_str):
    # Construct URL
    base_url = "https://data.binance.vision/data/spot/daily/aggTrades"
    file_name = f"{symbol}-aggTrades-{date_str}.zip"
    url = f"{base_url}/{symbol}/{file_name}"
    
    # Download file
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for bad status codes
        
        # Extract zip content
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
            # The CSV file will have the same name as the zip without .zip
            csv_filename = file_name.replace('.zip', '.csv')
            with zip_file.open(csv_filename) as csv_file:
                # Read CSV
                df = pd.read_csv(csv_file, 
                               names=['agg_trade_id', 'price', 'quantity', 
                                     'first_trade_id', 'last_trade_id', 
                                     'timestamp', 'is_buyer_maker', 
                                     'is_best_match'])
                
                # Convert timestamp to datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                return df
                
    except requests.exceptions.RequestException as e:
        print(f"Error downloading data: {e}")
        return None

# Example usage
symbol = "BTCUSDT"
date = datetime.now() - timedelta(days=1)  # Yesterday's data
date_str = date.strftime('%Y-%m-%d')
df = download_binance_data(symbol, date_str)

if df is not None:
    print(f"Downloaded {len(df)} records")
    print(df.head())