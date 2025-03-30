import pandas as pd
import pandas_ta as ta
from numpy import nan as npNaN
from typing import List, Dict

def compute_indicators(candles: List[List[str]]) -> Dict[str, float]:
    df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume", "turnover"])
    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["volume"] = df["volume"].astype(float)

    indicators = {}

    df["ema20"] = ta.ema(df["close"], length=20)
    df["ema50"] = ta.ema(df["close"], length=50)
    indicators["ema20"] = df["ema20"].iloc[-1]
    indicators["ema50"] = df["ema50"].iloc[-1]

    macd = ta.macd(df["close"], fast=8, slow=18, signal=6)
    indicators["macd_line"] = macd["MACD_8_18_6"].iloc[-1]
    indicators["macd_signal"] = macd["MACDs_8_18_6"].iloc[-1]

    df["rsi"] = ta.rsi(df["close"], length=14)
    indicators["rsi"] = df["rsi"].iloc[-1]

    stoch_rsi = ta.stochrsi(df["close"], length=14)
    indicators["stoch_rsi"] = stoch_rsi["STOCHRSIk_14_14_3_3"].iloc[-1]

    df["atr"] = ta.atr(df["high"], df["low"], df["close"], length=14)
    indicators["atr"] = df["atr"].iloc[-1]

    indicators["volume_avg"] = df["volume"].rolling(14).mean().iloc[-1]
    indicators["volume_last"] = df["volume"].iloc[-1]

    return indicators
