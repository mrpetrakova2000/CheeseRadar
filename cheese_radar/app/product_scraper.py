import json
from datetime import datetime
from bs4 import BeautifulSoup
import undetected_chromedriver as uc

from stores import *
from utils import *
from constants import *


class ProductScraper:
    def __init__(self, store_scraper):
        self.store = store_scraper
        self.driver = None
        self.json_filename = f"data/{self.store.store_name}_products.json"
        self.logger = get_logger(self.__class__.__name__)

    def _setup_driver(self):
        """Настройка драйвера с улучшенной защитой"""
        self.logger.info(f"[{self.store.store_name}] Настройка драйвера...")

        options = uc.ChromeOptions()

        # Основные опции
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--no-first-run')
        options.add_argument('--no-service-autorun')
        options.add_argument('--password-store=basic')
        options.add_argument('--disable-extensions')

        # Случайный User-Agent
        selected_ua = get_random_user_agent()
        options.add_argument(f'--user-agent={selected_ua}')

        # Предпочтения
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
        driver.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['ru-RU', 'ru', 'en-US', 'en']});
            window.chrome = {runtime: {}};
        """)

        self.logger.info(f"[{self.store.store_name}] Драйвер настроен, User-Agent: {selected_ua[:50]}...")
        return driver

    def _pyaterochka_page_load(self, url, page_num=None):
        """Специальная загрузка страницы для Пятерочки"""
        self.logger.info(f"[{self.store.store_name}] Загрузка страницы {page_num if page_num else ''}: {url}")

        try:
            self.driver.get(url)

            # Специальная задержка с анти-бан защитой
            pyaterochka_anti_ban_delay(self.driver, page_num)

            # Дополнительное человеческое поведение
            if random.random() < 0.6:
                simulate_human_mouse_movement(self.driver)

            if random.random() < 0.5:
                random_scroll_behavior(self.driver)

            # Проверяем не заблокировали ли нас
            page_source = self.driver.page_source.lower()
            if "доступ ограничен" in page_source or "blocked" in page_source or "captcha" in page_source:
                self.logger.warning(f"[{self.store.store_name}] Возможная блокировка обнаружена")
                # Делаем дополнительную паузу и пробуем обойти
                time.sleep(random.uniform(10, 20))

                # Пробуем другой User-Agent
                new_ua = get_random_user_agent()
                self.driver.execute_script(f"Object.defineProperty(navigator, 'userAgent', {{get: () => '{new_ua}'}});")

                # Перезагружаем страницу
                self.driver.refresh()
                time.sleep(random.uniform(5, 10))

        except Exception as e:
            self.logger.error(f"[{self.store.store_name}] Ошибка при загрузке страницы: {e}")
            raise

    def _normal_page_load(self, url):
        """Обычная загрузка страницы для других магазинов"""
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

            # Для Пятерочки рандомная задержка
            # if isinstance(self.store, PyaterochkaScraper):
            #     time.sleep(random.uniform(1.5, 3.5))
            # else:
            #     time.sleep(random.uniform(1.5, 2.5))

            self.driver.execute_script("window.scrollBy(0, -100);")
            time.sleep(random.uniform(0.5, 1))

            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                scroll_attempts += 1
                self.logger.debug(
                    f"[{self.store.store_name}] Высота не изменилась, попытка {scroll_attempts}/{max_scroll_attempts}")
            else:
                scroll_attempts = 0
                last_height = new_height

            time.sleep(random.uniform(0.5, 1))

        self.logger.info(f"[{self.store.store_name}] Скроллинг завершен")

    def _load_existing_products(self):
        """Загружает существующие товары из JSON"""
        all_products = []
        seen_products = set()

        if not os.path.exists(self.json_filename):
            self.logger.info(f"[{self.store.store_name}] Файл {self.json_filename} не существует, создаем новый")
            return all_products, seen_products

        try:
            with open(self.json_filename, 'r', encoding='utf-8') as jsonfile:
                content = jsonfile.read().strip()

                if not content:
                    self.logger.info(f"[{self.store.store_name}] Файл {self.json_filename} пуст")
                    return all_products, seen_products

                all_products = json.loads(content)

                # Проверяем, что это список
                if not isinstance(all_products, list):
                    self.logger.warning(f"[{self.store.store_name}] Неверный формат JSON, ожидался список")
                    all_products = []
                else:
                    self.logger.info(f"[{self.store.store_name}] Загружено {len(all_products)} существующих товаров")

                    for product in all_products:
                        try:
                            name = product.get('name', '').strip()
                            price = str(product.get('price', '')).strip()
                            store = str(product.get('store', '')).strip()
                            date_time = str(product.get('date_time', '')).strip()

                            if name and price and store and date_time:
                                key = f"{name}_{price}_{store}_{date_time}"
                                seen_products.add(key)
                        except Exception as e:
                            self.logger.error(
                                f"[{self.store.store_name}] Ошибка при обработке существующего товара: {e}")
                            continue

        except json.JSONDecodeError as e:
            self.logger.error(f"[{self.store.store_name}] Ошибка декодирования JSON: {e}")
            all_products = []
        except Exception as e:
            self.logger.error(f"[{self.store.store_name}] Ошибка при загрузке JSON: {e}")
            all_products = []

        return all_products, seen_products

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

                # Проверяем обязательные поля
                if name is None or price is None:
                    continue

                parsed_products.append({
                    "name": name,
                    "price": price,
                    "discount": discount,
                    "rating": rating,
                    "date_time": current_datetime,  # Записываем точное время парсинга
                    "store": self.store.store_name
                })

            except Exception as e:
                self.logger.debug(f"[{self.store.store_name}] Ошибка при парсинге товара: {e}")
                continue

        return parsed_products

    def scrape_to_json(self):
        """Основной метод скрейпинга"""
        all_products = []
        seen_products = set()

        try:
            # Загружаем существующие товары
            all_products, seen_products = self._load_existing_products()

            # Инициализация драйвера
            self.driver = self._setup_driver()

            # Выполняем before_scrape подготовку
            self.store.before_scrape(self.driver)

            new_products_total = 0

            # Для магазинов с пагинацией
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
                            self.logger.info(
                                f"[{self.store.store_name}] Пустая страница ({empty_pages_count}/{max_empty_pages})")
                        else:
                            empty_pages_count = 0

                            for product in parsed_products:
                                # Используем имя, цену и магазин для сравнения
                                product_key = f"{product['name']}_{product['price']}_{product['store']}"

                                if not product_key or product_key in seen_products:
                                    continue

                                seen_products.add(product_key)
                                all_products.append(product)
                                new_products_total += 1
                                self.logger.debug(
                                    f"[{self.store.store_name}] Добавлен новый товар: {product['name'][:50]}... - {product['price']} руб. ({product['date_time']})")

                            self.logger.info(
                                f"[{self.store.store_name}] Страница {page} загружена, новых товаров: {len(parsed_products)}")

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
                        self.logger.info(
                            f"[{self.store.store_name}] Пустая страница ({empty_pages_count}/{max_empty_pages})")
                    else:
                        empty_pages_count = 0

                        for product in parsed_products:
                            product_key = f"{product['name']}_{product['price']}_{product['store']}"

                            if not product_key or product_key in seen_products:
                                continue

                            seen_products.add(product_key)
                            all_products.append(product)
                            new_products_total += 1
                            # self.logger.info(
                            #     f"[{self.store.store_name}] Добавлен товар: {product['name'][:50]}... - {product['price']} руб.")

                        self.logger.info(
                            f"[{self.store.store_name}] Страница {page} загружена, новых товаров: {len(parsed_products)}")

                        page += 1
                        time.sleep(random.uniform(SHORT_PAUSE_TIME - 1, SHORT_PAUSE_TIME + 1))
                except Exception as e:
                    self.logger.error(f"[{self.store.store_name}] Ошибка на странице {page}: {e}")
                    empty_pages_count += 1
                    page += 1
                    time.sleep(LONG_PAUSE_TIME)

            # Сохранение результатов
            try:
                # Сортируем товары по дате (новые сверху)
                all_products.sort(key=lambda x: x.get('date_time', ''), reverse=True)

                with open(self.json_filename, 'w', encoding='utf-8') as jsonfile:
                    json.dump(all_products, jsonfile, ensure_ascii=False, indent=2)

                self.logger.info(f"[{self.store.store_name}] Данные сохранены в {self.json_filename}")
                self.logger.info(f"[{self.store.store_name}] Всего товаров: {len(all_products)}")
                self.logger.info(f"[{self.store.store_name}] Новых добавлено: {new_products_total}")

                # Записываем статистику в лог
                if all_products:
                    # Берем самую свежую дату
                    latest_date = max([p.get('date_time', '') for p in all_products if p.get('date_time')])
                    self.logger.info(f"[{self.store.store_name}] Самая свежая запись: {latest_date}")

            except Exception as e:
                self.logger.error(f"[{self.store.store_name}] Ошибка при сохранении JSON: {e}")

                try:
                    temp_filename = f"{self.json_filename}.temp"
                    with open(temp_filename, 'w', encoding='utf-8') as jsonfile:
                        json.dump(all_products, jsonfile, ensure_ascii=False, indent=2)
                    self.logger.info(f"[{self.store.store_name}] Данные сохранены во временный файл: {temp_filename}")
                except:
                    self.logger.error(f"[{self.store.store_name}] Не удалось сохранить даже во временный файл")

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