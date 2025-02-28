import base64
import hmac
import json
import logging
import time
import azure.functions as func
import requests

app = func.FunctionApp()

API_KEY = ""
API_SECRET = ""
API_PASSPHRASE = ""

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

def get_futures_open_positions():
    url = "https://api.bitget.com/api/v2/futures/positions"

    signature, timestamp = generate_rest_signature(API_SECRET, "GET", "/api/v2/futures/positions")

    headers = {
        "Content-Type": "application/json",
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": str(timestamp)
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"Failed to fetch futures open positions: {response.status_code}")
        return None

@app.function_name(name="orders_check")
@app.timer_trigger(schedule="0 */1 * * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def orders_check(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')

    positions = get_futures_open_positions()
    if positions:
        logging.info(f"Fetched futures open positions: {positions}")

    logging.info('Python timer trigger function executed.')