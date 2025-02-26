import websocket
import json
import hmac
import hashlib
import base64
import time
import threading
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import uuid
import json
import hmac
import hashlib
import base64


# 🔹 Replace with your Bitget API credentials
API_KEY = ""
API_SECRET = ""
API_PASSPHRASE = ""

# 🔹 Email configuration (for notifications)
GMAIL_USER = ""
GMAIL_PASSWORD = ""
RECIPIENT_EMAIL = ""

# 🔹 Bitget WebSocket URL (Production for SPOT)
# BITGET_WS_URL = "wss://ws.bitget.com/spot/v1/stream"
BITGET_WS_URL = "wss://ws.bitget.com/v2/ws/private"

# 🔹 Bitget API Base URL
BITGET_API_URL = "https://api.bitget.com"

# Global variables to track ping/pong responses
last_pong_time = time.time()
ws = None  # Global WebSocket instance

def generate_websocket_signature(endpoint, timestamp):
    """Generates the correct HMAC-SHA256 signature."""
    message = f"{timestamp}GET{endpoint}"
    signature = base64.b64encode(
        hmac.new(API_SECRET.encode(), message.encode(), hashlib.sha256).digest()
    ).decode()
    return signature

def get_timestamp():
  return int(time.time() * 1000)


def sign(message, secret_key):
  mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
  d = mac.digest()
  return base64.b64encode(d)


def pre_hash(timestamp, method, request_path, body):
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

def generate_rest_signature(secret_key, method, request_path, query_params=None, body=None):
  timestamp = get_timestamp()
  bodyJson = json.dumps(body)
  signature = sign(pre_hash(timestamp, method, request_path, str(bodyJson)), secret_key)
  print(signature)
  return signature, timestamp


def place_trailing_stop_buy_order(symbol, size, activation_price):
    """Places a trailing stop buy order 4.5% below the sell price using Bitget V2 API."""
    
    endpoint = "/api/v2/spot/trade/place-order"

    # timestamp = str(int(time.time() * 1000))  # ✅ REST API uses MILLISECONDS
    client_oid = str(uuid.uuid4())  # ✅ Unique order ID

    order_data = {
        "symbol": symbol,
        "side": "buy",
        "orderType": "trailing_stop",
        "size": str(size),
        "triggerPrice": str(activation_price),
        "rangeRate": "0.01",  # 1% trailing stop
        "triggerType": "last_price",
        "force": "gtc",
        "clientOid": client_oid
    }

    signature, timestamp = generate_rest_signature(API_SECRET, 'POST', endpoint, None, order_data)

    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": timestamp,  # ✅ Must match requestTime
        "ACCESS-PASSPHRASE": API_PASSPHRASE,
        "locale": "en-US",
        "Content-Type": "application/json"
    }

    response = requests.post(BITGET_API_URL + endpoint, headers=headers, json=order_data)
    response_data = response.json()
    print(f"🚀 Trailing Stop Buy Order Placed: {response_data}")

    return response_data

def place_trailing_stop_sell_order(symbol, size, activation_price):
    """Places a trailing stop sell order using Bitget V2 API."""
    
    endpoint = "/api/v2/mix/order/place-plan-order"

    client_oid = str(uuid.uuid4())  # ✅ Unique order ID

    # order_data = {
    #     "symbol": symbol,
    #     "side": "sell",
    #     "orderType": "market",
    #     "size": str(size),
    #     "triggerPrice": str(activation_price),
    #     "rangeRate": "0.01",  # 1% trailing stop
    #     "triggerType": "mark_price",
    #     "force": "gtc",
    #     "clientOid": client_oid
    # }

    order_data = {
            "planType": "track_plan",  # Trailing stop order
            "delegateType": "track",
            "symbol": symbol,
            "productType": "COIN-FUTURES",  # e.g., "UMCBL" for USDT-M futures
            "marginMode": "isolated",
            "marginCoin": "USDT",
            "size": str(size),
            "triggerPrice": str(activation_price),
            "callbackRatio": str(0.01),  # Trailing percentage
            "triggerType": "fill_price",  # or "mark_price"
            "side": "sell",  # "buy" or "sell"
            "orderType": "market",  # Trailing stop orders execute at market price
            "reduceOnly": "no",  # "yes" or "no"
            "clientOId": client_oid
        }

    signature, timestamp = generate_rest_signature(API_SECRET, 'POST', endpoint, None, order_data)

    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": str(timestamp),  # ✅ Must match requestTime
        "ACCESS-PASSPHRASE": API_PASSPHRASE,
        "locale": "en-US",
        "Content-Type": "application/json"
    }

    response = requests.post(BITGET_API_URL + endpoint, headers=headers, json=order_data)
    response_data = response.json()
    print(f"🚀 Trailing Stop Sell Order Placed: {response_data}")

    return response_data


def send_email(order_details, sell_price=None, size=None, order_type=""):
    """Sends an email when a buy/sell order is filled."""
    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL_USER
        msg["To"] = RECIPIENT_EMAIL
        msg["Subject"] = f"📩 {order_type} Order Notification: {order_details['instId']}"

        body = f"""
        <html>
        <body>
            <h2>{order_type} Order Details</h2>
            <p><b>Symbol:</b> {order_details["instId"]}</p>
            <p><b>Order ID:</b> {order_details["orderId"]}</p>
            <p><b>Size:</b> {order_details["size"]}</p>
            <p><b>Average Price:</b> {order_details["priceAvg"]}</p>
        """

        if sell_price and size:
            body += f"""
            <h2>New Sell Order</h2>
            <p><b>Sell Price:</b> {sell_price}</p>
            <p><b>Sell Size:</b> {size}</p>
            """

        body += "</body></html>"

        msg.attach(MIMEText(body, "html"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USER, RECIPIENT_EMAIL, msg.as_string())
        server.quit()

        print(f"✅ Email sent: {order_type} Order for {order_details['instId']}")
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")


def send_ping():
    """Sends 'ping' every 30 seconds and reconnects if no 'pong' received."""
    global last_pong_time, ws
    time.sleep(5)  # 🔹 Wait before sending the first ping

    while True:
        if ws:
            try:
                ws.send("ping")
                print("📡 Sent: ping")
                last_pong_time = time.time()  # Reset pong timer when we send ping
            except Exception as e:
                print(f"⚠️ Failed to send ping: {e}")
                reconnect_websocket()

        # Wait 30 seconds before sending the next ping
        time.sleep(30)
        print(last_pong_time)
        # Check if we received a 'pong' within the last 30 seconds
        if time.time() - last_pong_time > 30:
            print("⚠️ No 'pong' received in 30s. Reconnecting...")
            reconnect_websocket()

def reconnect_websocket():
    """Reconnects the WebSocket with exponential backoff."""
    global ws
    delay = 1
    while True:
        print(f"🔄 Reconnecting WebSocket in {delay} seconds...")
        time.sleep(delay)
        try:
            ws = websocket.WebSocketApp(
                BITGET_WS_URL,
                on_message=on_message,
                on_open=on_open,
                on_error=on_error,
                on_close=on_close
            )
            ws.run_forever()
            break  
        except Exception as e:
            print(f"⚠️ WebSocket reconnection failed: {e}")
            delay = min(delay * 2, 60)

def on_message(ws, message):
    """Handles messages received from WebSocket."""
    print(f"📡 Received message: {message}")

    global last_pong_time

    # Handle "pong" responses
    if message == "pong":
        print("📡 Received: pong")
        last_pong_time = time.time()
        print(last_pong_time)
        return
    
    try:
        data = json.loads(message)  # Only parse if it's valid JSON
    except json.JSONDecodeError:
        print(f"⚠️ Received non-JSON message: {message}")
        return

    # Handle Subscription Confirmation
    if "event" in data and data["event"] == "subscribe":
        print(f"✅ Successfully subscribed to: {data}")
        return  # Ignore further processing

    # Handle WebSocket Errors
    if "event" in data and data["event"] == "error":
        print(f"❌ WebSocket Error: {data}")
        reconnect_websocket()
        return

    # Ensure message contains order update data
    if "arg" in data and "channel" in data["arg"] and data["arg"]["channel"] == "orders":
        print(f"📩 Order Update: {data}")

        # Extract order details safely
        order_details = data.get("data", [{}])[0]  # Get first order entry

        if "status" in order_details and order_details["status"] == "filled":
            symbol = order_details["instId"]
            size = float(order_details["size"])
            price = float(order_details["priceAvg"])
            side = order_details["side"]

            if side == "buy":
                print(f"🟢 Buy Order Filled: {symbol} | Size: {size} | Price: {price}")

                # Calculate trailing stop activation price (+4.5%)
                activation_price = round(price * 1.045, 6)

                # Place Trailing Stop Sell Order
                sell_response = place_trailing_stop_sell_order(symbol, size, activation_price)

                # Send Email
                send_email(order_details, activation_price, size, "TRAILING STOP SELL")

            elif side == "sell":
                print(f"🔴 Sell Order Filled: {symbol} | Size: {size} | Price: {price}")

                # Calculate trailing stop buy activation price (-4.5%)
                buy_activation_price = round(price * 0.955, 6)

                # Place Trailing Stop Buy Order
                buy_response = place_trailing_stop_buy_order(symbol, size, buy_activation_price)

                # Send Email
                send_email(order_details, buy_activation_price, size, "TRAILING STOP BUY")

def on_open(ws):
    """Authenticates and subscribes to private SPOT orders."""
    timestamp = str(int(time.time()))
    signature = generate_websocket_signature("/user/verify", timestamp)

    auth_payload = {
        "op": "login",
        "args": [{"apiKey": API_KEY, "passphrase": API_PASSPHRASE, "timestamp": timestamp, "sign": signature}]
    }

    ws.send(json.dumps(auth_payload))
    time.sleep(1)

    subscribe_payload = {"op": "subscribe", "args": [{"instType": "SPOT", "channel": "orders"}]}
    ws.send(json.dumps(subscribe_payload))


def on_error(ws, error):
    print(f"❌ onerror WebSocket Error: {error}")


def on_close(ws, close_status_code, close_msg):
    print("❌ WebSocket Disconnected. Reconnecting in 5 seconds...")
    time.sleep(5)
    reconnect_websocket()  # Reconnect automatically


if __name__ == "__main__":
    print("🚀 Starting WebSocket Client for Bitget...")
    # threading.Thread(target=send_ping, daemon=True).start()
    # reconnect_websocket()
    place_trailing_stop_sell_order("PIUSDT", 50, 2)



