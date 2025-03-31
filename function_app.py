from datetime import datetime
import logging
import azure.functions as func

from bitget_api import get_candles
from email_utils import send_email
from indicators import compute_indicators
from openai_client import call_openai_market_analysis
from prompt_builder import build_prompt
from table_storage import get_crypto_status, update_crypto_status


SYMBOL = "WIFUSDT"

def should_call_openai(status: dict) -> bool:
    if not status:
        return True
    next_check = datetime.fromisoformat(status["next_check_time"])
    return datetime.utcnow() >= next_check

app = func.FunctionApp()

@app.function_name(name="takeDecsion")
@app.timer_trigger(schedule="10 */1 * * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def takeDecsion(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')

    print(f"🔄 Avvio analisi per {SYMBOL} alle {datetime.utcnow().isoformat()}")

    status = get_crypto_status(SYMBOL)

    if not should_call_openai(status):
        print(f"⏳ Prossima analisi per {SYMBOL} dopo le {status['next_check_time']}")
        return

    try:
        candles_4h = get_candles(SYMBOL, "4H", 50)
        candles_1h = get_candles(SYMBOL, "1H", 50)
        candles_15m = get_candles(SYMBOL, "15m", 50)
        candles_5m = get_candles(SYMBOL, "5m", 50)
        candles_1m = get_candles(SYMBOL, "1m", 50)

        ind_4h = compute_indicators(candles_4h)
        ind_1h = compute_indicators(candles_1h)
        ind_15m = compute_indicators(candles_15m)
        ind_5m = compute_indicators(candles_5m)
        ind_1m = compute_indicators(candles_1m)

        prompt = build_prompt(
            symbol=SYMBOL,
            candles_4h=candles_4h,
            candles_1h=candles_1h,
            candles_15m=candles_15m,
            candles_5m=candles_5m,
            candles_1m=candles_1m,
            indicators_4h=ind_4h,
            indicators_1h=ind_1h,
            indicators_15m=ind_15m,
            indicators_5m=ind_5m,
            indicators_1m=ind_1m
        )

        result = call_openai_market_analysis(prompt)
        decision = result["decision"]
        tokens = result["tokens"]

        update_crypto_status(
            symbol=SYMBOL,
            action=decision["action"],
            next_check_minutes=decision["next_check_minutes"],
            reason=decision["reason"],
            take_profit_pct=decision["take_profit_pct"],
            stop_loss_pct=decision["stop_loss_pct"],
            token_usage=tokens
        )

        send_email(
            subject=f"Analisi di mercato per {SYMBOL}",
            body=(
                f"🔄 Analisi completata per {SYMBOL}\n\n"
                f"✅ Azione: {decision['action'].upper()}\n"
                f"📈 TP: {decision['take_profit_pct']:.2f}%\n"
                f"📉 SL: {decision['stop_loss_pct']:.2f}%\n\n"
                f"⏳ Prossima analisi tra {decision['next_check_minutes']} minuti\n\n"
                f"Motivo: {decision['reason']}\n\n"
                f"Token utilizzati: {tokens}\n\n"
                f"Ultimo aggiornamento: {datetime.utcnow().isoformat()}"
            ),
            to_email="matteo.tomasini@gmail.com"
        )

        print(f"✅ {SYMBOL}: {decision['action'].upper()} | Prossima analisi tra {decision['next_check_minutes']} minuti")
        print(f"📝 Motivo: {decision['reason']}")

    except Exception as e:
        print(f"❌ Errore durante l'elaborazione di {SYMBOL}: {e}")

    logging.info('Python timer trigger function executed.')

@app.function_name(name="test")
@app.route(route="test", auth_level=func.AuthLevel.ANONYMOUS)
def test(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )