import logging
import time
import requests
import uuid
import os
from utils import get_timestamp, sign, pre_hash, parse_params_to_str, generate_rest_signature

# Get settings from environment variables
API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")
API_PASSPHRASE = os.environ.get("API_PASSPHRASE")
BITGET_API_URL = os.environ.get("BITGET_API_URL", "https://api.bitget.com")

def get_futures_open_positions():
    logging.info("Fetching futures open positions")
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
    logging.info(f"Fetching futures open position for symbol: {symbol}")
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

def reverse_position(symbol, size, side):
    """Reverses the position for a given symbol using Bitget V2 API."""
    logging.info(f"Reversing position for symbol: {symbol}, size: {size}, side: {side}")

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

def place_trailing_stop_order(symbol, size, side, trigger_price):
    """Places a trailing stop order using Bitget V2 API."""
    logging.info(f"Placing trailing stop order for symbol: {symbol}, size: {size}, side: {side}, trigger_price: {trigger_price}")

    endpoint = "/api/v2/mix/order/place-plan-order"
    client_oid = str(uuid.uuid4())  # Unique order ID

    order_data = {
        "planType": "track_plan",
        "symbol": symbol,
        "productType": "usdt-futures",
        "marginMode": "isolated",
        "marginCoin": "USDT",
        "size": size,
        "callbackRatio": 0.15,
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

# def test():
#     timestamp = get_timestamp()
#     body = ""
#     request_path = "/api/v2/mix/account/account"
#     params = {"symbol": "TRXUSDT", "marginCoin": "USDT", "productType": "usdt-futures"}
#     request_path = request_path + parse_params_to_str(params) # Need to be sorted in ascending alphabetical order by key
#     signature = sign(pre_hash(timestamp, "GET", request_path, str(body)), API_SECRET)
#     print(signature)
#     headers = {
#         "ACCESS-KEY": API_KEY,
#         "ACCESS-SIGN": signature,
#         "ACCESS-TIMESTAMP": str(timestamp),
#         "ACCESS-PASSPHRASE": API_PASSPHRASE,
#         "locale": "en-US",
#         "Content-Type": "application/json"
#     }

#     response = requests.get(BITGET_API_URL + request_path, headers=headers)
#     return response.json()

def get_order_details(symbol, order_id):
    """Retrieves order details using Bitget V2 API."""
    logging.info(f"Fetching order details for order_id: {order_id}")

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
    logging.info(f"Placing stop loss order for symbol: {symbol}, size: {size}, side: {side}, stop_price: {stop_price}")

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
    logging.info(f"Fetching symbol precision for symbol: {symbol}")

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
            symbol = symbol_data["symbol"]
            price_precision = int(symbol_data["pricePlace"])
            size_precision = int(symbol_data["volumePlace"])
            return symbol, price_precision, size_precision
    return None

def get_open_orders(symbol):
    """Fetches open orders for a given symbol from Bitget API V2."""
    logging.info(f"Fetching open orders for symbol: {symbol}")

    timestamp = get_timestamp()
    body = ""
    request_path = "/api/v2/mix/order/orders-plan-pending"
    params = {"symbol": symbol, "productType": "usdt-futures", "planType": "track_plan"}
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

def cancel_orders(symbol, order_ids):
    """Cancels orders using Bitget V2 API."""
    logging.info(f"Cancelling orders for symbol: {symbol}, order_ids: {order_ids}")

    endpoint = "/api/v2/mix/order/cancel-plan-order"
    order_id_list = [{"orderId": order_id} for order_id in order_ids]
    order_data = {
        "orderIdList": order_id_list,
        "symbol": symbol,
        "productType": "usdt-futures"
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

def place_market_order(symbol, size, side):
    """Places a market order using Bitget V2 API and places a trailing stop order and stop loss order."""
    logging.info(f"Placing market order for symbol: {symbol}, size: {size}, side: {side}")

    symbol_info = get_symbol_precision(symbol)
    if not symbol_info:
        logging.error(f"Failed to fetch symbol precision for symbol: {symbol}")
        return None
        
    symbol, price_precision, size_precision = symbol_info

    # Check if there is an open position for the symbol
    position = get_futures_open_position(symbol)
    if position.get("data"):
        logging.info(f"Position already open for symbol: {symbol} - Reversing position")
        position_data = position["data"][0]
        position_direction = position_data["holdSide"]
        if ((position_direction == 'long' and side == 'buy') or (position_direction == 'short' and side == 'sell')):
            logging.info(f"Position already open for symbol: {symbol} and side: {position_direction}")
            return None
        position_size = float(position_data["available"])
        position_side = position_data["holdSide"]
        # get all open orders related to the symbol and cancel them
        open_orders = get_open_orders(symbol)
        if open_orders.get("data"):
            order_ids = [order["orderId"] for order in open_orders["data"]["entrustedList"]]
            cancel_orders(symbol, order_ids)
        order_response = reverse_position(symbol, position_size, "sell" if position_side == "short" else "buy")
        logging.info(f"Reversed position response: {order_response}")
    else:
        logging.info(f"No open position for symbol: {symbol}")
        endpoint = "/api/v2/mix/order/place-order"
    
        order_data = {
            "symbol": symbol,
            "productType": "USDT-FUTURES",
            "marginMode": "isolated",
            "marginCoin": "USDT",
            "size": size,
            "side": side,
            "tradeSide": "open",
            "orderType": "market",

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

    if order_response.get("data"):
       order_id = order_response["data"]["orderId"]
       order_details = get_order_details(symbol, order_id)
       if order_details.get("data"):
            order_price = float(order_details["data"]["priceAvg"])
            size = float(order_details["data"]["size"])
            trigger_price = round(order_price * 1.0075 if side == "buy" else order_price * 0.9925, price_precision)
            stop_loss_price = round(order_price * 0.9925 if side == "buy" else order_price * 1.075, price_precision)
            trailing_stop_side = "sell" if side == "buy" else "buy"
            stop_loss_side = "sell" if side == "buy" else "buy"
            place_trailing_stop_order(symbol, size, trailing_stop_side, trigger_price)
            # place_stop_loss_order(symbol, size, stop_loss_side, stop_loss_price)
            modify_market_order(symbol, order_id, stop_loss_price)

    return order_details

def modify_market_order(symbol, order_id, stop_loss_price):
    """Modifies a market order using Bitget V2 API."""
    logging.info(f"Modifying market order for symbol: {symbol}, order_id: {order_id}, stop_loss_price: {stop_loss_price}")

    endpoint = "/api/v2/mix/order/modify-order"
    
    order_data = {
        "symbol": symbol,
        "productType": "USDT-FUTURES",
        "newPresetStopLossPrice": stop_loss_price
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
    logging.info(f"Update market order response: {order_response}")

def get_bitget_klines(symbol, interval, limit=100):
    """
    Get historical klines (candlestick data) from BitGet V2 API
    """
    logging.info(f"Fetching klines for symbol: {symbol}, interval: {interval}, limit: {limit}")

    timestamp = get_timestamp()
    body = ""
    request_path = "/api/v2/mix/market/candles"
    params = {"symbol": symbol, "productType": "usdt-futures", "granularity": interval, "limit": str(limit)}
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
    try:
        response = requests.get(BITGET_API_URL + request_path, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "00000":
                return data.get("data", [])
            else:
                logging.error(f"BitGet API error: {data.get('msg')}")
                return None
        else:
            logging.error(f"BitGet API request failed with status code: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Error fetching klines from BitGet: {e}")
        return None