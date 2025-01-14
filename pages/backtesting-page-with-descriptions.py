import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import numpy as np

# Dictionary of metric descriptions
METRIC_DESCRIPTIONS = {
    'Return (%)': """
        The total percentage return of the strategy over the testing period.
        Example: A return of 20% means $100 would have grown to $120.
    """,
    
    'Win Rate (%)': """
        The percentage of trades that were profitable.
        Example: A 60% win rate means 6 out of 10 trades made money.
    """,
    
    'Total Trades': """
        The total number of completed trades (both buy and sell) during the testing period.
        More trades generally mean more active strategy.
    """,
    
    'Max Drawdown (%)': """
        The largest peak-to-trough decline in the portfolio value.
        Example: A 20% max drawdown means the portfolio at some point declined 20% from its peak value.
    """,
    
    'Sharpe Ratio': """
        A measure of risk-adjusted returns. Higher is better.
        - Below 1: Poor risk-adjusted returns
        - 1-2: Acceptable
        - Above 2: Excellent
        Example: A Sharpe ratio of 1.5 means the strategy provides good returns for its level of risk.
    """,
    
    'Profit Factor': """
        The ratio of gross profits to gross losses.
        - Below 1: Strategy is losing money
        - 1-2: Moderately profitable
        - Above 2: Highly profitable
        Example: A profit factor of 1.5 means for every $1 lost, the strategy made $1.50 in profits.
    """,
    
    'Average Trade Duration': """
        The average time between opening and closing a trade.
        Helps understand if it's a short-term or long-term strategy.
    """,
    
    'Value at Risk (5%)': """
        The maximum loss expected with 95% confidence over a trading day.
        Example: A VaR of -2% means there's a 95% chance you won't lose more than 2% in a day.
    """,
    
    'Expected Shortfall': """
        The average loss when losses exceed the Value at Risk.
        Helps understand the severity of worst-case scenarios.
    """,
    
    'Maximum Consecutive Losses': """
        The longest streak of losing trades.
        Helps understand the worst drawdown in terms of trade count.
    """
}

def main():
    st.title("📊 Backtesting Results Analysis")
    st.markdown("""
        This page shows the historical performance analysis of different trading strategies 
        applied to BTC/USDT trading data from January 2024 to March 2024.
    """)
    
    # Add expandable section explaining trading metrics
    with st.expander("ℹ️ Understanding Trading Metrics"):
        st.markdown("""
        ### Key Performance Metrics Explained
        
        #### Return Metrics
        - **Total Return (%)**: The overall profit or loss as a percentage of initial investment
        - **Win Rate (%)**: The percentage of trades that were profitable
        - **Profit Factor**: Ratio of total profits to total losses
        
        #### Risk Metrics
        - **Max Drawdown (%)**: Largest peak-to-trough decline
        - **Sharpe Ratio**: Risk-adjusted return measure
        - **Value at Risk**: Potential loss in worst 5% of cases
        
        #### Trading Activity
        - **Total Trades**: Number of completed trades
        - **Average Trade Duration**: Typical length of each trade
        - **Maximum Consecutive Losses**: Longest streak of losing trades
        """)
    
    # Load results
    try:
        results_path = Path(r"C:\Users\filip\OneDrive\Desktop\binance hyst_data\zip\backtesting_results.parquet")
        results = pd.read_parquet(results_path)
        
        # Overview Section
        st.header("Strategy Performance Overview")
        col1, col2, col3 = st.columns(3)
        
        # Find best performing strategy
        best_strategy = results.loc[results['returns'].idxmax(), 'strategy']
        best_return = results.loc[results['returns'].idxmax(), 'returns']
        
        # Find most consistent strategy
        most_consistent = results.loc[results['win_rate'].idxmax(), 'strategy']
        best_win_rate = results.loc[results['win_rate'].idxmax(), 'win_rate']
        
        # Find lowest drawdown strategy
        safest_strategy = results.loc[results['max_drawdown'].idxmin(), 'strategy']
        lowest_drawdown = results.loc[results['max_drawdown'].idxmin(), 'max_drawdown']
        
        with col1:
            st.metric("Best Performer", 
                     f"{best_strategy}",
                     f"{best_return:.2f}%")
            st.caption("Strategy with highest total return")
            
        with col2:
            st.metric("Most Consistent", 
                     f"{most_consistent}",
                     f"{best_win_rate:.2f}% Win Rate")
            st.caption("Strategy with highest percentage of winning trades")
            
        with col3:
            st.metric("Safest Strategy", 
                     f"{safest_strategy}",
                     f"{lowest_drawdown:.2f}% Max DD")
            st.caption("Strategy with smallest maximum drawdown")
        
        # Detailed Performance Table
        st.header("Detailed Performance Metrics")
        st.markdown("""
            Hover over column headers for detailed explanations of each metric.
        """)
        
        performance_df = results[['strategy', 'returns', 'win_rate', 'total_trades', 'max_drawdown']].copy()
        performance_df.columns = ['Strategy', 'Return (%)', 'Win Rate (%)', 'Total Trades', 'Max Drawdown (%)']
        
        # Create tooltips for column headers
        formatted_df = performance_df.style.format({
            'Return (%)': '{:.2f}',
            'Win Rate (%)': '{:.2f}',
            'Total Trades': '{:,.0f}',
            'Max Drawdown (%)': '{:.2f}'
        }).set_tooltips({
            'Return (%)': METRIC_DESCRIPTIONS['Return (%)'],
            'Win Rate (%)': METRIC_DESCRIPTIONS['Win Rate (%)'],
            'Total Trades': METRIC_DESCRIPTIONS['Total Trades'],
            'Max Drawdown (%)': METRIC_DESCRIPTIONS['Max Drawdown (%)']
        })
        
        st.dataframe(formatted_df)
        
        # Equity Curves Comparison
        st.header("Strategy Equity Curves")
        st.markdown("""
            This chart shows how $100,000 would have grown over time with each strategy.
            - Steeper upward slopes indicate stronger performance
            - Downward slopes show periods of losses
            - Flatter sections indicate periods of sideways trading
        """)
        
        fig = go.Figure()
        colors = ['rgb(67, 133, 245)', 'rgb(80, 200, 120)', 'rgb(245, 154, 67)', 
                 'rgb(220, 67, 245)', 'rgb(245, 67, 67)']
        
        for (_, row), color in zip(results.iterrows(), colors):
            fig.add_trace(go.Scatter(
                y=row['equity_curve'],
                name=row['strategy'],
                line=dict(color=color),
                hovertemplate="Value: $%{y:,.2f}<extra></extra>"
            ))
        
        fig.update_layout(
            title="Strategy Performance Over Time",
            xaxis_title="Time Period",
            yaxis_title="Portfolio Value ($)",
            hovermode="x unified",
            template="plotly_dark",
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Strategy Analysis Section
        st.header("Individual Strategy Analysis")
        selected_strategy = st.selectbox(
            "Select a strategy to analyze",
            results['strategy'].tolist()
        )
        
        strategy_data = results[results['strategy'] == selected_strategy].iloc[0]
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Performance Metrics")
            metrics = {
                'Total Return': f"{strategy_data['returns']:.2f}%",
                'Win Rate': f"{strategy_data['win_rate']:.2f}%",
                'Number of Trades': f"{strategy_data['total_trades']:,.0f}",
                'Maximum Drawdown': f"{strategy_data['max_drawdown']:.2f}%",
                'Sharpe Ratio': f"{strategy_data['sharpe_ratio']:.2f}",
                'Profit Factor': f"{strategy_data['profit_factor']:.2f}",
                'Average Trade Duration': strategy_data['avg_trade_duration']
            }
            
            for metric, value in metrics.items():
                st.metric(metric, value)
                if metric in METRIC_DESCRIPTIONS:
                    st.caption(METRIC_DESCRIPTIONS[metric])
        
        with col2:
            st.subheader("Strategy Explanation")
            strategy_explanations = {
                'Moving Average': {
                    'Description': """
                        Uses a 20-period moving average to identify trends and generate trading signals.
                    """,
                    'Entry Rules': """
                        - Buy when price crosses above the moving average
                        - Sell when price crosses below the moving average
                    """,
                    'Best For': """
                        - Trending markets
                        - Longer-term trading
                        - Markets with clear directional movement
                    """,
                    'Limitations': """
                        - Can generate false signals in choppy markets
                        - May be late to enter and exit trends
                        - Performs poorly in sideways markets
                    """
                },
                'RSI': {
                    'Description': """
                        Uses the Relative Strength Index to identify overbought and oversold conditions.
                    """,
                    'Entry Rules': """
                        - Buy when RSI drops below 30 (oversold)
                        - Sell when RSI rises above 70 (overbought)
                    """,
                    'Best For': """
                        - Range-bound markets
                        - Markets with regular price oscillations
                        - Counter-trend trading
                    """,
                    'Limitations': """
                        - Can give premature signals in strong trends
                        - May miss extended trends
                        - Requires careful risk management
                    """
                },
                'Bollinger Bands': {
                    'Description': """
                        Uses standard deviation-based bands to identify price extremes.
                    """,
                    'Entry Rules': """
                        - Buy when price touches lower band
                        - Sell when price touches upper band
                    """,
                    'Best For': """
                        - Volatile markets
                        - Mean reversion trading
                        - Markets with defined ranges
                    """,
                    'Limitations': """
                        - Can be risky in strong trends
                        - Requires careful position sizing
                        - May generate too many signals in volatile markets
                    """
                },
                'MACD': {
                    'Description': """
                        Uses Moving Average Convergence Divergence to identify momentum shifts.
                    """,
                    'Entry Rules': """
                        - Buy when MACD crosses above signal line
                        - Sell when MACD crosses below signal line
                    """,
                    'Best For': """
                        - Trending markets
                        - Momentum trading
                        - Identifying trend reversals
                    """,
                    'Limitations': """
                        - Can be delayed in fast-moving markets
                        - May generate false signals
                        - Less effective in ranging markets
                    """
                },
                'Stochastic': {
                    'Description': """
                        Uses the Stochastic Oscillator to identify potential reversals.
                    """,
                    'Entry Rules': """
                        - Buy when %K crosses above %D in oversold territory
                        - Sell when %K crosses below %D in overbought territory
                    """,
                    'Best For': """
                        - Range-bound markets
                        - Identifying reversals
                        - Short-term trading
                    """,
                    'Limitations': """
                        - Can give false signals in trends
                        - Requires confirmation from other indicators
                        - May generate many signals
                    """
                }
            }
            
            explanation = strategy_explanations[selected_strategy]
            st.markdown("#### Description")
            st.markdown(explanation['Description'])
            st.markdown("#### Entry Rules")
            st.markdown(explanation['Entry Rules'])
            st.markdown("#### Best Used For")
            st.markdown(explanation['Best For'])
            st.markdown("#### Limitations")
            st.markdown(explanation['Limitations'])
        
        # Risk Analysis
        st.header("Risk Analysis")
        st.markdown("""
            Understanding the risk characteristics of a trading strategy is crucial for proper position sizing and risk management.
        """)
        
        risk_metrics = pd.DataFrame({
            'Metric': ['Value at Risk (5%)', 'Expected Shortfall', 'Maximum Consecutive Losses'],
            'Value': [
                f"{strategy_data['var']:.2f}%",
                f"{strategy_data['expected_shortfall']:.2f}%",
                f"{strategy_data['max_consecutive_losses']}"
            ],
            'Description': [
                METRIC_DESCRIPTIONS['Value at Risk (5%)'],
                METRIC_DESCRIPTIONS['Expected Shortfall'],
                METRIC_DESCRIPTIONS['Maximum Consecutive Losses']
            ]
        })
        st.table(risk_metrics)
        
    except Exception as e:
        st.error(f"Error loading backtesting results: {str(e)}")
        st.info("Please ensure the backtesting analysis has been run and results are saved.")

if __name__ == "__main__":
    st.set_page_config(
        page_title="Trading Strategy Backtesting Results",
        page_icon="📊",
        layout="wide"
    )
    main()