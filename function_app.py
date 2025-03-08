import json
import logging
import azure.functions as func
from email_utils import send_email
from trading import get_bitget_klines, place_market_order
from utils import calculate_macd_values, load_state, save_state
import pandas as pd
from datetime import datetime, timedelta

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.function_name(name="open_long")
@app.route(route="open_long")
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
@app.route(route="open_short")
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
    Calculate MACD indicator for a symbol every minute using BitGet V2 API
    MACD parameters: fast=8, slow=18, signal=6
    """
    logging.info('MACD calculation timer triggered')
    
    # Load state from persistent storage
    state = load_state()
    macd_history = state['macd_history']
    last_bullish_action_time = state['last_bullish_action_time']
    last_bearish_action_time = state['last_bearish_action_time']
    
    # Configuration
    symbol = "WIFUSDT"  # Default symbol, could be parameterized
    timeframe = "15m"   # 15-minute timeframe for historical data
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
        current_time = datetime.now()
        logging.info(f"MACD calculation for {symbol} at {current_time}")
        logging.info(f"MACD Line: {latest_macd:.8f}")
        logging.info(f"Signal Line: {latest_signal:.8f}")
        logging.info(f"Histogram: {latest_histogram:.8f}")
        
        # Determine current region
        current_region = "bullish" if latest_histogram > 0 else "bearish"
        
        # Store the current state with timestamp
        current_time = datetime.now()
        macd_history.append({
            'timestamp': current_time,
            'region': current_region,
            'histogram': latest_histogram
        })
        
        # Verify we have 12 consecutive minutes of data before making decisions
        valid_history = True
        if len(macd_history) >= 12:
            history_list = list(macd_history)
            # Check for time gaps in the last 12 minutes
            for i in range(len(history_list) - 1, max(len(history_list) - 12, 0), -1):
                time_diff = (history_list[i]['timestamp'] - history_list[i-1]['timestamp']).total_seconds()
                # Allow a small tolerance (10 seconds) around 1 minute
                if not (50 <= time_diff <= 70):
                    logging.info(f"Time gap detected: {time_diff} seconds between consecutive entries")
                    send_email("MACD Time Gap",
                              f"Time gap detected: {time_diff} seconds between consecutive entries",
                              "matteo.tomasini@gmail.com")
                    valid_history = False
                    break
            
            if valid_history:
                # Check if the last 10 minutes are consistently in one region
                last_10_regions = [entry['region'] for entry in history_list[-10:]]
                region_11_min_ago = history_list[-11]['region']
                
                # Check consistency and region change
                consistent_region = all(region == last_10_regions[0] for region in last_10_regions)
                region_changed = region_11_min_ago != last_10_regions[0]
                
                if consistent_region and region_changed:
                    signal_type = last_10_regions[0].upper()
                    logging.info(f"{signal_type} SIGNAL: Consistently in {last_10_regions[0]} region for last 10 minutes after being in {region_11_min_ago} region")
                    
                    # Send notification
                    send_email(f"{signal_type} SIGNAL", 
                              f"MACD consistently {last_10_regions[0]} for {symbol} after being {region_11_min_ago}",
                              "matteo.tomasini@gmail.com")
                    
                    # Execute trading action based on signal
                    if signal_type == "BULLISH" and last_bullish_action_time is None:
                        # Open a long position
                        logging.info(f"Opening LONG position for {symbol} based on MACD signal")
                        order_response = place_market_order(symbol, size=10, side="buy")
                        if order_response:
                            last_bullish_action_time = current_time
                            
                    elif signal_type == "BEARISH" and last_bearish_action_time is None:
                        # Open a short position
                        logging.info(f"Opening SHORT position for {symbol} based on MACD signal")
                        order_response = place_market_order(symbol, size=10, side="sell")
                        if order_response:
                            last_bearish_action_time = current_time
            else:
                logging.info("History doesn't contain consecutive minutes, continuing to collect data")
        else:
            logging.info(f"Building history: {len(macd_history)}/12 minutes collected")
        
        # Reset trading action flags after a cooldown period (e.g., 1 hour)
        if last_bullish_action_time and (current_time - last_bullish_action_time > timedelta(hours=1)):
            last_bullish_action_time = None
        if last_bearish_action_time and (current_time - last_bearish_action_time > timedelta(hours=1)):
            last_bearish_action_time = None
        
        # Save state before exiting
        state = {
            'macd_history': macd_history,
            'last_bullish_action_time': last_bullish_action_time,
            'last_bearish_action_time': last_bearish_action_time
        }
        save_state(state)
            
    except Exception as e:
        logging.error(f"Error calculating MACD: {e}")