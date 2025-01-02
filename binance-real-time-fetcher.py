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
        # Use current directory
        self.save_dir = Path.cwd()
        self.last_save_time = time.time()
        self.save_interval = 10
        self.new_data_buffer = []
        self.buffer_lock = threading.Lock()
        self.ws = None
        self.is_connected = False
        self.last_price = None
        self.start_time = time.time()
        self.trade_count = 0

    def get_parquet_path(self, symbol, date):
        return self.save_dir / f"{symbol}_{date.strftime('%Y%m%d')}.parquet"

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            
            timestamp = pd.to_datetime(data['E'], unit='ms')
            price = float(data['p'])
            volume = float(data['q'])
            
            # Add to buffer
            with self.buffer_lock:
                self.new_data_buffer.append([timestamp, price, volume])
            
            # Update trade statistics
            self.trade_count += 1
            
            # Print update (only price updates, no SMA or other calculations)
            sys.stdout.write("\033[K")  # Clear line
            print(f"\rPrice: ${price:,.2f} | Volume: {volume:.4f} | Total Trades: {self.trade_count:,}", end='')
            
            # Save data if interval elapsed
            current_time = time.time()
            if current_time - self.last_save_time >= self.save_interval:
                self.save_to_parquet()
                self.last_save_time = current_time

        except Exception as e:
            print(f"\nError processing message: {e}")

    def save_to_parquet(self):
        if not self.new_data_buffer:
            return

        with self.buffer_lock:
            buffer_data = self.new_data_buffer.copy()
            self.new_data_buffer = []

        if buffer_data:
            new_df = pd.DataFrame(buffer_data, columns=['timestamp', 'price', 'volume'])
            today = datetime.now().date()
            parquet_path = self.get_parquet_path(self.symbol, today)

            try:
                if parquet_path.exists():
                    existing_df = pd.read_parquet(parquet_path)
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                else:
                    combined_df = new_df

                combined_df.to_parquet(parquet_path, index=False)
                print(f"\nSaved {len(buffer_data):,} new records to {parquet_path}")
                
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
