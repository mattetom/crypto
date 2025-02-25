import websocket
import json
import hmac
import hashlib
import base64
import time
import requests
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# 🔹 Replace with your Bitget API credentials
API_KEY = "bg_1c2287b7a18c3a7b50177f9771645f64"
API_SECRET = "f382b057215383ad04b474e1d6169b35f2ac1693407054275af2fcfbdb32ac94"
API_PASSPHRASE = "9283jddhj89e298hdhaklscnc901834j"

# 🔹 Email configuration (for notifications)
GMAIL_USER = "matteo.tomasini@gmail.com"
GMAIL_PASSWORD = "password"
RECIPIENT_EMAIL = "matteo.tomasini@gmail.com"

# 🔹 Azure Function Webhook URL
# WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://your-azure-function-url")

# 🔹 Bitget API Base URL
BITGET_API_URL = "https://api.bitget.com"


def generate_signature(endpoint, timestamp, body=""):
    """Generates a signed request for Bitget API."""
    message = timestamp + "POST" + endpoint + json.dumps(body)
    signature = base64.b64encode(
        hmac.new(API_SECRET.encode(), message.encode(), hashlib.sha256).digest()
    ).decode()
    
    return signature


def place_trailing_stop_order(symbol, last_fill_price):
    """Places a new trailing stop buy order for the same crypto using 50 USDT."""
    
    # Calculate order price (4.5% above last sell price)
    new_order_price = round(float(last_fill_price) * 1.045, 6)
    
    # USDT amount to spend
    usdt_amount = 50
    
    # Calculate asset quantity
    order_quantity = round(usdt_amount / new_order_price, 6)

    # Define trailing stop distance (1%)
    trailing_stop_distance = 0.01  # 1%

    # API endpoint
    endpoint = "/api/mix/v1/order/placePlan"

    # Request payload
    order_data = {
        "symbol": symbol,
        "marginCoin": "USDT",
        "size": str(order_quantity),  
        "side": "buy",
        "orderType": "trailing_stop",
        "triggerPrice": str(new_order_price),  
        "rangeRate": str(trailing_stop_distance),  
        "triggerType": "mark_price",
        "reduceOnly": False
    }

    timestamp = str(int(time.time() * 1000))
    signature = generate_signature(endpoint, timestamp, order_data)

    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": API_PASSPHRASE,
        "Content-Type": "application/json"
    }

    response = requests.post(BITGET_API_URL + endpoint, headers=headers, json=order_data)
    
    response_data = response.json()
    print(f"🚀 New Trailing Stop Order Placed: {response_data}")

    return response_data, new_order_price, order_quantity


def send_email(order_details, new_order_price=None, new_order_quantity=None):
    """Sends an email with order details via Gmail, including new trailing stop order details."""
    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL_USER
        msg["To"] = RECIPIENT_EMAIL
        msg["Subject"] = f"📩 Order Closed & New Buy Order Placed: {order_details['symbol']}"

        body = f"""
        <html>
        <body>
            <h2>Closed Order Details</h2>
            <p><b>Symbol:</b> {order_details["symbol"]}</p>
            <p><b>Quantity:</b> {order_details["size"]}</p>
            <p><b>Close Price:</b> {order_details.get("lastFillPrice", "N/A")}</p>
            <p><b>Status:</b> {order_details["status"]}</p>
        """

        if new_order_price and new_order_quantity:
            body += f"""
            <h2>New Trailing Stop Buy Order</h2>
            <p><b>Buy Price:</b> {new_order_price}</p>
            <p><b>Quantity:</b> {new_order_quantity}</p>
            <p><b>Trailing Stop Distance:</b> 1%</p>
            <p><b>USDT Spent:</b> 50</p>
            """

        body += "</body></html>"

        msg.attach(MIMEText(body, "html"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USER, RECIPIENT_EMAIL, msg.as_string())
        server.quit()

        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")


def on_message(ws, message):
    """Handles messages received from WebSocket."""
    data = json.loads(message)
    if "data" in data:
        for order in data["data"]:
            if order["status"] == "filled":
                print(f"📩 Order Closed: {order}")

                # Extract order details
                symbol = order["symbol"]
                last_fill_price = order["lastFillPrice"]
                side = order["side"]

                # 🔹 If this was a SELL order, place a new trailing stop BUY order
                new_order_price, new_order_quantity = None, None
                if side == "sell":
                    print(f"🔄 Placing new trailing stop BUY order for {symbol}...")
                    response_data, new_order_price, new_order_quantity = place_trailing_stop_order(symbol, last_fill_price)

                # 🔹 Send an email notification including new order details
                send_email(order, new_order_price, new_order_quantity)

                # 🔹 Send data to Azure Function Webhook
                # requests.post(WEBHOOK_URL, json=order)


def on_open(ws):
    """Authenticates and subscribes to private WebSocket channels."""
    print("🔹 Connecting to Bitget WebSocket...")

    # Step 1: Authenticate WebSocket connection
    timestamp = str(int(time.time() * 1000))
    signature = generate_signature("/user/verify", timestamp)
    auth_payload = {
        "op": "login",
        "args": [
            {
                "apiKey": API_KEY,
                "passphrase": API_PASSPHRASE,
                "timestamp": timestamp,
                "sign": signature
            }
        ]
    }
    ws.send(json.dumps(auth_payload))
    print("✅ Authentication request sent...")

    # Step 2: Subscribe to private order updates
    time.sleep(1)  # Ensure authentication completes before subscribing
    subscribe_payload = {
        "op": "subscribe",
        "args": [{"instType": "SPOT", "channel": "order"}]
    }
    ws.send(json.dumps(subscribe_payload))
    print("✅ Subscribed to private order updates!")


def on_error(ws, error):
    print(f"❌ WebSocket Error: {error}")


def on_close(ws, close_status_code, close_msg):
    print("❌ WebSocket Disconnected. Reconnecting in 5 seconds...")
    time.sleep(5)
    start_websocket()  # Reconnect automatically


def start_websocket():
    """Starts the WebSocket connection."""
    ws = websocket.WebSocketApp(
        "wss://ws.bitget.com/mix/v1/stream",
        on_message=on_message,
        on_open=on_open,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()


if __name__ == "__main__":
    print("🚀 Starting WebSocket Client for Bitget...")
    start_websocket()
