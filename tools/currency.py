#!/usr/bin/env python3

import os
import time
import json
import requests
import argh

CACHE_FILE = os.path.join(os.path.expanduser('~'), '.currency_cache.json')
CACHE_EXPIRY = 3600  # cache expiry time in seconds (1 hour)
API_URL = "https://openexchangerates.org/api/latest.json"
APP_ID = os.getenv('OPENEXCHANGERATES_APP_ID')

def fetch_rates():
    if not APP_ID:
        raise EnvironmentError("OPENEXCHANGERATES_APP_ID environment variable is not set")

    response = requests.get(f"{API_URL}?app_id={APP_ID}")
    if response.status_code != 200:
        raise Exception("Error fetching rates from Open Exchange Rates API")

    data = response.json()
    rates = data.get('rates', {})
    with open(CACHE_FILE, 'w') as f:
        cache_data = {
            'timestamp': time.time(),
            'rates': rates
        }
        json.dump(cache_data, f)
    return rates

def get_rates():
    try:
        with open(CACHE_FILE, 'r') as f:
            cache_data = json.load(f)
            if time.time() - cache_data['timestamp'] < CACHE_EXPIRY:
                return cache_data['rates']
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    return fetch_rates()

def convert_currency(amount, from_currency, to_currency):
    rates = get_rates()
    if from_currency != 'USD':
        if from_currency not in rates:
            raise ValueError(f"Rate for {from_currency} not available")
        amount = amount / rates[from_currency]
    if to_currency not in rates:
        raise ValueError(f"Rate for {to_currency} not available")
    return amount * rates[to_currency]

def main(amount: float, from_currency: str = "usd", to_currency: str = "aud", verbose: bool = False):
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    result = convert_currency(amount, from_currency, to_currency)
    if verbose:
        print(f"{amount} {from_currency} is {result:.2f} {to_currency}")
    else:
        print(f"{result:.2f}")

if __name__ == "__main__":
    argh.dispatch_command(main)
