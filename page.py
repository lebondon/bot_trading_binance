import streamlit as st
import requests
from datetime import datetime
import time
import plotly.graph_objects as go
import asyncio

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
    if len(prices) < period:
        return None
    gains = 0
    losses = 0
    for i in range(1, period+1):
        change = prices[-i] - prices[-i-1]
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

# Base class for trading strategies
class TradingStrategy:
    def should_buy(self, prices, current_balance, investment_amount):
        raise NotImplementedError

    def should_sell(self, prices, current_position):
        raise NotImplementedError

# Moving Average Strategy
class MovingAverageStrategy(TradingStrategy):
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
    def should_buy(self, prices, current_balance, investment_amount):
        rsi = relative_strength_index(prices)
        return rsi and rsi < 30 and current_balance >= investment_amount

    def should_sell(self, prices, current_position):
        rsi = relative_strength_index(prices)
        return rsi and rsi > 70 and current_position > 0

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
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # Print the alert
        st.success(f"Purchase made! BTC balance: {self.current_position:.6f} | USD balance: {self.current_balance:.2f}")

    def sell(self, price):
        """Execute a sale."""
        sale_amount = self.current_position * price
        self.current_balance += sale_amount
        self.current_position = 0
        self.transactions.append({
            'type': 'sell',
            'quantity': self.current_position,
            'price': price,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
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
        initial_balance = st.number_input("Initial Balance (USD)", min_value=100.0, value=1000.0, step=100.0)
        investment_amount = st.number_input("Investment Amount per Trade (USD)", min_value=10.0, value=100.0, step=10.0)
        strategy_choice = st.selectbox("Trading Strategy", ["Moving Average (MA)", "Relative Strength Index (RSI)"])
        if strategy_choice == "Moving Average (MA)":
            strategy = MovingAverageStrategy()
        else:
            strategy = RSIStrategy()

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

    # Display the price chart
    st.subheader("📈 BTC Price Over Time")
    chart_placeholder = st.empty()

    # Simulate trades and update the chart
    while True:
        # Fetch the current price
        current_price = get_current_price()
        if current_price is not None:
            st.session_state.prices.append(current_price)
            st.session_state.timestamps.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            # Update the chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=st.session_state.timestamps, y=st.session_state.prices, mode='lines', name='BTC Price'))
            fig.update_layout(
                title="BTC Price Trend Over Time",
                xaxis_title="Time",
                yaxis_title="Price in USD",
                template="plotly_dark"
            )
            chart_placeholder.plotly_chart(fig, use_container_width=True)

            # Simulate a trade
            st.session_state.bot.simulate_trade(investment_amount)

        # Wait for 1 second before the next update
        time.sleep(1)

# Run the Streamlit app
if __name__ == "__main__":
    main()