from abc import ABC
import os
from dotenv import load_dotenv

from utils import *

load_dotenv()

class StoreScraper(ABC):
    def __init__(self):
        self.store_name = ""
        self.base_url = ""
        self.product_selector = ""
        self.name_selector = ""
        self.price_selector = ""
        self.page_param = ""
        self.discount_selector = ""
        self.rating_selector = ""
        self.price_cents_selector = None
        self.SESSION_COOKIE = None
        self.logger = get_logger(self.__class__.__name__)

    def get_url(self, page: int) -> str:
        if page == 1:
            return self.base_url
        return f"{self.base_url}{self.page_param}{page}"

    def before_scrape(self, driver):
        """Настройка перед скрейпингом. Можно переопределить."""
        pass


class MagnitScraper(StoreScraper):
    def __init__(self):
        super().__init__()
        self.store_name = "Магнит"
        shop_code = os.getenv("MAGNIT_SHOP_CODE", "161924")
        self.base_url = STORE_URLS["magnit"].format(shop_code=shop_code)
        self.product_selector = SELECTORS["magnit"]["product"]
        self.name_selector = SELECTORS["magnit"]["name"]
        self.price_selector = SELECTORS["magnit"]["price"]
        self.discount_selector = SELECTORS["magnit"]["discount"]
        self.rating_selector = SELECTORS["magnit"]["rating"]
        self.page_param = PAGINATION_PARAMS["magnit"]

    def before_scrape(self, driver):
        """Настройка города и магазина для Магнита"""
        self.logger.info(f"[{self.store_name}] Настраиваем город и магазин для Магнита...")

        driver.get("https://magnit.ru/")
        time.sleep(SHORT_PAUSE_TIME)

        shop_code = os.getenv("MAGNIT_SHOP_CODE", "161924")
        try:
            driver.add_cookie({
                "name": "shopCode",
                "value": shop_code,
                "domain": ".magnit.ru",
                "path": "/"
            })
            time.sleep(COOKIE_PAUSE_TIME)
        except Exception as e:
            self.logger.error(f"[{self.store_name}] Не удалось установить cookie shopCode: {e}")

        driver.refresh()
        time.sleep(SHORT_PAUSE_TIME)
        self.logger.info(f"[{self.store_name}] Настройка Магнита завершена")


class PerekrestokScraper(StoreScraper):
    def __init__(self):
        super().__init__()
        self.store_name = "Перекрёсток"
        self.base_url = STORE_URLS["perekrestok"]
        self.product_selector = SELECTORS["perekrestok"]["product"]
        self.name_selector = SELECTORS["perekrestok"]["name"]
        self.price_selector = SELECTORS["perekrestok"]["price"]
        self.discount_selector = SELECTORS["perekrestok"]["discount"]
        self.rating_selector = SELECTORS["perekrestok"]["rating"]
        self.page_param = PAGINATION_PARAMS["perekrestok"]
        self.SESSION_COOKIE = os.getenv("PEREKRESTOK_SESSION_COOKIE")

    def before_scrape(self, driver):
        """Настройка сессии для Перекрёстка"""
        self.logger.info(f"[{self.store_name}] Подготовка сессии для Перекрёстка...")

        if not self.SESSION_COOKIE:
            raise ValueError("SESSION_COOKIE не установлена для Перекрёстка")

        driver.get("https://www.perekrestok.ru/")
        time.sleep(PAGE_LOAD_PAUSE_TIME)

        try:
            driver.add_cookie({
                "name": "session",
                "value": self.SESSION_COOKIE,
                "domain": "www.perekrestok.ru",
                "path": "/",
                "secure": True,
                "httpOnly": False
            })
            self.logger.info(f"[{self.store_name}] Cookie успешно вставлена")
        except Exception as e:
            self.logger.error(f"[{self.store_name}] Не удалось вставить cookie: {e}")
            raise

        driver.refresh()
        time.sleep(BEFORE_SCRAPE_PAUSE_TIME)

        driver.get(self.base_url)
        time.sleep(PAGE_LOAD_PAUSE_TIME)

        # Проверка доступа
        page_source = driver.page_source.lower()
        if "forbidden" in page_source or "проверка безопасности" in page_source:
            self.logger.error(f"[{self.store_name}] 403! Cookie устарела — обнови её вручную в браузере")
            raise Exception("Cookie мертва")
        else:
            self.logger.info(f"[{self.store_name}] Начало парсинга")

        # Скроллинг для загрузки всех товаров
        for _ in range(6):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE_TIME)


class LentaScraper(StoreScraper):
    def __init__(self):
        super().__init__()
        self.store_name = "Лента"
        self.base_url = STORE_URLS["lenta"]
        self.product_selector = SELECTORS["lenta"]["product"]
        self.name_selector = SELECTORS["lenta"]["name"]
        self.price_selector = SELECTORS["lenta"]["price"]
        self.discount_selector = SELECTORS["lenta"]["discount"]
        self.rating_selector = SELECTORS["lenta"]["rating"]
        self.page_param = PAGINATION_PARAMS["lenta"]

    def get_url(self, page: int) -> str:
        if page == 1:
            return self.base_url
        else:
            return f"{self.base_url}page/{page}/"

    def before_scrape(self, driver):
        """Настройка сессии для Ленты с полным набором куки и headers"""
        self.logger.info(f"[{self.store_name}] Настройка сессии для Ленты...")

        try:
            # Первая загрузка для инициализации
            driver.get("https://www.google.com/")
            time.sleep(SHORT_PAUSE_TIME)

            # Устанавливаем дополнительные headers через JavaScript
            driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['ru-RU', 'ru', 'en-US', 'en']});
                
                // Добавляем дополнительные свойства для обхода защиты
                window.chrome = {runtime: {}};
                
                // Меняем User-Agent если нужно
                const originalUserAgent = navigator.userAgent;
                Object.defineProperty(navigator, 'userAgent', {
                    get: () => {
                        return originalUserAgent.replace(/HeadlessChrome\\/[\\d.]+/, 'Chrome/');
                    }
                });
            """)

            # Основная страница Ленты
            driver.get("https://lenta.com/")
            time.sleep(PAGE_LOAD_PAUSE_TIME)

            self.logger.info(f"[{self.store_name}] Установка cookies...")

            # Расширенный набор cookies для Ленты
            cookies_to_set = [
                {
                    "name": "citySlug",
                    "value": "spb",
                    "domain": ".lenta.com",
                    "path": "/",
                    "secure": True,
                    "httpOnly": False
                },
                {
                    "name": "App_Cache_CitySlug",
                    "value": "spb",
                    "domain": ".lenta.com",
                    "path": "/"
                },
                {
                    "name": "App_Cache_City",
                    "value": """{"centerLat":"59.93909600","centerLng":"30.31587100","id":3,"isDefault":false,"mainDomain":false,"name":"Санкт-Петербург и область","slug":"spb"}""",
                    "domain": ".lenta.com",
                    "path": "/"
                },
                {
                    "name": "App_Cache_MissionAddressMode",
                    "value": """{"t":"pickup","ids":false,"ma":{"i":3241,"a":"0214","t":"TK214","af":"Санкт-Петербург, п. Бугры, Южная ул., 5","ri":3,"mt":"HM","s":false}}""",
                    "domain": ".lenta.com",
                    "path": "/"
                },
                {
                    "name": "_ga",
                    "value": "GA1.1." + str(random.randint(1000000000, 9999999999)) + "." + str(int(time.time())),
                    "domain": ".lenta.com",
                    "path": "/"
                },
                {
                    "name": "_gid",
                    "value": "GA1.1." + str(random.randint(1000000000, 9999999999)) + "." + str(int(time.time())),
                    "domain": ".lenta.com",
                    "path": "/"
                },
                {
                    "name": "_gat",
                    "value": "1",
                    "domain": ".lenta.com",
                    "path": "/"
                }
            ]

            for cookie in cookies_to_set:
                try:
                    driver.add_cookie(cookie)
                    self.logger.debug(f"[{self.store_name}] Установлен cookie: {cookie['name']}")
                    time.sleep(random.uniform(0.1, 0.3))
                except Exception as e:
                    self.logger.error(f"[{self.store_name}] Не удалось установить cookie {cookie['name']}: {e}")

            self.logger.info(f"[{self.store_name}] Обновление страницы...")
            driver.refresh()
            time.sleep(PAGE_LOAD_PAUSE_TIME * 1.5)

            # Имитация человеческого поведения
            self._simulate_human_behavior(driver)

            # Проверяем успешность загрузки
            page_source = driver.page_source
            if "403" in page_source or "Forbidden" in page_source or "Доступ запрещен" in page_source:
                self.logger.warning(f"[{self.store_name}] Обнаружена ошибка 403, пробуем обойти...")
                self._bypass_403(driver)

        except Exception as e:
            self.logger.error(f"[{self.store_name}] Ошибка в настройке сессии: {e}")
            # Пробуем продолжить, возможно страница все равно загрузится

    def _simulate_human_behavior(self, driver):
        """Имитация человеческого поведения"""
        try:
            # Плавный скролл
            scroll_steps = [300, 500, 200, 400, 600]

            for step in scroll_steps:
                driver.execute_script(f"""
                    window.scrollBy({{
                        top: {step},
                        behavior: 'smooth'
                    }});
                """)
                time.sleep(random.uniform(0.5, 1.5))

            # Возвращаемся немного назад
            driver.execute_script("window.scrollTo({top: 200, behavior: 'smooth'});")
            time.sleep(1)

            # Имитация движения мыши
            actions = ActionChains(driver)
            window_size = driver.get_window_size()

            # Случайные движения мыши
            for _ in range(3):
                x = random.randint(50, window_size['width'] - 50)
                y = random.randint(50, window_size['height'] - 100)
                actions.move_by_offset(x, y)
                actions.pause(random.uniform(0.1, 0.5))

            actions.perform()

        except Exception as e:
            self.logger.debug(f"[{self.store_name}] Ошибка при имитации поведения: {e}")

    def _bypass_403(self, driver):
        """Попытка обойти 403 ошибку"""
        try:
            self.logger.info(f"[{self.store_name}] Попытка обхода 403 ошибки...")

            # 1. Меняем User-Agent
            new_ua = get_random_user_agent()
            driver.execute_script(f"""
                Object.defineProperty(navigator, 'userAgent', {{
                    get: () => '{new_ua}'
                }});
            """)
            self.logger.info(f"[{self.store_name}] User-Agent изменен на: {new_ua[:50]}...")

            # 2. Меняем размер окна
            change_viewport_randomly(driver)

            # 3. Длительная пауза
            time.sleep(random.uniform(10, 20))

            # 4. Переходим через Google
            driver.get("https://www.google.com/search?q=lenta+сыры")
            time.sleep(3)

            # Ищем ссылку на Ленту в результатах поиска
            try:
                lenta_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='lenta.com']")
                if lenta_links:
                    lenta_links[0].click()
                    time.sleep(5)
            except:
                # Если не нашли, грузим напрямую
                driver.get(self.base_url)
                time.sleep(5)

            # 5. Добавляем Referer header через JavaScript
            driver.execute_script("""
                // Создаем XMLHttpRequest с нужными headers
                const oldSend = XMLHttpRequest.prototype.send;
                XMLHttpRequest.prototype.send = function(body) {
                    this.setRequestHeader('Referer', 'https://www.google.com/');
                    this.setRequestHeader('Accept-Language', 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7');
                    this.setRequestHeader('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8');
                    oldSend.call(this, body);
                };
                
                // Также для fetch
                const oldFetch = window.fetch;
                window.fetch = function(...args) {
                    if (args[1]) {
                        args[1].headers = {
                            ...args[1].headers,
                            'Referer': 'https://www.google.com/',
                            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
                        };
                    }
                    return oldFetch.apply(this, args);
                };
            """)

            self.logger.info(f"[{self.store_name}] Завершена попытка обхода 403")

        except Exception as e:
            self.logger.error(f"[{self.store_name}] Ошибка при обходе 403: {e}")