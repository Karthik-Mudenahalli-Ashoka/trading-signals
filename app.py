"""
app.py — Algorithmic Trading Signal Dashboard
Main entry point. Handles data loading and sidebar navigation.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils import fetch_data, add_all_signals, generate_signal, run_backtest

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Trading Signal Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.title("📈 Trading Signals")
    st.markdown("---")

    page = st.radio(
        "Navigation",
        ["📊 Market Overview",
         "📉 Technical Indicators",
         "🧪 Backtest Strategy",
         "⚖️ Risk Analysis"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.subheader("⚙️ Settings")

    ticker = st.text_input("Stock Ticker", value="AAPL").upper().strip()

    period = st.selectbox(
        "Time Period",
        ["6mo", "1y", "2y", "5y"],
        index=1,
    )

    initial_capital = st.number_input(
        "Initial Capital ($)", value=10000, step=1000
    )

    st.markdown("---")
    st.caption("Data from Yahoo Finance · Built with Streamlit")

# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
@st.cache_data(show_spinner="Fetching market data...", ttl=3600)
def load(ticker, period):
    df = fetch_data(ticker, period=period)
    df = add_all_signals(df)
    df = generate_signal(df)
    return df

try:
    df = load(ticker, period)
except Exception as e:
    st.error(f"Could not load data for **{ticker}**. Check the ticker and try again.")
    st.stop()

# ─────────────────────────────────────────────
# PAGE: MARKET OVERVIEW
# ─────────────────────────────────────────────
if page == "📊 Market Overview":
    st.title(f"📊 {ticker} — Market Overview")
    st.markdown("---")

    # KPI cards
    latest      = df.iloc[-1]
    prev        = df.iloc[-2]
    price_change = latest["close"] - prev["close"]
    pct_change   = price_change / prev["close"] * 100

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Price",       f"${latest['close']:.2f}",  f"{pct_change:+.2f}%")
    k2.metric("RSI",         f"{latest['rsi']:.1f}",
              "Overbought" if latest["rsi"] > 70 else "Oversold" if latest["rsi"] < 30 else "Neutral")
    k3.metric("Volume",      f"{int(latest['volume']):,}")
    k4.metric("52W High",    f"${df['close'].max():.2f}")
    k5.metric("52W Low",     f"${df['close'].min():.2f}")

    st.markdown("---")

    # Candlestick chart
    st.subheader("🕯️ Price Chart with Moving Averages")
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.7, 0.3], vertical_spacing=0.05)

    fig.add_trace(go.Candlestick(
        x=df.index, open=df["open"], high=df["high"],
        low=df["low"], close=df["close"], name="Price",
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df.index, y=df["sma_20"], name="SMA 20",
        line=dict(color="#636EFA", width=1.5),
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df.index, y=df["sma_50"], name="SMA 50",
        line=dict(color="#EF553B", width=1.5),
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=df.index, y=df["volume"], name="Volume",
        marker_color="#AB63FA", opacity=0.5,
    ), row=2, col=1)

    fig.update_layout(
        height=550,
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", y=1.02),
        margin=dict(t=20, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Buy/Sell signals
    st.subheader("🚦 Latest Signals")
    buys  = df[df["signal"] == "BUY"].tail(5)
    sells = df[df["signal"] == "SELL"].tail(5)

    c1, c2 = st.columns(2)
    with c1:
        st.success("**Recent BUY Signals**")
        if len(buys) > 0:
            st.dataframe(buys[["close", "rsi", "macd", "signal"]].round(2),
                         use_container_width=True)
        else:
            st.write("No recent BUY signals")

    with c2:
        st.error("**Recent SELL Signals**")
        if len(sells) > 0:
            st.dataframe(sells[["close", "rsi", "macd", "signal"]].round(2),
                         use_container_width=True)
        else:
            st.write("No recent SELL signals")

# ─────────────────────────────────────────────
# PAGE: TECHNICAL INDICATORS
# ─────────────────────────────────────────────
elif page == "📉 Technical Indicators":
    st.title(f"📉 {ticker} — Technical Indicators")
    st.markdown("---")

    # RSI
    st.subheader("📊 RSI (Relative Strength Index)")
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(
        x=df.index, y=df["rsi"], name="RSI",
        line=dict(color="#636EFA", width=2),
    ))
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red",   annotation_text="Overbought (70)")
    fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold (30)")
    fig_rsi.update_layout(height=300, margin=dict(t=20, b=20))
    st.plotly_chart(fig_rsi, use_container_width=True)

    st.markdown("---")

    # MACD
    st.subheader("📊 MACD")
    fig_macd = make_subplots(rows=2, cols=1, shared_xaxes=True,
                              row_heights=[0.6, 0.4], vertical_spacing=0.05)
    fig_macd.add_trace(go.Scatter(
        x=df.index, y=df["macd"], name="MACD",
        line=dict(color="#636EFA", width=2),
    ), row=1, col=1)
    fig_macd.add_trace(go.Scatter(
        x=df.index, y=df["macd_signal"], name="Signal",
        line=dict(color="#EF553B", width=2),
    ), row=1, col=1)
    fig_macd.add_trace(go.Bar(
        x=df.index, y=df["macd_hist"], name="Histogram",
        marker_color=df["macd_hist"].apply(lambda x: "#00CC96" if x >= 0 else "#EF553B"),
    ), row=2, col=1)
    fig_macd.update_layout(height=380, margin=dict(t=20, b=20))
    st.plotly_chart(fig_macd, use_container_width=True)

    st.markdown("---")

    # Bollinger Bands
    st.subheader("📊 Bollinger Bands")
    fig_bb = go.Figure()
    fig_bb.add_trace(go.Scatter(
        x=df.index, y=df["bb_upper"], name="Upper Band",
        line=dict(color="gray", dash="dash"),
    ))
    fig_bb.add_trace(go.Scatter(
        x=df.index, y=df["bb_lower"], name="Lower Band",
        line=dict(color="gray", dash="dash"),
        fill="tonexty", fillcolor="rgba(100,100,100,0.1)",
    ))
    fig_bb.add_trace(go.Scatter(
        x=df.index, y=df["close"], name="Price",
        line=dict(color="#636EFA", width=2),
    ))
    fig_bb.add_trace(go.Scatter(
        x=df.index, y=df["bb_mid"], name="Middle Band",
        line=dict(color="#EF553B", dash="dot"),
    ))
    fig_bb.update_layout(height=380, margin=dict(t=20, b=20))
    st.plotly_chart(fig_bb, use_container_width=True)

# ─────────────────────────────────────────────
# PAGE: BACKTEST
# ─────────────────────────────────────────────
elif page == "🧪 Backtest Strategy":
    st.title(f"🧪 {ticker} — Backtest Strategy")
    st.markdown("MA Crossover Strategy (SMA 20 / SMA 50) vs Buy & Hold")
    st.markdown("---")

    result = run_backtest(df, initial_capital=initial_capital)
    s = result["strategy"]
    m = result["market"]
    eq = result["equity_curve"]

    # KPI comparison
    st.subheader("📊 Performance Comparison")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🤖 Strategy")
        st.metric("Total Return",     f"{s['total_return']}%")
        st.metric("Annualized Return",f"{s['ann_return']}%")
        st.metric("Sharpe Ratio",     f"{s['sharpe']}")
        st.metric("Max Drawdown",     f"{s['max_drawdown']}%")
        st.metric("Win Rate",         f"{s['win_rate']}%")
        st.metric("Final Value",      f"${s['final_value']:,.2f}")

    with col2:
        st.markdown("#### 📈 Buy & Hold")
        st.metric("Total Return",     f"{m['total_return']}%")
        st.metric("Annualized Return",f"{m['ann_return']}%")
        st.metric("Sharpe Ratio",     f"{m['sharpe']}")
        st.metric("Max Drawdown",     f"{m['max_drawdown']}%")
        st.metric("Win Rate",         f"{m['win_rate']}%")
        st.metric("Final Value",      f"${m['final_value']:,.2f}")

    st.markdown("---")

    # Equity curve
    st.subheader("📈 Equity Curve")
    fig_eq = go.Figure()
    fig_eq.add_trace(go.Scatter(
        x=eq.index, y=eq["strategy_equity"],
        name="Strategy", line=dict(color="#636EFA", width=2),
    ))
    fig_eq.add_trace(go.Scatter(
        x=eq.index, y=eq["market_equity"],
        name="Buy & Hold", line=dict(color="#EF553B", width=2),
    ))
    fig_eq.update_layout(
        height=380,
        yaxis_title="Portfolio Value ($)",
        margin=dict(t=20, b=20),
        legend=dict(orientation="h", y=1.02),
    )
    st.plotly_chart(fig_eq, use_container_width=True)

    st.markdown("---")

    # Trades table
    st.subheader("📋 Trade Log")
    trades = result["trades"].copy()
    trades = trades.reset_index()
    trades["action"] = trades["position"].map({1: "BUY", 0: "SELL"})
    trades["close"]  = trades["close"].round(2)
    date_col = "Date" if "Date" in trades.columns else trades.columns[0]
    st.dataframe(
        trades[[date_col, "close", "action"]].rename(columns={
            date_col: "Date", "close": "Price", "action": "Action"
        }),
        use_container_width=True,
        height=300,
    )

# ─────────────────────────────────────────────
# PAGE: RISK ANALYSIS
# ─────────────────────────────────────────────
elif page == "⚖️ Risk Analysis":
    st.title(f"⚖️ {ticker} — Risk Analysis")
    st.markdown("---")

    import numpy as np

    returns = df["close"].pct_change().dropna()

    # VaR
    confidence_level = st.slider("Confidence Level", 0.90, 0.99, 0.95, step=0.01)
    var_pct  = np.percentile(returns, (1 - confidence_level) * 100)
    var_dollar = var_pct * initial_capital

    st.subheader("📉 Value at Risk (VaR)")
    v1, v2, v3 = st.columns(3)
    v1.metric("Daily VaR (%)",    f"{var_pct*100:.2f}%")
    v2.metric("Daily VaR ($)",    f"${abs(var_dollar):,.2f}")
    v3.metric("Confidence Level", f"{confidence_level*100:.0f}%")

    st.markdown("---")

    # Returns distribution
    st.subheader("📊 Returns Distribution")
    fig_ret = go.Figure()
    fig_ret.add_trace(go.Histogram(
        x=returns, nbinsx=60,
        name="Daily Returns",
        marker_color="#636EFA", opacity=0.75,
    ))
    fig_ret.add_vline(
        x=var_pct, line_dash="dash", line_color="red",
        annotation_text=f"VaR ({confidence_level*100:.0f}%)",
    )
    fig_ret.update_layout(height=340, margin=dict(t=20, b=20),
                          xaxis_title="Daily Return", yaxis_title="Frequency")
    st.plotly_chart(fig_ret, use_container_width=True)

    st.markdown("---")

    # Rolling volatility
    st.subheader("📊 Rolling 30-Day Volatility")
    rolling_vol = returns.rolling(30).std() * np.sqrt(252) * 100
    fig_vol = px.line(
        x=df.index[1:], y=rolling_vol,
        labels={"x": "", "y": "Annualized Volatility (%)"},
        color_discrete_sequence=["#EF553B"],
    )
    fig_vol.update_layout(height=300, margin=dict(t=20, b=20))
    st.plotly_chart(fig_vol, use_container_width=True)

    st.markdown("---")

    # Drawdown chart
    st.subheader("📊 Drawdown Chart")
    roll_max  = df["close"].cummax()
    drawdown  = (df["close"] - roll_max) / roll_max * 100
    fig_dd = px.area(
        x=df.index, y=drawdown,
        labels={"x": "", "y": "Drawdown (%)"},
        color_discrete_sequence=["#EF553B"],
    )
    fig_dd.update_layout(height=300, margin=dict(t=20, b=20))
    st.plotly_chart(fig_dd, use_container_width=True)