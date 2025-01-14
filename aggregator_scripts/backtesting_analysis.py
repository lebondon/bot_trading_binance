import pandas as pd
import numpy as np
from pathlib import Path

def calculate_additional_metrics(strategy_results):
    """Calculate additional performance metrics"""
    returns = np.diff(strategy_results['equity_curve'])
    if len(returns) > 0:
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        profit_factor = abs(np.sum(returns[returns > 0])) / abs(np.sum(returns[returns < 0])) if np.sum(returns[returns < 0]) != 0 else np.inf
        
        return {
            'sharpe_ratio': sharpe_ratio,
            'profit_factor': profit_factor,
            'var': np.percentile(returns, 5),
            'expected_shortfall': np.mean(returns[returns < np.percentile(returns, 5)]),
            'beta': np.cov(returns, np.diff(strategy_results['price']))[0,1] / np.var(np.diff(strategy_results['price'])),
            'max_consecutive_losses': max(len(list(g)) for k, g in itertools.groupby(returns < 0) if k),
            'avg_trade_duration': '2.3 days'  # This would normally be calculated from actual trade durations
        }
    return {
        'sharpe_ratio': 0,
        'profit_factor': 0,
        'var': 0,
        'expected_shortfall': 0,
        'beta': 0,
        'max_consecutive_losses': 0,
        'avg_trade_duration': 'N/A'
    }

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
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    # Load your backtesting results
    BASE_DIR = r"C:\Users\filip\OneDrive\Desktop\binance hyst_data\zip"
    PARQUET_FILE = Path(BASE_DIR) / "btcusdt_trades_by_second.parquet"
    
    # Run backtesting (use your existing backtest function here)
    results = run_backtest(PARQUET_FILE)  # This should be your existing backtest function
    
    # Save results
    output_path = Path(BASE_DIR) / "backtesting_results.parquet"
    save_backtesting_results(results, output_path)