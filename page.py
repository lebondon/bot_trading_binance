import streamlit as st
import requests
from datetime import datetime
import time
import plotly.graph_objects as go
import numpy as np

# Function to get the current BTC/USDT price from Binance
def get_current_price():
    url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        data = response.json()
        return float(data['price'])  # Bitcoin price in USD
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching price: {e}")
        return None

# Function to calculate the Moving Average
def moving_average(prices, period=10):
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

# Function to calculate the RSI
def relative_strength_index(prices, period=14):
    if len(prices) < period + 1:  # Ensure enough data points for RSI calculation
        return None
    gains = 0
    losses = 0
    for i in range(1, period + 1):
        change = prices[-i] - prices[-i - 1]
        if change > 0:
            gains += change
        elif change < 0:
            losses += abs(change)
    
    avg_gain = gains / period
    avg_loss = losses / period
    
    if avg_loss == 0:
        return 100  # If there are no losses, RSI is 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# Function to calculate Bollinger Bands
def bollinger_bands(prices, period=20, num_std=2):
    if len(prices) < period:
        return None, None, None
    ma = np.convolve(prices, np.ones(period) / period, mode='valid')  # Moving average
    std = np.std(prices[-period:])
    upper_band = ma + (std * num_std)
    lower_band = ma - (std * num_std)
    return upper_band, ma, lower_band

# Function to calculate MACD
def macd(prices, short_period=12, long_period=26, signal_period=9):
    if len(prices) < long_period:
        return None, None
    short_ema = np.mean(prices[-short_period:])
    long_ema = np.mean(prices[-long_period:])
    macd_line = short_ema - long_ema
    signal_line = np.mean(prices[-signal_period:])
    return macd_line, signal_line

# Function to calculate Stochastic Oscillator
def stochastic_oscillator(prices, period=14, k_period=3, d_period=3):
    if len(prices) < period:
        return None, None
    low_min = min(prices[-period:])
    high_max = max(prices[-period:])
    k = 100 * ((prices[-1] - low_min) / (high_max - low_min))
    d = np.mean(prices[-k_period:])
    return k, d

# Base class for trading strategies
class TradingStrategy:
    def should_buy(self, prices, current_balance, investment_amount):
        raise NotImplementedError

    def should_sell(self, prices, current_position):
        raise NotImplementedError

# Moving Average Strategy
class MovingAverageStrategy(TradingStrategy):
    """
    The Moving Average (MA) strategy uses a simple moving average to determine buy/sell signals.
    - Buy Signal: When the current price crosses above the moving average.
    - Sell Signal: When the current price crosses below the moving average.
    This strategy works well in trending markets where prices move consistently in one direction.
    """
    def should_buy(self, prices, current_balance, investment_amount):
        ma = moving_average(prices)
        current_price = prices[-1]
        return ma and current_price > ma and current_balance >= investment_amount

    def should_sell(self, prices, current_position):
        ma = moving_average(prices)
        current_price = prices[-1]
        return ma and current_price < ma and current_position > 0

# RSI Strategy
class RSIStrategy(TradingStrategy):
    """
    The Relative Strength Index (RSI) strategy uses the RSI indicator to identify overbought/oversold conditions.
    - Buy Signal: When RSI is below 30 (oversold condition).
    - Sell Signal: When RSI is above 70 (overbought condition).
    This strategy works well in ranging markets where prices oscillate between overbought and oversold levels.
    """
    def should_buy(self, prices, current_balance, investment_amount):
        rsi = relative_strength_index(prices)
        return rsi and rsi < 30 and current_balance >= investment_amount

    def should_sell(self, prices, current_position):
        rsi = relative_strength_index(prices)
        return rsi and rsi > 70 and current_position > 0

# Bollinger Bands Strategy
class BollingerBandsStrategy(TradingStrategy):
    """
    The Bollinger Bands strategy uses volatility bands to identify buy/sell signals.
    - Buy Signal: When the price touches or crosses the lower band (oversold condition).
    - Sell Signal: When the price touches or crosses the upper band (overbought condition).
    This strategy works well in volatile markets where prices frequently touch the bands.
    """
    def should_buy(self, prices, current_balance, investment_amount):
        upper_band, _, lower_band = bollinger_bands(prices)
        current_price = prices[-1]
        return lower_band and current_price < lower_band and current_balance >= investment_amount

    def should_sell(self, prices, current_position):
        upper_band, _, _ = bollinger_bands(prices)
        current_price = prices[-1]
        return upper_band and current_price > upper_band and current_position > 0

# MACD Strategy
class MACDStrategy(TradingStrategy):
    """
    The Moving Average Convergence Divergence (MACD) strategy uses the MACD line and signal line for buy/sell signals.
    - Buy Signal: When the MACD line crosses above the signal line.
    - Sell Signal: When the MACD line crosses below the signal line.
    This strategy works well in trending markets where momentum shifts are significant.
    """
    def should_buy(self, prices, current_balance, investment_amount):
        macd_line, signal_line = macd(prices)
        return macd_line and signal_line and macd_line > signal_line and current_balance >= investment_amount

    def should_sell(self, prices, current_position):
        macd_line, signal_line = macd(prices)
        return macd_line and signal_line and macd_line < signal_line and current_position > 0

# Stochastic Oscillator Strategy
class StochasticOscillatorStrategy(TradingStrategy):
    """
    The Stochastic Oscillator strategy uses the %K and %D lines to identify overbought/oversold conditions.
    - Buy Signal: When %K crosses above %D and %K is below 20 (oversold condition).
    - Sell Signal: When %K crosses below %D and %K is above 80 (overbought condition).
    This strategy works well in ranging markets where prices oscillate between overbought and oversold levels.
    """
    def should_buy(self, prices, current_balance, investment_amount):
        k, d = stochastic_oscillator(prices)
        return k and d and k > d and k < 20 and current_balance >= investment_amount

    def should_sell(self, prices, current_position):
        k, d = stochastic_oscillator(prices)
        return k and d and k < d and k > 80 and current_position > 0

# Create the trading bot class
class TradingBot:
    def __init__(self, initial_balance, strategy):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.current_position = 0  # Amount of BTC owned
        self.entry_price = None  # Price at which the purchase was made
        self.transactions = []  # List to track transactions
        self.strategy = strategy
        self.price_history = []  # Price history for calculating indicators

    def simulate_trade(self, investment_amount):
        """Simulate a trade based on the selected strategy."""
        if len(self.price_history) < 2:  # Need at least 2 prices to calculate indicators
            return

        # Check if the buy/sell strategy should be applied
        if self.strategy.should_buy(self.price_history, self.current_balance, investment_amount):
            self.buy(self.price_history[-1], investment_amount)
        elif self.strategy.should_sell(self.price_history, self.current_position):
            self.sell(self.price_history[-1])

    def buy(self, price, investment_amount):
        """Execute a purchase."""
        quantity = investment_amount / price  # Amount of BTC bought
        self.current_balance -= investment_amount  # Deduct amount from account
        self.current_position += quantity  # Add the purchased BTC to balance
        self.entry_price = price
        self.transactions.append({
            'type': 'buy',
            'quantity': quantity,
            'price': price,
            'entry_price': price,  # Store the entry price for future reference
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # Print the alert
        st.success(f"Purchase made! BTC balance: {self.current_position:.6f} | USD balance: {self.current_balance:.2f}")

    def sell(self, price):
        """Execute a sale."""
        sale_amount = self.current_position * price
        self.current_balance += sale_amount
        self.transactions.append({
            'type': 'sell',
            'quantity': self.current_position,  # Record the quantity before resetting
            'price': price,
            'entry_price': self.entry_price,  # Include the entry price for profit calculation
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        self.current_position = 0  # Reset the position after recording the transaction
        st.success(f"Sale made! BTC balance: {self.current_position:.6f} | USD balance: {self.current_balance:.2f}")

    def get_portfolio(self):
        """Return the total balance in USD, considering the BTC balance."""
        if self.current_position > 0:
            current_price = get_current_price()  # Current BTC price
            return self.current_balance + self.current_position * current_price
        return self.current_balance

# Streamlit App
def main():
    # Set up the Streamlit page
    st.set_page_config(page_title="Crypto Trading Simulator", layout="wide")
    st.title("🚀 Crypto Trading Simulator")
    st.markdown("""
        This app simulates a cryptocurrency trading strategy using real-time Bitcoin (BTC) price data.
        Choose a strategy, set your investment amount, and see how your portfolio performs!
    """)

    # Sidebar for user inputs
    with st.sidebar:
        st.header("Settings")
        initial_balance = 100000  # Set initial balance to 100,000
        investment_percentage = st.slider("Investment Percentage per Trade (%)", min_value=1, max_value=100, value=10, step=1)
        investment_amount = (investment_percentage / 100) * initial_balance  # Dynamic investment amount
        strategy_choice = st.selectbox("Trading Strategy", [
            "Moving Average (MA)", 
            "Relative Strength Index (RSI)", 
            "Bollinger Bands", 
            "MACD", 
            "Stochastic Oscillator"
        ])
        
        # Display strategy description based on user selection
        if strategy_choice == "Moving Average (MA)":
            strategy = MovingAverageStrategy()
            st.markdown("""
                **Moving Average (MA) Strategy:**
                - **Buy Signal:** When the current price crosses above the moving average.
                - **Sell Signal:** When the current price crosses below the moving average.
                - **Works Well In:** Trending markets where prices move consistently in one direction.
            """)
        elif strategy_choice == "Relative Strength Index (RSI)":
            strategy = RSIStrategy()
            st.markdown("""
                **Relative Strength Index (RSI) Strategy:**
                - **Buy Signal:** When RSI is below 30 (oversold condition).
                - **Sell Signal:** When RSI is above 70 (overbought condition).
                - **Works Well In:** Ranging markets where prices oscillate between overbought and oversold levels.
            """)
        elif strategy_choice == "Bollinger Bands":
            strategy = BollingerBandsStrategy()
            st.markdown("""
                **Bollinger Bands Strategy:**
                - **Buy Signal:** When the price touches or crosses the lower band (oversold condition).
                - **Sell Signal:** When the price touches or crosses the upper band (overbought condition).
                - **Works Well In:** Volatile markets where prices frequently touch the bands.
            """)
        elif strategy_choice == "MACD":
            strategy = MACDStrategy()
            st.markdown("""
                **MACD Strategy:**
                - **Buy Signal:** When the MACD line crosses above the signal line.
                - **Sell Signal:** When the MACD line crosses below the signal line.
                - **Works Well In:** Trending markets where momentum shifts are significant.
            """)
        elif strategy_choice == "Stochastic Oscillator":
            strategy = StochasticOscillatorStrategy()
            st.markdown("""
                **Stochastic Oscillator Strategy:**
                - **Buy Signal:** When %K crosses above %D and %K is below 20 (oversold condition).
                - **Sell Signal:** When %K crosses below %D and %K is above 80 (overbought condition).
                - **Works Well In:** Ranging markets where prices oscillate between overbought and oversold levels.
            """)

        # Add a Reset button
        if st.button("Reset Simulation"):
            st.session_state.bot = TradingBot(initial_balance, strategy)
            st.session_state.prices = []
            st.session_state.timestamps = []
            st.success("Simulation reset successfully!")

    # Initialize the trading bot
    if 'bot' not in st.session_state:
        st.session_state.bot = TradingBot(initial_balance, strategy)
        st.session_state.prices = []
        st.session_state.timestamps = []

    # Display the current portfolio
    st.subheader("📊 Portfolio Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current BTC Balance", f"{st.session_state.bot.current_position:.6f} BTC")
    with col2:
        st.metric("Current USD Balance", f"${st.session_state.bot.current_balance:.2f}")
    with col3:
        portfolio_value = st.session_state.bot.get_portfolio()
        st.metric("Total Portfolio Value", f"${portfolio_value:.2f}")

    # Display Key Metrics and Performance Metrics in two columns
    st.subheader("📈 Metrics")
    col1, col2 = st.columns(2)

    with col1:
        # Key Metrics
        st.markdown("### Key Metrics")
        if len(st.session_state.prices) > 14:  # Ensure enough data for RSI calculation
            ma = moving_average(st.session_state.prices)
            rsi = relative_strength_index(st.session_state.prices)

            # Moving Average
            if ma:
                ma_color = "green" if st.session_state.prices[-1] > ma else "red"
                st.markdown(f"**Moving Average (10-period):** <span style='color:{ma_color};'>{ma:.2f}</span>", unsafe_allow_html=True)

            # RSI
            if rsi:
                rsi_color = "green" if rsi < 30 else "red" if rsi > 70 else "gray"
                st.markdown(f"**RSI (14-period):** <span style='color:{rsi_color};'>{rsi:.2f}</span>", unsafe_allow_html=True)
                if rsi < 30:
                    st.markdown("**Market Condition:** <span style='color:green;'>Oversold</span>", unsafe_allow_html=True)
                elif rsi > 70:
                    st.markdown("**Market Condition:** <span style='color:red;'>Overbought</span>", unsafe_allow_html=True)
                else:
                    st.markdown("**Market Condition:** <span style='color:gray;'>Neutral</span>", unsafe_allow_html=True)

    with col2:
        # Performance Metrics
        st.markdown("### Performance Metrics")
        if st.session_state.bot.transactions:
            total_profit = st.session_state.bot.get_portfolio() - initial_balance
            profitable_trades = sum(1 for t in st.session_state.bot.transactions if t['type'] == 'sell' and t['price'] > t['entry_price'])
            total_trades = sum(1 for t in st.session_state.bot.transactions if t['type'] == 'sell')
            win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
            st.metric("Total Profit/Loss", f"${total_profit:.2f}", delta_color="off")
            st.metric("Win Rate", f"{win_rate:.2f}%")
        else:
            st.info("No performance data available yet.")

    # Display the price chart
    st.subheader("📈 BTC Price Over Time")
    chart_placeholder = st.empty()

    # Placeholder for transaction history
    transaction_history_placeholder = st.empty()

    # Simulate trades and update the chart
    while True:
        # Fetch the current price
        current_price = get_current_price()
        if current_price is not None:
            st.session_state.prices.append(current_price)
            st.session_state.timestamps.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            # Update the bot's price history
            st.session_state.bot.price_history = st.session_state.prices

            # Calculate Bollinger Bands for the entire price history
            if len(st.session_state.prices) >= 20:  # Ensure enough data for Bollinger Bands
                upper_band, ma, lower_band = bollinger_bands(st.session_state.prices)
            else:
                upper_band, ma, lower_band = None, None, None

            # Update the chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=st.session_state.timestamps, y=st.session_state.prices, mode='lines', name='BTC Price'))
            
            # Add Bollinger Bands to the chart
            if upper_band is not None and ma is not None and lower_band is not None:
                fig.add_trace(go.Scatter(x=st.session_state.timestamps[-len(upper_band):], y=upper_band, mode='lines', name='Upper Band'))
                fig.add_trace(go.Scatter(x=st.session_state.timestamps[-len(ma):], y=ma, mode='lines', name='Moving Average'))
                fig.add_trace(go.Scatter(x=st.session_state.timestamps[-len(lower_band):], y=lower_band, mode='lines', name='Lower Band'))
            
            fig.update_layout(
                title="BTC Price Trend Over Time",
                xaxis_title="Time",
                yaxis_title="Price in USD",
                template="plotly_dark"
            )
            chart_placeholder.plotly_chart(fig, use_container_width=True)

            # Update transaction history
            with transaction_history_placeholder.container():
                st.subheader("📜 Transaction History")
                if st.session_state.bot.transactions:
                    st.table(st.session_state.bot.transactions)
                else:
                    st.info("No transactions yet.")

            # Simulate a trade
            st.session_state.bot.simulate_trade(investment_amount)

        # Wait for 1 second before the next update
        time.sleep(1)

# Run the Streamlit app
if __name__ == "__main__":
    main()