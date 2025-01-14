import pandas as pd
import numpy as np
from pathlib import Path
import itertools
from datetime import datetime

def run_backtest(parquet_file):
    """Run backtesting on historical data using vectorized operations"""
    print("Loading data...")
    # Read and resample data to 1-minute intervals to reduce noise
    df = pd.read_parquet(parquet_file)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.set_index('datetime')
    df = df.resample('1T').agg({
        'avg_price': 'last',
        'volume': 'sum',
        'trade_count': 'sum'
    }).dropna()
    
    print("Calculating indicators...")
    initial_capital = 100000
    
    # Calculate all indicators
    # Moving Average
    df['MA20'] = df['avg_price'].rolling(window=20).mean()
    df['MA_signal'] = (df['avg_price'] > df['MA20']).astype(int).diff()
    
    # RSI
    delta = df['avg_price'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['RSI_signal'] = ((df['RSI'] < 30).astype(int) - (df['RSI'] > 70).astype(int)).diff()
    
    # Bollinger Bands
    df['BB_middle'] = df['avg_price'].rolling(window=20).mean()
    df['BB_std'] = df['avg_price'].rolling(window=20).std()
    df['BB_upper'] = df['BB_middle'] + (2 * df['BB_std'])
    df['BB_lower'] = df['BB_middle'] - (2 * df['BB_std'])
    df['BB_signal'] = ((df['avg_price'] < df['BB_lower']).astype(int) - 
                      (df['avg_price'] > df['BB_upper']).astype(int)).diff()
    
    # MACD
    exp1 = df['avg_price'].ewm(span=12, adjust=False).mean()
    exp2 = df['avg_price'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_signal'] = (df['MACD'] > df['Signal_Line']).astype(int).diff()
    
    # Stochastic
    df['Low_14'] = df['avg_price'].rolling(window=14).min()
    df['High_14'] = df['avg_price'].rolling(window=14).max()
    df['%K'] = ((df['avg_price'] - df['Low_14']) / 
                (df['High_14'] - df['Low_14'])) * 100
    df['%D'] = df['%K'].rolling(window=3).mean()
    df['Stoch_signal'] = (((df['%K'] < 20) & (df['%D'] < 20)).astype(int) - 
                         ((df['%K'] > 80) & (df['%D'] > 80)).astype(int)).diff()
    
    print("Running strategy backtests...")
    
    def backtest_strategy(signal_col):
        position = 0
        capital = initial_capital
        trades = []
        equity_curve = [initial_capital]
        entry_price = 0
        
        for idx, row in df.iterrows():
            if pd.isna(row[signal_col]):
                equity_curve.append(equity_curve[-1])
                continue
                
            price = row['avg_price']
            
            # Buy signal
            if row[signal_col] == 1 and position == 0:
                position = capital / price
                entry_price = price
                capital = 0
                trades.append({
                    'type': 'buy',
                    'price': price,
                    'date': idx
                })
            
            # Sell signal
            elif row[signal_col] == -1 and position > 0:
                capital = position * price
                trades.append({
                    'type': 'sell',
                    'price': price,
                    'date': idx,
                    'return': (price - entry_price) / entry_price * 100
                })
                position = 0
            
            equity_curve.append(capital + (position * price))
        
        # Calculate metrics
        if trades:
            winning_trades = sum(1 for t in trades if t.get('return', 0) > 0)
            win_rate = (winning_trades / (len(trades) // 2)) * 100
        else:
            win_rate = 0
            
        # Calculate max drawdown
        peak = equity_curve[0]
        max_dd = 0
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100
            max_dd = max(max_dd, dd)
        
        final_return = ((equity_curve[-1] - initial_capital) / initial_capital * 100)
        
        return {
            'Final Return': final_return,
            'Win Rate': win_rate,
            'Total Trades': len(trades) // 2,
            'Max Drawdown': max_dd,
            'Equity Curve': equity_curve,
            'Trades': trades
        }
    
    # Process each strategy
    strategies = {
        'Moving Average': 'MA_signal',
        'RSI': 'RSI_signal',
        'Bollinger Bands': 'BB_signal',
        'MACD': 'MACD_signal',
        'Stochastic': 'Stoch_signal'
    }
    
    results = {}
    for strategy_name, signal_col in strategies.items():
        print(f"Processing {strategy_name} strategy...")
        results[strategy_name] = backtest_strategy(signal_col)
    
    return results

def calculate_additional_metrics(strategy_results):
    """Calculate additional performance metrics"""
    equity_curve = np.array(strategy_results['Equity Curve'])
    returns = np.diff(equity_curve) / equity_curve[:-1]
    
    if len(returns) > 0:
        # Daily metrics (assuming minute data)
        daily_returns = returns.reshape(-1, 1440).sum(axis=1)
        
        sharpe_ratio = np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252) if np.std(daily_returns) > 0 else 0
        
        positive_returns = daily_returns[daily_returns > 0]
        negative_returns = daily_returns[daily_returns < 0]
        profit_factor = abs(np.sum(positive_returns)) / abs(np.sum(negative_returns)) if len(negative_returns) > 0 else np.inf
        
        return {
            'sharpe_ratio': sharpe_ratio,
            'profit_factor': profit_factor,
            'var': np.percentile(daily_returns, 5),
            'expected_shortfall': np.mean(daily_returns[daily_returns < np.percentile(daily_returns, 5)]),
            'max_consecutive_losses': max(len(list(g)) for k, g in itertools.groupby(daily_returns < 0) if k),
            'avg_trade_duration': f"{len(returns) // len(strategy_results['Trades']) if strategy_results['Trades'] else 0} minutes"
        }
    return {
        'sharpe_ratio': 0,
        'profit_factor': 0,
        'var': 0,
        'expected_shortfall': 0,
        'max_consecutive_losses': 0,
        'avg_trade_duration': 'N/A'
    }

def print_strategy_summary(results):
    """Print a summary of all strategy results"""
    print("\nStrategy Performance Summary:")
    print("=" * 80)
    print(f"{'Strategy':<20} {'Return %':<12} {'Win Rate %':<12} {'Total Trades':<12} {'Max DD %':<12}")
    print("-" * 80)
    
    for strategy_name, metrics in results.items():
        print(f"{strategy_name:<20} "
              f"{metrics['Final Return']:>10.2f}% "
              f"{metrics['Win Rate']:>10.2f}% "
              f"{metrics['Total Trades']:>10} "
              f"{metrics['Max Drawdown']:>10.2f}%")

def save_backtesting_results(results, output_path):
    """Save backtesting results in a format suitable for the display page"""
    strategies_data = []
    
    for strategy_name, strategy_results in results.items():
        additional_metrics = calculate_additional_metrics(strategy_results)
        
        strategies_data.append({
            'strategy': strategy_name,
            'returns': strategy_results['Final Return'],
            'win_rate': strategy_results['Win Rate'],
            'total_trades': strategy_results['Total Trades'],
            'max_drawdown': strategy_results['Max Drawdown'],
            'equity_curve': strategy_results['Equity Curve'],
            **additional_metrics
        })
    
    results_df = pd.DataFrame(strategies_data)
    results_df.to_parquet(output_path, compression='gzip')
    print(f"\nResults saved to {output_path}")

if __name__ == "__main__":
    # Configure paths
    BASE_DIR = r"C:\Users\filip\OneDrive\Desktop\binance hyst_data\zip"
    PARQUET_FILE = Path(BASE_DIR) / "btcusdt_trades_by_second.parquet"
    
    # Run backtest
    results = run_backtest(PARQUET_FILE)
    
    # Print summary
    print_strategy_summary(results)
    
    # Save results
    output_path = Path(BASE_DIR) / "backtesting_results.parquet"
    save_backtesting_results(results, output_path)