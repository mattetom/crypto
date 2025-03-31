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
Sto operando su {symbol} con i perpetual futures a leva 10x.  
Posso aprire posizioni long o short.

Voglio fare un trading molto aggressivo sfruttando le oscillazioni di brevissimo termine, anche inferiori a 1 ora.

Il mio obiettivo è guadagnare in ogni apertura/chiusura di posizione una percentuale netta che superi le fee (0.06% per round trip), ma rimanga contenuta per sfruttare movimenti rapidi.

Suggerisci una strategia di ingresso con questi vincoli:
- take profit ideale: 1.0% - 1.2%
- stop loss ideale: 0.6% - 0.8%
- risk_reward_ratio ≥ 1.3
- possibilità di usare trailing stop se vantaggioso

Accetto anche setup deboli ma promettenti, purché il rischio sia contenuto.  
Se ci sono segnali anticipatori (es. rimbalzo da oversold, divergenze MACD/RSI), valuta comunque l'apertura di una posizione con SL stretto e TP minimo.

Se i segnali tecnici confermano un trend ribassista su più timeframe (MACD negativo, RSI debole, prezzo sotto EMA), valuta attivamente un ingresso short in trend continuativo, anche in assenza di segnali anticipatori.

Se i segnali tecnici confermano un trend rialzista su più timeframe (MACD positivo, RSI forte, prezzo sopra EMA), valuta attivamente un ingresso long in trend continuativo, anche in assenza di segnali anticipatori.

Valuta ingressi anche se lo Stochastic RSI è neutro o non estremo, purché MACD, RSI e andamento delle EMA confermino una direzione coerente.

Preferisco agire piuttosto che attendere passivamente.  
Se i segnali sono misti ma c'è un'opportunità con rischio controllabile, proponi comunque una posizione ridotta piuttosto che "wait".

Imposta `next_check_minutes` a massimo 10 minuti, idealmente 5, per restare reattivi.

Se non è il momento di agire, restituisci 0 come take profit e stop loss.  
Se è il momento di agire, restituisci un JSON con questi 6 campi:

- action: "long" | "short" | "wait"
- next_check_minutes: int (max 10)
- reason: spiegazione della scelta
- take_profit_pct: float
- stop_loss_pct: float
- risk_mode: "standard" | "trailing"

{format_candles(candles_5m, "Timeframe 5m", 50)}
{format_indicators("5m", indicators_5m)}

{format_candles(candles_15m, "Timeframe 15m", 20)}
{format_indicators("15m", indicators_15m)}

{format_candles(candles_1h, "Timeframe 1h", 5)}
{format_indicators("1h", indicators_1h)}

"""
    return prompt.strip()
