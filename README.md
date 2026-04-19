# Algorithmic Trading Signal Dashboard

A real-time algorithmic trading dashboard powered by live Yahoo Finance data — technical indicators, strategy backtesting, and risk analysis for any stock ticker.

**[Live Demo](https://trading-signals-mrj72xnukv9senvhsbl6r5.streamlit.app)**

---

## Features

### 📊 Market Overview
- Live price, RSI, Volume, 52W High/Low
- Candlestick chart with SMA 20 and SMA 50
- Recent BUY and SELL signal table

### 📉 Technical Indicators
- RSI with overbought/oversold zones
- MACD with signal line and histogram
- Bollinger Bands with price overlay

### 🧪 Backtest Strategy
- MA Crossover strategy (SMA 20 / SMA 50) vs Buy & Hold
- Total return, annualized return, Sharpe ratio
- Max drawdown, win rate, final portfolio value
- Equity curve comparison chart
- Full trade log

### ⚖️ Risk Analysis
- Value at Risk (VaR) with adjustable confidence level
- Daily returns distribution histogram
- Rolling 30-day annualized volatility
- Drawdown chart

---

## Tech Stack

| Layer | Tools |
|---|---|
| Data | Yahoo Finance (yfinance) |
| Data Processing | Pandas, NumPy |
| Visualization | Plotly |
| App Framework | Streamlit |
| Deployment | Streamlit Cloud |

---

## Run Locally

    git clone https://github.com/Karthik-Mudenahalli-Ashoka/trading-signals.git
    cd trading-signals
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    streamlit run app.py

---

## Project Structure

    trading-signals/
    ├── app.py
    ├── requirements.txt
    ├── .python-version
    └── utils/
        ├── __init__.py
        ├── signals.py      # Technical indicators
        └── backtest.py     # Strategy backtesting