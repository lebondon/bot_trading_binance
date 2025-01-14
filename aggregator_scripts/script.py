import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import os

def process_trade_files(base_dir: str, start_date: datetime, end_date: datetime):
    """
    Process all trade files between start_date and end_date, aggregate by second
    and save as parquet.
    """
    all_data = []
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        folder_name = f"BTCUSDT-aggTrades-{date_str}"
        file_name = f"BTCUSDT-aggTrades-{date_str}.csv"
        file_path = Path(base_dir) / folder_name / file_name
        
        if file_path.exists():
            print(f"\nProcessing {date_str}...")
            try:
                # Read CSV
                df = pd.read_csv(file_path, header=None, 
                               names=["trade_id", "price", "quantity", "first_trade_id", 
                                     "last_trade_id", "timestamp", "is_buyer_maker", "is_best_match"])
                
                print(f"Raw data rows: {len(df):,}")
                
                # Convert timestamp from milliseconds to datetime
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
                
                # Create a second-level timestamp for grouping
                df['date_second'] = df['datetime'].dt.floor('S')
                
                unique_seconds = df['date_second'].nunique()
                print(f"Unique seconds in day: {unique_seconds:,}")
                
                # Group by second and aggregate
                df_agg = df.groupby('date_second').agg({
                    'trade_id': 'count',
                    'quantity': 'sum',
                    'price': 'mean',
                    'is_buyer_maker': 'sum'
                }).reset_index()
                
                # Rename columns
                df_agg.columns = ['datetime', 'trade_count', 'volume', 'avg_price', 'buy_trades']
                
                # Calculate sell trades
                df_agg['sell_trades'] = df_agg['trade_count'] - df_agg['buy_trades']
                
                print(f"Aggregated rows (unique seconds): {len(df_agg):,}")
                print(f"Time range: {df_agg['datetime'].min()} to {df_agg['datetime'].max()}")
                print(f"Total trades in period: {df_agg['trade_count'].sum():,}")
                
                all_data.append(df_agg)
                
            except Exception as e:
                print(f"Error processing {date_str}: {str(e)}")
        else:
            print(f"Warning: File not found: {file_path}")
        
        current_date += timedelta(days=1)
    
    if all_data:
        # Combine all dataframes
        final_df = pd.concat(all_data, ignore_index=True)
        
        # Sort by timestamp
        final_df = final_df.sort_values('datetime')
        
        # Save as parquet with compression
        output_path = Path(base_dir) / "btcusdt_trades_by_second.parquet"
        final_df.to_parquet(
            output_path,
            compression='zstd'
        )
        
        print(f"\nFinal Processing Summary")
        print("=" * 50)
        print(f"Total records (seconds): {len(final_df):,}")
        print(f"Total unique seconds: {final_df['datetime'].nunique():,}")
        print(f"Total trades processed: {final_df['trade_count'].sum():,}")
        print(f"Date range: {final_df['datetime'].min()} to {final_df['datetime'].max()}")
        print(f"Output saved to: {output_path}")
        
        # Display sample
        print("\nSample of aggregated data (first 5 rows):")
        print(final_df[['datetime', 'trade_count', 'volume', 
                       'avg_price', 'buy_trades', 'sell_trades']].head())
        
    else:
        print("No data was processed!")

if __name__ == "__main__":
    # Configure parameters
    BASE_DIR = r"C:\Users\filip\OneDrive\Desktop\binance hyst_data\zip"
    START_DATE = datetime(2024, 1, 1)
    END_DATE = datetime(2024, 3, 31)
    
    # Process files
    process_trade_files(BASE_DIR, START_DATE, END_DATE)