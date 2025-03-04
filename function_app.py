import base64
import hmac
import json
import logging
import time
import azure.functions as func
import requests
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = func.FunctionApp()

API_KEY = ""
API_SECRET = ""
API_PASSPHRASE = ""
BITGET_API_URL = "https://api.bitget.com"

def get_timestamp():
  return int(time.time() * 1000)


def sign(message, secret_key):
  mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
  d = mac.digest()
  return base64.b64encode(d)


def pre_hash(timestamp, method, request_path, body=None):
    return str(timestamp) + str.upper(method) + request_path + body


def parse_params_to_str(params):
    params = [(key, val) for key, val in params.items()]
    params.sort(key=lambda x: x[0])
    url = '?' +toQueryWithNoEncode(params);
    if url == '?':
        return ''
    return url

def toQueryWithNoEncode(params):
    url = ''
    for key, value in params:
        url = url + str(key) + '=' + str(value) + '&'
    return url[0:-1]

def generate_rest_signature(secret_key, method, request_path, body=None):
  timestamp = get_timestamp()
  bodyJson = json.dumps(body)
  signature = sign(pre_hash(timestamp, method, request_path, str(bodyJson)), secret_key)
  print(signature)
  return signature, timestamp

def get_futures_open_positions():
    timestamp = get_timestamp()
    body = ""
    request_path = "/api/v2/mix/position/all-position"
    params = {"productType": "usdt-futures"}
    request_path = request_path + parse_params_to_str(params) # Need to be sorted in ascending alphabetical order by key
    signature = sign(pre_hash(timestamp, "GET", request_path, str(body)), API_SECRET)
    
    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": str(timestamp),
        "ACCESS-PASSPHRASE": API_PASSPHRASE,
        "locale": "en-US",
        "Content-Type": "application/json"
    }

    response = requests.get(BITGET_API_URL + request_path, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"Failed to fetch futures open positions: {response.status_code}")
        return None
    
def get_futures_open_position(symbol):
    timestamp = get_timestamp()
    body = ""
    request_path = "/api/v2/mix/position/single-position"
    params = {"productType": "usdt-futures", "symbol": symbol, "marginCoin": "USDT"}
    request_path = request_path + parse_params_to_str(params) # Need to be sorted in ascending alphabetical order by key
    signature = sign(pre_hash(timestamp, "GET", request_path, str(body)), API_SECRET)
    
    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": str(timestamp),
        "ACCESS-PASSPHRASE": API_PASSPHRASE,
        "locale": "en-US",
        "Content-Type": "application/json"
    }

    response = requests.get(BITGET_API_URL + request_path, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"Failed to fetch futures open positions: {response.status_code}")
        return None

def send_email(subject, body, to_email):
    from_email = ""
    password = ""

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(from_email, password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        logging.info("Email sent successfully")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

def reverse_position(symbol, size, side):
    endpoint = "/api/v2/mix/order/click-backhand"
    client_oid = str(uuid.uuid4())  # Unique order ID

    order_data = {
        "symbol": symbol,
        "productType": "usdt-futures",
        "marginCoin": "USDT",
        "size": size,
        "side": side,
        "tradeSide": "open",
        "clientOid": client_oid,
    }

    signature, timestamp = generate_rest_signature(API_SECRET, 'POST', endpoint, order_data)

    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": str(timestamp),
        "ACCESS-PASSPHRASE": API_PASSPHRASE,
        "locale": "en-US",
        "Content-Type": "application/json"
    }

    response = requests.post(BITGET_API_URL + endpoint, headers=headers, json=order_data)
    return response.json()

# @app.function_name(name="orders_check")
# @app.timer_trigger(schedule="0 */1 * * * *", arg_name="myTimer", run_on_startup=False,
#               use_monitor=False) 
# def orders_check(myTimer: func.TimerRequest) -> None:
#     if myTimer.past_due:
#         logging.info('The timer is past due!')

#     positions = get_futures_open_position('IPUSDT')
#     if positions:
#         logging.info(f"Fetched futures open positions: {positions}")
#         email_body = json.dumps(positions, indent=4)
#         send_email("Futures Open Positions", email_body, "matteo.tomasini@gmail.com")

#     logging.info('Python timer trigger function executed.')

def place_trailing_stop_order(symbol, size, side, trigger_price):
    """Places a trailing stop order using Bitget V2 API."""
    endpoint = "/api/v2/mix/order/place-plan-order"
    client_oid = str(uuid.uuid4())  # Unique order ID

    order_data = {
        "planType": "track_plan",
        "symbol": symbol,
        "productType": "usdt-futures",
        "marginMode": "isolated",
        "marginCoin": "USDT",
        "size": size,
        "callbackRatio": 0.5,
        "triggerPrice": trigger_price,
        "triggerType": "fill_price",
        "side": side,
        "tradeSide": "close",
        "orderType": "market",
        "clientOid": client_oid,
    }

    signature, timestamp = generate_rest_signature(API_SECRET, 'POST', endpoint, order_data)

    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": str(timestamp),
        "ACCESS-PASSPHRASE": API_PASSPHRASE,
        "locale": "en-US",
        "Content-Type": "application/json"
    }

    response = requests.post(BITGET_API_URL + endpoint, headers=headers, json=order_data)
    return response.json()

def test():
    timestamp = get_timestamp()
    body = ""
    request_path = "/api/v2/mix/account/account"
    params = {"symbol": "TRXUSDT", "marginCoin": "USDT", "productType": "usdt-futures"}
    request_path = request_path + parse_params_to_str(params) # Need to be sorted in ascending alphabetical order by key
    signature = sign(pre_hash(timestamp, "GET", request_path, str(body)), API_SECRET)
    print(signature)
    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": str(timestamp),
        "ACCESS-PASSPHRASE": API_PASSPHRASE,
        "locale": "en-US",
        "Content-Type": "application/json"
    }

    response = requests.get(BITGET_API_URL + request_path, headers=headers)
    return response.json()


def get_order_details(symbol, order_id):
    """Retrieves order details using Bitget V2 API."""
    timestamp = get_timestamp()
    body = ""
    request_path = "/api/v2/mix/order/detail"
    params = {"symbol": symbol, "orderId": order_id, "productType": "usdt-futures"}
    request_path = request_path + parse_params_to_str(params) # Need to be sorted in ascending alphabetical order by key
    signature = sign(pre_hash(timestamp, "GET", request_path, str(body)), API_SECRET)
    
    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": str(timestamp),
        "ACCESS-PASSPHRASE": API_PASSPHRASE,
        "locale": "en-US",
        "Content-Type": "application/json"
    }

    start_time = time.time()
    while time.time() - start_time < 10:
        response = requests.get(BITGET_API_URL + request_path, headers=headers)
        order_details = response.json()
        if response.status_code == 200 and order_details.get("data"):
            return order_details
        time.sleep(1)  # Wait for 1 second before retrying

    logging.error(f"Failed to fetch order details for order_id: {order_id}")
    return None

def place_stop_loss_order(symbol, size, side, stop_price):
    """Places a stop loss order using Bitget V2 API."""
    endpoint = "/api/v2/mix/order/place-plan-order"
    client_oid = str(uuid.uuid4())  # Unique order ID

    order_data = {
        "planType": "normal_plan",
        "symbol": symbol,
        "productType": "usdt-futures",
        "marginMode": "isolated",
        "marginCoin": "USDT",
        "size": size,
        "triggerPrice": stop_price,
        "triggerType": "mark_price",
        "side": side,
        "tradeSide": "close",
        "orderType": "market",
        "stopLossTriggerPrice": stop_price,
        "stopLossTriggerType": "mark_price",
        "clientOid": client_oid,
    }

    signature, timestamp = generate_rest_signature(API_SECRET, 'POST', endpoint, order_data)

    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": str(timestamp),
        "ACCESS-PASSPHRASE": API_PASSPHRASE,
        "locale": "en-US",
        "Content-Type": "application/json"
    }

    response = requests.post(BITGET_API_URL + endpoint, headers=headers, json=order_data)
    return response.json()

def get_symbol_precision(symbol):
    """Fetches the precision for a given symbol from Bitget API V2."""
    timestamp = get_timestamp()
    body = ""
    request_path = "/api/v2/mix/market/contracts"
    params = {"symbol": symbol, "productType": "usdt-futures"}
    request_path = request_path + parse_params_to_str(params) # Need to be sorted in ascending alphabetical order by key
    signature = sign(pre_hash(timestamp, "GET", request_path, str(body)), API_SECRET)
    print(signature)
    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": str(timestamp),
        "ACCESS-PASSPHRASE": API_PASSPHRASE,
        "locale": "en-US",
        "Content-Type": "application/json"
    }

    response = requests.get(BITGET_API_URL + request_path, headers=headers)
    if response.status_code == 200:
        symbols_data = response.json()
        if symbols_data.get("data"):
            symbol_data = symbols_data["data"][0]
            price_precision = int(symbol_data["pricePlace"])
            size_precision = int(symbol_data["volumePlace"])
            return symbol_data, price_precision, size_precision
    return None

def place_market_order(symbol, size, side):
    """Places a market order using Bitget V2 API and places a trailing stop order and stop loss order."""

    # Check if there is an open position for the symbol
    position = get_futures_open_position(symbol)
    if position.get("data"):
        logging.info(f"Position already open for symbol: {symbol} - Reversing position")
        position_data = position["data"][0]
        position_size = float(position_data["available"])
        position_side = position_data["holdSide"]
        reverse_response = reverse_position(symbol, position_size, "sell" if position_side == "short" else "buy")
        logging.info(f"Reversed position response: {reverse_response}")
        return reverse_response
    
    
    symbol, price_precision, size_precision = get_symbol_precision(symbol)

    endpoint = "/api/v2/mix/order/place-order"
    client_oid = str(uuid.uuid4())  # Unique order ID

    order_data = {
        "symbol": symbol,
        "productType": "USDT-FUTURES",
        "marginMode": "isolated",
        "marginCoin": "USDT",
        "size": round(size, size_precision),
        "side": side,
        "tradeSide": "open",
        "orderType": "market",
        "clientOid": client_oid,
    }

    signature, timestamp = generate_rest_signature(API_SECRET, 'POST', endpoint, order_data)

    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": str(timestamp),
        "ACCESS-PASSPHRASE": API_PASSPHRASE,
        "locale": "en-US",
        "Content-Type": "application/json"
    }

    response = requests.post(BITGET_API_URL + endpoint, headers=headers, json=order_data)
    order_response = response.json()
    logging.info(f"Market order response: {order_response}")

    if response.status_code == 200 and order_response.get("data"):
       order_id = order_response["data"]["orderId"]
    # order_id="1279846032966557705"
       order_details = get_order_details(symbol, order_id)
       if order_details.get("data"):
            order_price = float(order_details["data"]["priceAvg"])
            size = float(order_details["data"]["size"])
            trigger_price = round(order_price * 1.015 if side == "buy" else order_price * 0.985, price_precision)
            # stop_loss_price = round(order_price * 0.99 if side == "buy" else order_price * 1.01, price_precision)
            trailing_stop_side = "sell" if side == "sell" else "buy"
            stop_loss_side = "sell" if side == "sell" else "buy"
            place_trailing_stop_order(symbol, size, trailing_stop_side, trigger_price)
            # place_stop_loss_order(symbol, size, stop_loss_side, stop_loss_price)

    return order_details

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
        order_response = place_market_order(symbol, size=10, side="buy")
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
        order_response = place_market_order(symbol, size=10/value, side="sell")
        return func.HttpResponse(json.dumps(order_response), status_code=200, mimetype="application/json")
    except Exception as e:
        logging.error(f"Error processing request: {e}")
        return func.HttpResponse("Internal Server Error", status_code=500)
