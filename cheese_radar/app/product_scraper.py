import json
from datetime import datetime

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from constants import *
from mongo import mongodb_handler
from stores import *
from utils import *


class ProductScraper:
    def __init__(self, store_scraper):
        self.store = store_scraper
        self.driver = None
        self.logger = get_logger(self.__class__.__name__)

    def _setup_driver(self):
        """Настройка драйвера"""
        self.logger.info(f"[{self.store.store_name}] Настройка драйвера...")

        options = uc.ChromeOptions()

        # Основные опции
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--no-first-run")
        options.add_argument("--no-service-autorun")
        options.add_argument("--password-store=basic")
        options.add_argument("--disable-extensions")

        selected_ua = get_random_user_agent()
        options.add_argument(f"--user-agent={selected_ua}")

        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
        }
        options.add_experimental_option("prefs", prefs)

        driver = uc.Chrome(
            options=options,
            use_subprocess=True,
            headless=True,
        )

        # Устанавливаем скрипты для обхода детекции
        driver.execute_script(
            """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['ru-RU', 'ru', 'en-US', 'en']});
            window.chrome = {runtime: {}};
        """
        )

        self.logger.info(f"[{self.store.store_name}] Драйвер настроен, User-Agent: {selected_ua[:50]}...")
        return driver

    def _normal_page_load(self, url):
        """Обычная загрузка страницы магазинов"""
        self.logger.info(f"[{self.store.store_name}] Загрузка страницы: {url}")
        self.driver.get(url)
        time.sleep(PAGE_LOAD_PAUSE_TIME)
        simulate_human_interaction(self.driver)

    def _scroll_to_load_all_products(self):
        """Скроллинг для загрузки всех товаров"""
        self.logger.info(f"[{self.store.store_name}] Скроллинг для загрузки всех товаров...")

        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scroll_attempts = 8

        while scroll_attempts < max_scroll_attempts:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            self.driver.execute_script("window.scrollBy(0, -100);")
            time.sleep(random.uniform(0.5, 1))

            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                scroll_attempts += 1
                self.logger.debug(
                    f"[{self.store.store_name}] Высота не изменилась, попытка {scroll_attempts}/{max_scroll_attempts}"
                )
            else:
                scroll_attempts = 0
                last_height = new_height

            time.sleep(random.uniform(0.5, 1))

        self.logger.info(f"[{self.store.store_name}] Скроллинг завершен")

    def _load_existing_products_from_mongo(self):
        """Загружает существующие товары из MongoDB"""
        all_products = []

        try:
            # Получаем все товары для этого магазина из MongoDB
            existing_products = mongodb_handler.get_store_products(self.store.store_name)

            if not existing_products:
                self.logger.info(f"[{self.store.store_name}] В MongoDB нет товаров для магазина {self.store.store_name}")
                return all_products

            self.logger.info(f"[{self.store.store_name}] Загружено {len(existing_products)} существующих товаров из MongoDB")

            for product in existing_products:
                try:
                    name = product.get("name", "").strip()
                    price = str(product.get("price", "")).strip()
                    store = str(product.get("store", "")).strip()
                    date_time = str(product.get("date_time", "")).strip()

                    if name and price and store:
                        # Сохраняем продукт для возврата
                        all_products.append(
                            {
                                "name": name,
                                "price": price,
                                "store": store,
                                "date_time": date_time,
                                "discount": product.get("discount"),
                                "rating": product.get("rating"),
                            }
                        )

                except Exception as e:
                    self.logger.error(f"[{self.store.store_name}] Ошибка при обработке существующего товара из MongoDB: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"[{self.store.store_name}] Ошибка загрузки из MongoDB: {e}")
            all_products = []

        return all_products

    def _parse_single_page(self):
        """Парсинг одной страницы"""
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        soup = BeautifulSoup(self.driver.page_source, "html.parser")

        # Проверяем, является ли селектор функцией или строкой
        if callable(self.store.product_selector):
            products = soup.find_all(self.store.product_selector)
        else:
            products = soup.select(self.store.product_selector)

        self.logger.info(f"[{self.store.store_name}] Найдено элементов на странице: {len(products)}")

        parsed_products = []

        for item in products:
            try:
                # Имя товара
                name_elem = item.select_one(self.store.name_selector)
                name = name_elem.text.strip() if name_elem else None

                # Цена товара
                price_elem = item.select_one(self.store.price_selector)
                price_str = price_elem.text.strip() if price_elem else None

                price = price_str

                # Скидка
                discount_elem = item.select_one(self.store.discount_selector)
                discount = discount_elem.text.strip() if discount_elem else None

                # Рейтинг
                rating_elem = item.select_one(self.store.rating_selector)
                rating = rating_elem.text.strip() if rating_elem else None

                # Вес (если есть)
                weight_elem = item.select_one(self.store.weight_selector)
                weight = weight_elem.text.strip() if weight_elem else ""

                # Проверяем обязательные поля
                if name is None or price is None:
                    continue

                parsed_products.append(
                    {
                        "name": name + " " + weight,
                        "price": price,
                        "discount": discount,
                        "rating": rating,
                        "date_time": current_datetime,
                        "store": self.store.store_name,
                    }
                )

            except Exception as e:
                self.logger.debug(f"[{self.store.store_name}] Ошибка при парсинге товара: {e}")
                continue

        return parsed_products

    def scrape(self):
        """Основной метод скрейпинга с использованием MongoDB"""
        seen_products = set()

        try:
            # Загружаем существующие товары из MongoDB
            all_products = self._load_existing_products_from_mongo()

            # Инициализация драйвера
            self.driver = self._setup_driver()

            # Выполняем before_scrape подготовку
            self.store.before_scrape(self.driver)

            new_products_total = 0
            scraped_products = []

            if isinstance(self.store, (MagnitScraper, LentaScraper)):
                page = 1
                max_empty_pages = 2
                empty_pages_count = 0

                while empty_pages_count < max_empty_pages:
                    url = self.store.get_url(page)

                    try:
                        self._normal_page_load(url)

                        parsed_products = self._parse_single_page()

                        if not parsed_products:
                            empty_pages_count += 1
                            self.logger.info(f"[{self.store.store_name}] Пустая страница ({empty_pages_count}/{max_empty_pages})")
                        else:
                            empty_pages_count = 0

                            for product in parsed_products:
                                product_key = f"{product['name']}_{product['price']}_{product['store']}"

                                if not product_key or product_key in seen_products:
                                    continue

                                seen_products.add(product_key)
                                all_products.append(product)
                                scraped_products.append(product)
                                new_products_total += 1

                            self.logger.info(
                                f"[{self.store.store_name}] Страница {page} загружена, новых товаров: {len(parsed_products)}"
                            )

                        page += 1
                        time.sleep(random.uniform(SHORT_PAUSE_TIME - 1, SHORT_PAUSE_TIME + 1))

                    except Exception as e:
                        self.logger.error(f"[{self.store.store_name}] Ошибка на странице {page}: {e}")
                        empty_pages_count += 1
                        page += 1
                        time.sleep(LONG_PAUSE_TIME)

            # Для Перекрёстка
            elif isinstance(self.store, PerekrestokScraper):
                page = 1
                empty_pages_count = 0
                max_empty_pages = 1

                url = self.store.get_url(page)
                self.logger.info(f"[{self.store.store_name}] Запрос страницы {page}: {url}")

                try:
                    self._scroll_to_load_all_products()
                    parsed_products = self._parse_single_page()

                    if not parsed_products:
                        empty_pages_count += 1
                        self.logger.info(f"[{self.store.store_name}] Пустая страница ({empty_pages_count}/{max_empty_pages})")
                    else:
                        empty_pages_count = 0

                        for product in parsed_products:
                            product_key = f"{product['name']}_{product['price']}_{product['store']}"

                            if not product_key or product_key in seen_products:
                                continue

                            seen_products.add(product_key)
                            all_products.append(product)
                            scraped_products.append(product)
                            new_products_total += 1

                        self.logger.info(
                            f"[{self.store.store_name}] Страница {page} загружена, новых товаров: {len(parsed_products)}"
                        )

                        page += 1
                        time.sleep(random.uniform(SHORT_PAUSE_TIME - 1, SHORT_PAUSE_TIME + 1))
                except Exception as e:
                    self.logger.error(f"[{self.store.store_name}] Ошибка на странице {page}: {e}")
                    empty_pages_count += 1
                    page += 1
                    time.sleep(LONG_PAUSE_TIME)

            # Сохранение новых товаров в MongoDB
            if scraped_products:
                mongo_processed, mongo_new = mongodb_handler.save_products(scraped_products, self.store.store_name)
                self.logger.info(f"[{self.store.store_name}] В MongoDB добавлено {mongo_new} новых товаров")
            else:
                mongo_processed, mongo_new = 0, 0
                self.logger.warning(f"[{self.store.store_name}] Нет новых товаров для сохранения")

            self.logger.info(f"[{self.store.store_name}] ИТОГИ:")
            self.logger.info(f"[{self.store.store_name}]   Всего в базе: {len(all_products)} товаров")
            self.logger.info(f"[{self.store.store_name}]   Найдено новых: {new_products_total}")
            self.logger.info(f"[{self.store.store_name}]   Сохранено в MongoDB: {mongo_new}")

            return len(all_products), mongo_new

        except Exception as e:
            self.logger.error(f"[{self.store.store_name}] Критическая ошибка: {e}")
            raise
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    self.logger.info(f"[{self.store.store_name}] Драйвер закрыт")
                except:
                    pass

        return len(all_products), new_products_total
