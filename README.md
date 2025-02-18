# 🚀 Crypto Trading Simulator

A real-time cryptocurrency trading simulator built with Streamlit that allows users to test different trading strategies using live Bitcoin (BTC) price data from Binance.

## 🌟 Features

- Real-time BTC/USDT price tracking
- Multiple trading strategies:
  - Moving Average (MA)
  - Relative Strength Index (RSI)
  - Bollinger Bands
  - MACD (Moving Average Convergence Divergence)
  - Stochastic Oscillator
- Live portfolio tracking
- Interactive price charts with technical indicators
- Detailed transaction history
- Performance metrics and strategy analytics
- Backtesting results for strategy comparison

## 📊 Trading Strategies

### Moving Average (MA)
- Buy Signal: Price crosses above moving average
- Sell Signal: Price crosses below moving average
- Best For: Trending markets

### RSI (Relative Strength Index)
- Buy Signal: RSI below 30 (oversold)
- Sell Signal: RSI above 70 (overbought)
- Best For: Range-bound markets

### Bollinger Bands
- Buy Signal: Price touches lower band
- Sell Signal: Price touches upper band
- Best For: Volatile markets

### MACD
- Buy Signal: MACD line crosses above signal line
- Sell Signal: MACD line crosses below signal line
- Best For: Trending markets with momentum

### Stochastic Oscillator
- Buy Signal: %K crosses above %D (below 20)
- Sell Signal: %K crosses below %D (above 80)
- Best For: Range-bound markets

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/crypto-trading-simulator.git
cd crypto-trading-simulator
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## 🚀 Usage

1. Start the main application:
```bash
streamlit run simulator.py
```

2. View backtesting results:
```bash
streamlit run pages/backtesting\ results.py
```

3. In the web interface:
   - Select your preferred trading strategy
   - Adjust the investment percentage per trade
   - Monitor real-time performance
   - View transaction history and metrics

## 📈 Backtesting Results

Strategy performance based on historical data (Jan 2024 - Mar 2024):

| Strategy           | Return (%) | Win Rate (%) | Total Trades | Max Drawdown (%) |
|-------------------|------------|--------------|--------------|------------------|
| RSI               | 72.66      | 62.8         | 95          | -9.4            |
| Moving Average    | 34.04      | 55.3         | 120         | -15.2           |
| Stochastic        | 28.76      | 63.67        | 140         | -16.2           |
| MACD              | 27.25      | 52.4         | 110         | -14.8           |
| Bollinger Bands   | 21.40      | 48.9         | 150         | -18.6           |

## ⚠️ Disclaimer

This simulator is for educational purposes only. Cryptocurrency trading involves substantial risk of loss. Past performance of these trading strategies does not guarantee future results.

## 🔧 Dependencies

Major dependencies include:
- streamlit==1.41.1
- plotly==5.24.1
- pandas==2.2.3
- numpy==2.2.1
- requests==2.32.3

For a complete list of dependencies, see `requirements.txt`.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
