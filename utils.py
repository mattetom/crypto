import base64
from collections import deque
import hmac
import json
import os
import pickle
import time
import logging

import numpy as np

from azure.storage.blob import BlobServiceClient, BlobClient

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
    url = '?' + toQueryWithNoEncode(params)
    if url == '?':
        return ''
    return url


def toQueryWithNoEncode(params):
    url = ''
    for key, value in params:
        url = url + str(key) + '=' + str(value) + '&'
    return url[0:-1]


def generate_rest_signature(secret_key, method, request_path, body=None):
  logging.info(f"Generating signature for {method} {request_path}")
  timestamp = get_timestamp()
  bodyJson = json.dumps(body)
  signature = sign(pre_hash(timestamp, method, request_path, str(bodyJson)), secret_key)
  print(signature)
  return signature, timestamp



def calculate_macd_values(close_prices, fast_length, slow_length, signal_length):
    """
    Calculate MACD, Signal Line and Histogram
    
    Args:
        close_prices: numpy array of close prices
        fast_length: fast EMA period
        slow_length: slow EMA period
        signal_length: signal line EMA period
        
    Returns:
        tuple: (macd_line, signal_line, histogram)
    """
    # Calculate fast and slow EMAs
    ema_fast = calculate_ema(close_prices, fast_length)
    ema_slow = calculate_ema(close_prices, slow_length)
    
    # Calculate MACD line
    macd_line = ema_fast - ema_slow
    
    # Calculate signal line
    signal_line = calculate_ema(macd_line, signal_length)
    
    # Calculate histogram
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram

def calculate_ema(prices, period):
    """
    Calculate Exponential Moving Average
    """
    prices = np.array(prices)
    ema = np.zeros_like(prices)
    
    # Use SMA as the first value
    ema[:period] = np.mean(prices[:period])
    
    # Calculate multiplier
    multiplier = 2 / (period + 1)
    
    # Calculate EMA for the rest of the array
    for i in range(period, len(prices)):
        ema[i] = (prices[i] - ema[i-1]) * multiplier + ema[i-1]
        
    return ema


# Azure Blob Storage functions for state persistence
def get_blob_client():
    """Get a blob client for our state storage"""
    connection_string = os.environ.get("AzureWebJobsStorage")
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_name = "macd-state"
    
    # Create container if it doesn't exist
    try:
        container_client = blob_service_client.create_container(container_name)
    except:
        container_client = blob_service_client.get_container_client(container_name)
    
    return container_client.get_blob_client("macd-history")

def load_state():
    """Load MACD history from Azure Blob Storage"""
    blob_client = get_blob_client()
    
    try:
        downloaded_blob = blob_client.download_blob()
        state_data = pickle.loads(downloaded_blob.readall())
        logging.info("Successfully loaded MACD history from Blob Storage")
        return state_data
    except Exception as e:
        logging.info(f"No existing state found or error loading state: {e}")
        return {'macd_history': deque(maxlen=15), 
                'last_bullish_action_time': None, 
                'last_bearish_action_time': None}

def save_state(state_data):
    """Save MACD history to Azure Blob Storage"""
    blob_client = get_blob_client()
    
    try:
        serialized_data = pickle.dumps(state_data)
        blob_client.upload_blob(serialized_data, overwrite=True)
        logging.info("Successfully saved MACD history to Blob Storage")
    except Exception as e:
        logging.error(f"Error saving state to Blob Storage: {e}")
