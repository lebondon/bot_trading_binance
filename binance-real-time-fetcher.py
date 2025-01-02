import websocket
import json
import pandas as pd
from datetime import datetime
import threading
import time
import os
from pathlib import Path
import sys

class BinanceRealtimeFetcher:
    def __init__(self):
        self.save_dir = Path.cwd()
        self.last_save_time = time.time()
        self.save_interval = 1
        self.current_second_data = []
        self.buffer_lock = threading.Lock()
        self.ws = None
        self.is_connected = False
        self.trade_count = 0

    def get_parquet_path(self, symbol, date):
        return self.save_dir / f"{symbol}_{date.strftime('%Y%m%d')}_1s.parquet"

    def aggregate_second_data(self, data_list):
        """Aggregate trade data into 1-second intervals"""
        if not data_list:
            return None
        
        df = pd.DataFrame(data_list, columns=['timestamp', 'price', 'volume'])
        # Round timestamp to seconds
        df['timestamp'] = df['timestamp'].dt.floor('S')
        
        # Aggregate by second
        agg_df = df.groupby('timestamp').agg({
            'price': 'mean',      # Average price in the second
            'volume': 'sum'       # Total volume in the second
        }).reset_index()
        
        return agg_df

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            
            timestamp = pd.to_datetime(data['E'], unit='ms')
            price = float(data['p'])
            volume = float(data['q'])
            
            with self.buffer_lock:
                self.current_second_data.append([timestamp, price, volume])
            
            self.trade_count += 1
            current_time = datetime.now().strftime('%H:%M:%S')
            
            # Print update
            sys.stdout.write("\033[K")
            print(f"\r[{current_time}] Price: ${price:,.2f} | Volume: {volume:.4f} | Total Trades: {self.trade_count:,}", end='')
            
            # Check if we should save
            current_time = time.time()
            if current_time - self.last_save_time >= self.save_interval:
                self.save_to_parquet()
                self.last_save_time = current_time

        except Exception as e:
            print(f"\nError processing message: {e}")

    def save_to_parquet(self):
        with self.buffer_lock:
            current_data = self.current_second_data.copy()
            self.current_second_data = []

        if current_data:
            try:
                # Aggregate the current second's data
                agg_df = self.aggregate_second_data(current_data)
                if agg_df is None or agg_df.empty:
                    return

                today = datetime.now().date()
                parquet_path = self.get_parquet_path(self.symbol, today)

                if parquet_path.exists():
                    existing_df = pd.read_parquet(parquet_path)
                    combined_df = pd.concat([existing_df, agg_df], ignore_index=True)
                    # Remove any duplicates based on timestamp
                    combined_df = combined_df.drop_duplicates(subset=['timestamp'], keep='last')
                    # Sort by timestamp
                    combined_df = combined_df.sort_values('timestamp')
                else:
                    combined_df = agg_df

                combined_df.to_parquet(parquet_path, index=False)
                save_time = datetime.now().strftime('%H:%M:%S')
                print(f"\r[{save_time}] Saved aggregated data for {len(agg_df)} seconds", end='')
                
            except Exception as e:
                print(f"\nError saving to parquet: {e}")

    def on_error(self, ws, error):
        print(f"\nWebSocket Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("\nWebSocket connection closed")
        self.is_connected = False
        self.save_to_parquet()

    def on_open(self, ws):
        print("\nConnected to Binance WebSocket")
        self.is_connected = True
        
        subscribe_message = {
            "method": "SUBSCRIBE",
            "params": [f"{self.symbol.lower()}@trade"],
            "id": 1
        }
        ws.send(json.dumps(subscribe_message))

    def start_streaming(self, symbol='btcusdt'):
        self.symbol = symbol
        print(f"Starting stream for {symbol.upper()}")
        print(f"Saving data to: {self.save_dir}")
        
        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp(
            f"wss://stream.binance.com:9443/ws",
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        
        self.ws_thread = threading.Thread(target=self.ws.run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()

        # Start periodic save thread
        self.save_thread = threading.Thread(target=self.periodic_save)
        self.save_thread.daemon = True
        self.save_thread.start()

    def periodic_save(self):
        while self.is_connected:
            time.sleep(self.save_interval)
            current_time = time.time()
            if current_time - self.last_save_time >= self.save_interval:
                self.save_to_parquet()
                self.last_save_time = current_time

    def stop_streaming(self):
        if self.ws:
            self.ws.close()
        if hasattr(self, 'ws_thread'):
            self.ws_thread.join()
        self.save_to_parquet()
        print("\nStream stopped and final data saved")

if __name__ == "__main__":
    try:
        fetcher = BinanceRealtimeFetcher()
        fetcher.start_streaming('btcusdt')  # Change symbol here if needed
        
        while True:
            if not fetcher.is_connected:
                print("Waiting for connection...")
                time.sleep(1)
            time.sleep(0.1)
                
    except KeyboardInterrupt:
        print("\nStopping the stream...")
        fetcher.stop_streaming()
