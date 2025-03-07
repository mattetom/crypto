import json
import logging
import azure.functions as func
from email_utils import send_email
from trading import get_bitget_klines, place_market_order
from utils import calculate_macd_values
import pandas as pd
from datetime import datetime

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.function_name(name="open_long")
@app.route(route="open_long")  # Removed redundant auth_level as it's set in FunctionApp
def open_long(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        symbol = req.params.get("symbol")
        if not symbol:
            return func.HttpResponse("Symbol is required", status_code=400)

        logging.info('open_long function called with symbol: %s', symbol) 
        # Open a future long position at market value
        order_response = place_market_order(symbol, size=10, side="buy")
        
        if order_response is None:
            return func.HttpResponse(json.dumps({"message": "No order was executed or position already exists"}), 
                                    status_code=200, 
                                    mimetype="application/json")
                                    
        return func.HttpResponse(json.dumps(order_response), status_code=200, mimetype="application/json")
    except Exception as e:
        logging.error(f"Error processing request: {e}")
        return func.HttpResponse("Internal Server Error", status_code=500)

@app.function_name(name="open_short")
@app.route(route="open_short")  # Removed redundant auth_level as it's set in FunctionApp
def open_short(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        symbol = req.params.get("symbol")
        if not symbol:
            return func.HttpResponse("Symbol is required", status_code=400)

        logging.info('open_short function called with symbol: %s', symbol) 
        # Open a future short position at market value
        order_response = place_market_order(symbol, size=10, side="sell")
        
        if order_response is None:
            return func.HttpResponse(json.dumps({"message": "No order was executed or position already exists"}), 
                                    status_code=200, 
                                    mimetype="application/json")
                                    
        return func.HttpResponse(json.dumps(order_response), status_code=200, mimetype="application/json")
    except Exception as e:
        logging.error(f"Error processing request: {e}")
        return func.HttpResponse("Internal Server Error", status_code=500)

@app.function_name(name="calculate_macd_v2")
@app.timer_trigger(schedule="0 */1 * * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def calculate_macd_v2(myTimer: func.TimerRequest) -> None:
    """
    Calculate MACD indicator for a symbol every 15 minutes using BitGet V2 API
    MACD parameters: fast=8, slow=18, signal=6
    """
    logging.info('MACD calculation timer triggered')
    
    # Configuration
    symbol = "WIFUSDT"  # Default symbol, could be parameterized
    timeframe = "15m"   # 15-minute timeframe
    fast_length = 8
    slow_length = 18
    signal_smoothing = 6
    
    try:
        # Get historical klines from BitGet V2 API
        klines = get_bitget_klines(symbol, timeframe)
        
        if klines is None or len(klines) < slow_length:
            logging.error(f"Not enough data points for MACD calculation. Got {len(klines) if klines else 0} klines")
            return
            
        # Convert to dataframe for easier calculations
        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
        df['close'] = pd.to_numeric(df['close'])
        
        # Calculate MACD
        macd_line, signal_line, histogram = calculate_macd_values(
            df['close'].values, fast_length, slow_length, signal_smoothing
        )
        
        # Get latest values
        latest_macd = macd_line[-1]
        latest_signal = signal_line[-1]
        latest_histogram = histogram[-1]
        
        # Log results
        logging.info(f"MACD calculation for {symbol} at {datetime.now()}")
        logging.info(f"MACD Line: {latest_macd:.8f}")
        logging.info(f"Signal Line: {latest_signal:.8f}")
        logging.info(f"Histogram: {latest_histogram:.8f}")
        
        # Determine signal (example logic)
        if latest_macd > latest_signal and macd_line[-2] <= signal_line[-2]:
            logging.info("BULLISH SIGNAL: MACD crossed above Signal")
            send_email("BULLISH SIGNAL", f"MACD crossed above Signal for {symbol}", "matteo.tomasini@gmail.com")
        elif latest_macd < latest_signal and macd_line[-2] >= signal_line[-2]:
            logging.info("BEARISH SIGNAL: MACD crossed below Signal")
            send_email("BEARISH SIGNAL", f"MACD crossed below Signal for {symbol}", "matteo.tomasini@gmail.com")
            
    except Exception as e:
        logging.error(f"Error calculating MACD: {e}")