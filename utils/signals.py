"""
utils/signals.py
Computes technical indicators: Moving Averages, RSI, MACD, Bollinger Bands.
"""

import pandas as pd
import numpy as np
import yfinance as yf

def fetch_data(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """Download OHLCV data from Yahoo Finance."""
    df = yf.download(ticker, period=period, interval=interval, auto_adjust=True, progress=False)
    df.dropna(inplace=True)
    # Flatten multi-level columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [c.lower() for c in df.columns]
    return df

def add_moving_averages(df: pd.DataFrame, short=20, long=50) -> pd.DataFrame:
    df = df.copy()
    df[f"sma_{short}"] = df["close"].rolling(short).mean()
    df[f"sma_{long}"]  = df["close"].rolling(long).mean()
    df[f"ema_{short}"] = df["close"].ewm(span=short, adjust=False).mean()
    return df


def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    df = df.copy()
    delta  = df["close"].diff()
    gain   = delta.clip(lower=0)
    loss   = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs     = avg_gain / avg_loss.replace(0, np.nan)
    df["rsi"] = 100 - (100 / (1 + rs))
    return df


def add_macd(df: pd.DataFrame, fast=12, slow=26, signal=9) -> pd.DataFrame:
    df = df.copy()
    ema_fast   = df["close"].ewm(span=fast,   adjust=False).mean()
    ema_slow   = df["close"].ewm(span=slow,   adjust=False).mean()
    df["macd"]        = ema_fast - ema_slow
    df["macd_signal"] = df["macd"].ewm(span=signal, adjust=False).mean()
    df["macd_hist"]   = df["macd"] - df["macd_signal"]
    return df


def add_bollinger_bands(df: pd.DataFrame, period=20, std=2) -> pd.DataFrame:
    df = df.copy()
    sma          = df["close"].rolling(period).mean()
    rolling_std  = df["close"].rolling(period).std()
    df["bb_upper"] = sma + std * rolling_std
    df["bb_lower"] = sma - std * rolling_std
    df["bb_mid"]   = sma
    return df


def add_all_signals(df: pd.DataFrame) -> pd.DataFrame:
    df = add_moving_averages(df)
    df = add_rsi(df)
    df = add_macd(df)
    df = add_bollinger_bands(df)
    return df.dropna()


def generate_signal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate BUY/SELL/HOLD signals based on:
    - MA crossover (SMA 20 vs SMA 50)
    - RSI overbought/oversold
    - MACD crossover
    """
    df = df.copy()
    df["signal"] = "HOLD"

    # MA crossover
    ma_buy  = df["sma_20"] > df["sma_50"]
    ma_sell = df["sma_20"] < df["sma_50"]

    # RSI
    rsi_buy  = df["rsi"] < 35
    rsi_sell = df["rsi"] > 65

    # MACD crossover
    macd_buy  = (df["macd"] > df["macd_signal"]) & (df["macd"].shift(1) <= df["macd_signal"].shift(1))
    macd_sell = (df["macd"] < df["macd_signal"]) & (df["macd"].shift(1) >= df["macd_signal"].shift(1))

    # Combined signal
    df.loc[ma_buy  & rsi_buy,  "signal"] = "BUY"
    df.loc[ma_sell & rsi_sell, "signal"] = "SELL"
    df.loc[macd_buy,           "signal"] = "BUY"
    df.loc[macd_sell,          "signal"] = "SELL"

    return df