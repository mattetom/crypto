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
        output = f"\"{label}\": [[open, high, low, close, volume],"
        for i, c in enumerate(candles[-limit:]):
            output += f"[{c[1]}, {c[2]}, {c[3]}, {c[4]}, {c[5]}],"
        output += "]"
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
Opero su {symbol} (futures perp, leva 10x, long/short).  
Trading aggressivo su timeframe <1h.  
Obiettivo: profitti rapidi superiori a fee (0.06% round trip), anche piccoli.

Vincoli strategia:
- Determina TP e SL basandoti su livelli tecnici significativi come supporti e resistenze individuati nell'analisi dei dati.
- Usa trailing stop se utile
- Accetta setup deboli con rischio contenuto
- Agisci se trend chiaro o segnali anticipatori (divergenze, rimbalzi, ecc.)
- Evita ingressi se probabilità successo bassa
- Evita ingressi contro il trend principale su timeframe 1h, a meno di segnali forti e chiari (pattern di inversione, divergenze marcate, volumi e struttura coerente)

Frequenza analisi:
- 5-10 minuti se segnali forti o mercato attivo
- ≥15 min (fino a 30) se segnali misti o stagnazione

Input:  
Candlestick OHLCV di 3 timeframe (5m, 15m, 1h), **ordinate dalla più vecchia alla più recente**  
Calcola tu EMA, MACD, RSI, Stoch RSI, ATR.

Output JSON:
{{
  "action": "long" | "short" | "wait",
  "next_check_minutes": 5-30,
  "reason": "...",
  "take_profit_price": float,
  "stop_loss_price": float,
  "risk_mode": "standard" | "trailing"
}}
Se wait, TP e SL = 0."
"""
    # return prompt.strip()
    input = [
        {
        "role": "system",
        "content": "Sei un analista di crypto trading. Riceverai candele OHLCV su 3 timeframe. Calcola gli indicatori EMA20, EMA50, MACD, RSI, Stochastic RSI e ATR e suggerisci se aprire una posizione, con logica aggressiva ma prudente come specificato dall'utente."
        },
        {
        "role": "user",
        "content": prompt.strip()
        },
        {
        "role": "user",
        "content": f"{ {format_candles(candles_5m, 'Timeframe 5m', 40)}, {format_candles(candles_15m, 'Timeframe 15m', 40)}, {format_candles(candles_1h, 'Timeframe 1h', 40)} }"
        }
    ]
    return input

