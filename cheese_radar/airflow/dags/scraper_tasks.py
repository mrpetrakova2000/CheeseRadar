import logging
import os
from time import sleep

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = f"http://{os.getenv('APP_HOST')}:5080"


def call_scraper_api(endpoint, payload=None):
    """Базовый вызов API"""
    url = f"{API_URL}/{endpoint}"

    try:
        if payload:
            response = requests.post(url, json=payload, timeout=300)
        else:
            response = requests.get(url, timeout=30)

        response.raise_for_status()
        return response.json()

    except Exception as e:
        logging.error(f"Ошибка API {endpoint}: {e}")
        raise


def scrape_magnit():
    """Скрапинг Магнита"""
    return call_scraper_api("scrape", {"store": "magnit"})
