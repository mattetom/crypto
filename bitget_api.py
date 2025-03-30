import logging
import os
import pandas as pd
import requests

from utils import get_timestamp, parse_params_to_str, pre_hash, sign

# Get settings from environment variables
API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")
API_PASSPHRASE = os.environ.get("API_PASSPHRASE")
BITGET_API_URL = os.environ.get("BITGET_API_URL", "https://api.bitget.com")

# Funzione per ottenere dati storici da BitGet
def get_candles(symbol, interval, limit=100):
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
    response = requests.get(BITGET_API_URL + request_path, headers=headers)
    data = response.json()
    if "data" in data:
        return response.json()["data"]
    else:
        logging.error("Errore nella richiesta API: %s", data)
        return None