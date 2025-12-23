import re

STORE_URLS = {
    "pyaterochka": "https://5ka.ru/catalog/syr--251C13095/",
    "magnit": "https://magnit.ru/catalog/63991-testmmsyry?shopCode={shop_code}&shopType=1",
    "perekrestok": "https://www.perekrestok.ru/cat/c/122/syr",
    "lenta": "https://lenta.com/catalog/syry-2/",
}

SELECTORS = {
    "pyaterochka": {
        "product": lambda tag: tag.get("data-qa", "")
        and re.compile(r"product-card-\d+$").match(tag.get("data-qa", "")),
        "name": ".css-ijz3vq",
        "price": ".css-1j4x839",
        "price_cents": ".css-30bcam",
        "discount": ".css-1mt5fo7",
        "rating": ".css-1seh83q",
    },
    "magnit": {
        "product": ".unit-catalog-product-preview",
        "name": ".unit-catalog-product-preview-title",
        "price": ".unit-catalog-product-preview-prices__regular",
        "discount": ".unit-catalog-product-preview__discount",
        "rating": ".unit-catalog-product-preview-rating-score",
        "weight": ".unit-catalog-product-preview-unit-value",
    },
    "perekrestok": {
        "product": ".product-card",
        "name": ".product-card__title",
        "price": ".price-new",
        "discount": ".product-card__badge",
        "rating": ".rating-value",
    },
    "lenta": {
        "product": "lu-product-card",
        "name": ".card-name_content",
        "price": ".main-price",
        "discount": ".discount-badge",
        "rating": ".rating-number",
    },
}

PAGINATION_PARAMS = {
    "pyaterochka": "?page=",
    "magnit": "&page=",
    "perekrestok": "",
    "lenta": "/page/",
}

PAGE_LOAD_PAUSE_TIME = 10
BEFORE_SCRAPE_PAUSE_TIME = 3
COOKIE_PAUSE_TIME = 0.5
SHORT_PAUSE_TIME = 2
LONG_PAUSE_TIME = 10
SCROLL_PAUSE_TIME = 3

PYATEROCHKA_TIMING = {
    "MIN_PAGE_LOAD": 12,
    "MAX_PAGE_LOAD": 25,
    "MIN_BETWEEN_PAGES": 5,
    "MAX_BETWEEN_PAGES": 15,
    "RANDOM_MOUSE_MOVE": 0.8,
    "RANDOM_SCROLL_CHANCE": 0.7,
    "MOUSE_MOVE_DELAY": 0.3,
    "MAX_PAGES_PER_SESSION": 4,
    "SESSION_BREAK_MIN": 30,
    "SESSION_BREAK_MAX": 60,
    "RANDOM_PAGE_ORDER": True,
    "CHANGE_USER_AGENT_EVERY": 2,
}

ANTI_BAN_SETTINGS = {
    "random_mouse_movements": True,
    "random_scrolls": True,
    "random_delays": True,
    "human_like_typing": False,
    "random_click_on_body": True,
    "change_viewport": True,
    "use_random_proxy": False,
    "rotate_user_agent": True,
    "simulate_reading": True,
    "random_browsing_patterns": True,
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
]

MAX_EMPTY_PAGES = 3
MAX_SCROLL_ATTEMPTS = 8
PROXY_LIST = []
