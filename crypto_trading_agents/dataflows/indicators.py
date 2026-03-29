"""
Technical indicators computed from OHLCV data.
Pure pandas/numpy — no external indicator libraries needed.
"""

import pandas as pd
import numpy as np
from typing import Optional


def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute common technical indicators on an OHLCV DataFrame.
    Expects columns: open, high, low, close (and optionally volume).
    """
    result = df.copy()

    # Moving Averages
    result["sma_10"] = df["close"].rolling(window=10).mean()
    result["sma_20"] = df["close"].rolling(window=20).mean()
    result["sma_50"] = df["close"].rolling(window=min(50, len(df))).mean()
    result["ema_10"] = df["close"].ewm(span=10, adjust=False).mean()
    result["ema_20"] = df["close"].ewm(span=20, adjust=False).mean()

    # RSI (14-period)
    result["rsi"] = _compute_rsi(df["close"], 14)

    # MACD
    macd_line, signal_line, histogram = _compute_macd(df["close"])
    result["macd"] = macd_line
    result["macd_signal"] = signal_line
    result["macd_histogram"] = histogram

    # Bollinger Bands (20-period, 2 std)
    upper, middle, lower = _compute_bollinger(df["close"], 20, 2)
    result["bb_upper"] = upper
    result["bb_middle"] = middle
    result["bb_lower"] = lower

    # ATR (14-period)
    result["atr"] = _compute_atr(df, 14)

    # Price change
    result["pct_change"] = df["close"].pct_change() * 100

    # Volatility (20-period rolling std of returns)
    result["volatility"] = df["close"].pct_change().rolling(window=20).std() * np.sqrt(365) * 100

    return result


def _compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Compute Relative Strength Index."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def _compute_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """Compute MACD, Signal Line, and Histogram."""
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def _compute_bollinger(series: pd.Series, period: int = 20, std_dev: float = 2):
    """Compute Bollinger Bands."""
    middle = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    return upper, middle, lower


def _compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Compute Average True Range."""
    high = df["high"]
    low = df["low"]
    close = df["close"]

    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())

    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    return atr


def generate_indicator_summary(df: pd.DataFrame) -> str:
    """
    Generate a human-readable summary of current indicator values.
    Assumes df has been processed through compute_all_indicators().
    """
    if df.empty:
        return "No indicator data available."

    latest = df.iloc[-1]
    lines = []

    # Price
    lines.append(f"**Current Price:** ${latest['close']:,.2f}")

    # Trend
    if "sma_50" in latest and not np.isnan(latest["sma_50"]):
        trend = "Bullish" if latest["close"] > latest["sma_50"] else "Bearish"
        lines.append(f"**Trend (vs 50 SMA):** {trend} (SMA: ${latest['sma_50']:,.2f})")

    # RSI
    if "rsi" in latest and not np.isnan(latest["rsi"]):
        rsi_val = latest["rsi"]
        rsi_signal = "Overbought" if rsi_val > 70 else "Oversold" if rsi_val < 30 else "Neutral"
        lines.append(f"**RSI (14):** {rsi_val:.1f} — {rsi_signal}")

    # MACD
    if "macd" in latest and not np.isnan(latest["macd"]):
        macd_signal = "Bullish" if latest["macd_histogram"] > 0 else "Bearish"
        lines.append(f"**MACD:** {latest['macd']:.4f} (Signal: {latest['macd_signal']:.4f}) — {macd_signal}")

    # Bollinger Bands
    if "bb_upper" in latest and not np.isnan(latest["bb_upper"]):
        if latest["close"] > latest["bb_upper"]:
            bb_signal = "Above upper band (potential overbought)"
        elif latest["close"] < latest["bb_lower"]:
            bb_signal = "Below lower band (potential oversold)"
        else:
            bb_signal = "Within bands"
        lines.append(f"**Bollinger:** {bb_signal}")

    # Volatility
    if "volatility" in latest and not np.isnan(latest["volatility"]):
        lines.append(f"**Annualized Volatility:** {latest['volatility']:.1f}%")

    # ATR
    if "atr" in latest and not np.isnan(latest["atr"]):
        lines.append(f"**ATR (14):** ${latest['atr']:,.2f}")

    # Recent performance
    if len(df) >= 7:
        week_return = (latest["close"] / df.iloc[-7]["close"] - 1) * 100
        lines.append(f"**7-day Return:** {week_return:+.2f}%")
    if len(df) >= 30:
        month_return = (latest["close"] / df.iloc[-30]["close"] - 1) * 100
        lines.append(f"**30-day Return:** {month_return:+.2f}%")

    return "\n".join(lines)
