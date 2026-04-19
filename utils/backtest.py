"""
utils/backtest.py
Backtests a moving average crossover strategy against buy-and-hold (S&P 500).
"""

import pandas as pd
import numpy as np


def run_backtest(df: pd.DataFrame, initial_capital: float = 10000.0) -> dict:
    """
    Simple MA crossover strategy:
    - BUY when SMA20 crosses above SMA50
    - SELL when SMA20 crosses below SMA50
    Returns performance metrics and equity curve.
    """
    df = df.copy().reset_index()

    # Generate position: 1 = long, 0 = cash
    df["position"] = 0
    df.loc[df["sma_20"] > df["sma_50"], "position"] = 1
    df["position"] = df["position"].shift(1).fillna(0)  # avoid lookahead bias

    # Daily returns
    df["market_return"]   = df["close"].pct_change()
    df["strategy_return"] = df["market_return"] * df["position"]

    # Equity curves
    df["market_equity"]   = initial_capital * (1 + df["market_return"]).cumprod()
    df["strategy_equity"] = initial_capital * (1 + df["strategy_return"]).cumprod()

    # ── METRICS ───────────────────────────────
    trading_days = 252

    def annualized_return(equity_series):
        total = equity_series.iloc[-1] / initial_capital
        n     = len(equity_series) / trading_days
        return (total ** (1 / n) - 1) * 100

    def annualized_volatility(returns):
        return returns.std() * np.sqrt(trading_days) * 100

    def sharpe_ratio(returns, risk_free=0.05):
        excess = returns - risk_free / trading_days
        return (excess.mean() / excess.std()) * np.sqrt(trading_days) if excess.std() != 0 else 0

    def max_drawdown(equity_series):
        roll_max  = equity_series.cummax()
        drawdown  = (equity_series - roll_max) / roll_max
        return drawdown.min() * 100

    def win_rate(returns):
        positive = (returns > 0).sum()
        total    = (returns != 0).sum()
        return (positive / total * 100) if total > 0 else 0

    strat_ret  = df["strategy_return"].dropna()
    market_ret = df["market_return"].dropna()

    metrics = {
        "strategy": {
            "total_return":   round((df["strategy_equity"].iloc[-1] / initial_capital - 1) * 100, 2),
            "ann_return":     round(annualized_return(df["strategy_equity"]), 2),
            "ann_volatility": round(annualized_volatility(strat_ret), 2),
            "sharpe":         round(sharpe_ratio(strat_ret), 3),
            "max_drawdown":   round(max_drawdown(df["strategy_equity"]), 2),
            "win_rate":       round(win_rate(strat_ret), 2),
            "final_value":    round(df["strategy_equity"].iloc[-1], 2),
        },
        "market": {
            "total_return":   round((df["market_equity"].iloc[-1] / initial_capital - 1) * 100, 2),
            "ann_return":     round(annualized_return(df["market_equity"]), 2),
            "ann_volatility": round(annualized_volatility(market_ret), 2),
            "sharpe":         round(sharpe_ratio(market_ret), 3),
            "max_drawdown":   round(max_drawdown(df["market_equity"]), 2),
            "win_rate":       round(win_rate(market_ret), 2),
            "final_value":    round(df["market_equity"].iloc[-1], 2),
        },
        "equity_curve": df[["close", "market_equity",
                             "strategy_equity", "position"]].copy(),
        "trades": df[df["position"].diff() != 0][
            ["close", "position"]
        ].copy(),
    }

    return metrics