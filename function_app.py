import json
import logging
import azure.functions as func
from trading import place_market_order
from email_utils import send_email

app = func.FunctionApp()

@app.function_name(name="ping")
@app.timer_trigger(schedule="30 4,9,14,19,24,29,34,39,44,49,54,59 * * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def ping(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')

    # positions = get_futures_open_position('IPUSDT')
    # if positions:
    #     logging.info(f"Fetched futures open positions: {positions}")
    #     email_body = json.dumps(positions, indent=4)
    #     send_email("Futures Open Positions", email_body, "matteo.tomasini@gmail.com")

    logging.info('Python timer trigger function executed.')

@app.function_name(name="open_long")
@app.route(route="open_long", auth_level=func.AuthLevel.ANONYMOUS)
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
@app.route(route="open_short", auth_level=func.AuthLevel.ANONYMOUS)
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

@app.function_name(name="open_long_v2")
@app.route(route="open_long_v2", auth_level=func.AuthLevel.ANONYMOUS)
def open_long_v2(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        req_body = req.get_json()
        symbol = req_body.get("symbol")
        value = req_body.get("value")
        if not symbol or not value:
            return func.HttpResponse("Symbol and value are required", status_code=400)

        logging.info('open_long_v2 function called with symbol: %s and value: %s', symbol, value)
        value = float(value)
        # Open a future long position at market value
        # order_response = place_market_order(symbol, size=10, side="buy")
        order_response = ""
        return func.HttpResponse(json.dumps(order_response), status_code=200, mimetype="application/json")
    except Exception as e:
        logging.error(f"Error processing request: {e}")
        return func.HttpResponse("Internal Server Error", status_code=500)

@app.function_name(name="open_short_v2")
@app.route(route="open_short_v2", auth_level=func.AuthLevel.ANONYMOUS)
def open_short_v2(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        req_body = req.get_json()
        symbol = req_body.get("symbol")
        value = req_body.get("value")
        if not symbol or not value:
            return func.HttpResponse("Symbol and value are required", status_code=400)

        logging.info('open_short_v2 function called with symbol: %s and value: %s', symbol, value)
        value = float(value)
        # Open a future short position at market value
        # order_response = place_market_order(symbol, size=10/value, side="sell")
        order_response = ""
        return func.HttpResponse(json.dumps(order_response), status_code=200, mimetype="application/json")
    except Exception as e:
        logging.error(f"Error processing request: {e}")
        return func.HttpResponse("Internal Server Error", status_code=500)
