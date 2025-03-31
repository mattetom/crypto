from typing import List, Dict

def build_prompt(
    symbol: str,
    candles_4h: List,
    candles_1h: List,
    candles_15m: List,
    candles_5m: List,
    candles_1m: List,
    indicators_4h: Dict,
    indicators_1h: Dict,
    indicators_15m: Dict,
    indicators_5m: Dict,
    indicators_1m: Dict,
) -> str:

    def format_candles(candles: List, label: str, limit: int) -> str:
        output = f"\n {label} - ultime {limit} candele:\n"
        for i, c in enumerate(candles[-limit:]):
            output += f"{i+1}) open: {c[1]}, high: {c[2]}, low: {c[3]}, close: {c[4]}, volume: {c[5]}\n"
        return output

    def format_indicators(label: str, ind: Dict) -> str:
        return (
            f"\nIndicatori {label}:\n"
            f"EMA20: {ind['ema20']:.4f}, EMA50: {ind['ema50']:.4f}\n"
            f"MACD: {ind['macd_line']:.4f}, Signal: {ind['macd_signal']:.4f}\n"
            f"RSI: {ind['rsi']:.2f}, Stochastic RSI: {ind['stoch_rsi']:.2f}\n"
            f"ATR: {ind['atr']:.4f}\n"
            f"Volume medio: {ind['volume_avg']:.2f}, Volume ultimo: {ind['volume_last']:.2f}\n"
        )

    prompt = f"""
Simbolo: {symbol}
Analizza attentamente i dati su più timeframe (1m, 5m, 15m, 1h) e suggerisci se aprire una posizione long, short o attendere.
Voglio fare un trading molto aggressivo sfruttando le oscillazioni di brevissimo termine, anche che durino meno di 1 ora.
Se non è il momento di agire, indica tra quanti minuti rivalutare la situazione e restituisci 0 come take profit e stop loss.
Se è il momento di agire, suggerisci una percentuale di take profit e stop loss.
Restituisci un JSON con 5 campi:
- action: "buy" | "sell" | "wait"
- next_check_minutes: int
- reason: spiegazione della scelta
- take_profit_pct: float (percentuale suggerita per TP, es. 1.5 = 1.5%)
- stop_loss_pct: float (percentuale suggerita per SL, es. 0.8 = 0.8%)
Se non è il momento di agire, restituisci nella reason anche un'analisi di cosa attendere nel brevissimo periodo prima di agire.

{format_candles(candles_1m, "Timeframe 1m", 50)}
{format_indicators("1m", indicators_1m)}

{format_candles(candles_5m, "Timeframe 5m", 50)}
{format_indicators("5m", indicators_5m)}

{format_candles(candles_15m, "Timeframe 15m", 20)}
{format_indicators("15m", indicators_15m)}

{format_candles(candles_1h, "Timeframe 1h", 5)}
{format_indicators("1h", indicators_1h)}

"""
    return prompt.strip()
