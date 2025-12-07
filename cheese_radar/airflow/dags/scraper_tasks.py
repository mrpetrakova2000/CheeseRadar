import requests
import logging
from time import sleep

API_URL = "http://host.docker.internal:8081"


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


def scrape_perekrestok():
    """Скрапинг Перекрестка"""
    sleep(5)
    return call_scraper_api("scrape", {"store": "perekrestok"})
