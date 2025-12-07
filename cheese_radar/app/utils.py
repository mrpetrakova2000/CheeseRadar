import logging
import time
import random
import math
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from constants import *


# Настройка логирования
def setup_logging():
    """Настраивает логирование в файл и консоль"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.handlers = []

    logger.addHandler(console_handler)

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("undetected_chromedriver").setLevel(logging.WARNING)
    logging.getLogger("websocket").setLevel(logging.WARNING)

    return logger


def get_logger(name):
    """Возвращает логгер с указанным именем"""
    return logging.getLogger(name)


def simulate_human_interaction(driver):
    """Имитация человеческого поведения через JavaScript"""
    try:
        scroll_script = """
            window.scrollBy({
                top: 200 + Math.random() * 400,
                behavior: 'smooth'
            });
        """

        for i in range(random.randint(1, 3)):
            driver.execute_script(scroll_script)
            time.sleep(random.uniform(0.8, 1.5))

            if random.random() > 0.7:
                driver.execute_script("""
                    window.scrollBy({
                        top: -100,
                        behavior: 'smooth'
                    });
                """)
                time.sleep(random.uniform(0.5, 1))

    except Exception as e:
        logging.getLogger(__name__).error(f"Ошибка при имитации взаимодействия: {e}")


def simulate_human_mouse_movement(driver):
    """Имитация человеческого движения мыши"""
    try:
        actions = ActionChains(driver)

        # Получаем размеры окна
        window_size = driver.get_window_size()
        width = window_size['width']
        height = window_size['height']

        # Генерируем случайные точки для движения мыши
        num_points = random.randint(3, 7)
        last_x, last_y = 0, 0

        for i in range(num_points):
            # Случайные координаты с плавным движением
            x = random.randint(50, width - 50)
            y = random.randint(50, height - 100)

            # Плавное движение к точке
            steps = random.randint(3, 8)
            for step in range(steps):
                step_x = last_x + (x - last_x) * (step / steps)
                step_y = last_y + (y - last_y) * (step / steps)
                actions.move_to_element_with_offset(driver.find_element(By.TAG_NAME, 'body'), step_x, step_y)
                actions.pause(random.uniform(0.01, 0.05))

            last_x, last_y = x, y

            # Пауза в конечной точке
            pause_time = random.uniform(0.1, 0.5)
            actions.pause(pause_time)

            # Иногда кликаем
            if random.random() < 0.3:
                actions.click()
                actions.pause(random.uniform(0.2, 0.8))

        actions.perform()

    except Exception as e:
        pass


def random_scroll_behavior(driver):
    """Случайный скроллинг как у человека"""
    try:
        scroll_count = random.randint(1, 4)

        for i in range(scroll_count):
            # Случайное направление (вверх или вниз)
            direction = random.choice([-1, 1])

            # Случайная величина скролла (разная для разных направлений)
            if direction == 1:  # Вниз
                scroll_amount = random.randint(300, 1000)
            else:  # Вверх
                scroll_amount = random.randint(100, 500)

            # Плавный скролл через JS с разной скоростью
            speed = random.choice(['smooth', 'auto'])
            driver.execute_script(f"""
                window.scrollBy({{
                    top: {scroll_amount * direction},
                    behavior: '{speed}'
                }});
            """)

            # Случайная пауза между скроллами (разная)
            time.sleep(random.uniform(0.5, 2.5))

            # Иногда делаем маленький обратный скролл (40% вероятность)
            if random.random() < 0.4:
                small_back = random.randint(50, 200) * -direction
                driver.execute_script(f"""
                    window.scrollBy({{
                        top: {small_back},
                        behavior: 'smooth'
                    }});
                """)
                time.sleep(random.uniform(0.2, 0.8))

        # Иногда возвращаемся к началу
        if random.random() < 0.2:
            driver.execute_script("""
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            """)
            time.sleep(random.uniform(0.5, 1.5))

    except Exception as e:
        pass


def simulate_reading_time(driver, min_time=2, max_time=5):
    """Имитация времени чтения страницы"""
    try:
        read_time = random.uniform(min_time, max_time)
        time.sleep(read_time)

        # Разные действия во время "чтения"
        actions_during_reading = random.choices(
            ["scroll", "mouse", "wait", "mini_scroll", "click"],
            weights=[0.4, 0.3, 0.2, 0.05, 0.05],
            k=random.randint(1, 3)
        )

        for action in actions_during_reading:
            if action == "scroll":
                random_scroll_behavior(driver)
            elif action == "mouse":
                simulate_human_mouse_movement(driver)
            elif action == "mini_scroll":
                driver.execute_script("window.scrollBy(0, 100);")
                time.sleep(0.3)
            elif action == "click":
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, "a, button, div[role='button']")
                    if elements:
                        random.choice(elements[:5]).click()
                        time.sleep(random.uniform(0.5, 1.5))
                except:
                    pass

    except Exception as e:
        pass


def pyaterochka_anti_ban_delay(driver, page_num=None, is_session_break=False):
    """Специальная задержка для Пятерочки с рандомизацией"""
    logger = logging.getLogger(__name__)

    try:
        if is_session_break:
            # Длительный перерыв между сессиями
            break_time = random.uniform(PYATEROCHKA_TIMING["SESSION_BREAK_MIN"],
                                        PYATEROCHKA_TIMING["SESSION_BREAK_MAX"])
            logger.info(f"[Пятерочка] Длительный перерыв между сессиями: {break_time:.1f} сек")
            time.sleep(break_time)
            return

        # Базовое время ожидания с рандомизацией
        if page_num is None or page_num == 1:
            # Для первой страницы больше времени
            base_wait = random.uniform(PYATEROCHKA_TIMING["MIN_PAGE_LOAD"],
                                       PYATEROCHKA_TIMING["MAX_PAGE_LOAD"])
            logger.info(f"[Пятерочка] Задержка для страницы: {base_wait:.1f} сек")
        else:
            # Для последующих страниц меньше времени (но с вариацией)
            base_multiplier = 0.7 + (random.random() * 0.3)  # 0.7-1.0
            base_wait = random.uniform(PYATEROCHKA_TIMING["MIN_PAGE_LOAD"],
                                       PYATEROCHKA_TIMING["MAX_PAGE_LOAD"]) * base_multiplier
            logger.info(f"[Пятерочка] Задержка для страницы {page_num}: {base_wait:.1f} сек")

        # Ждем базовое время
        time.sleep(base_wait)

        # Разные комбинации действий после загрузки
        action_combination = random.choice([
            ["mouse", "scroll", "read"],
            ["scroll", "mouse"],
            ["read", "mouse", "mini_scroll"],
            ["scroll", "read"],
            ["mouse"]
        ])

        for action in action_combination:
            if action == "mouse" and random.random() < PYATEROCHKA_TIMING["RANDOM_MOUSE_MOVE"]:
                simulate_human_mouse_movement(driver)
                time.sleep(random.uniform(0.5, 1.5))

            elif action == "scroll" and random.random() < PYATEROCHKA_TIMING["RANDOM_SCROLL_CHANCE"]:
                random_scroll_behavior(driver)
                time.sleep(random.uniform(0.5, 1.5))

            elif action == "read":
                read_extra = random.uniform(1, 4)
                time.sleep(read_extra)
                logger.debug(f"[Пятерочка] Дополнительное время чтения: {read_extra:.1f} сек")

            elif action == "mini_scroll":
                driver.execute_script("window.scrollBy(0, 150);")
                time.sleep(0.5)

    except Exception as e:
        logger.error(f"[Пятерочка] Ошибка в anti-ban задержке: {e}")
        # В случае ошибки просто ждем стандартное время
        time.sleep(PAGE_LOAD_PAUSE_TIME)


def get_random_user_agent():
    """Возвращает случайный User-Agent"""
    return random.choice(USER_AGENTS)


def change_viewport_randomly(driver):
    """Случайное изменение размера окна"""
    try:
        # Разные комбинации размеров окна
        viewport_presets = [
            (1920, 1080),  # Full HD
            (1366, 768),  # Ноутбук
            (1536, 864),  # Mac
            (1440, 900),  # iMac
            (1280, 720),  # HD
            (1024, 768),  # iPad
        ]

        width, height = random.choice(viewport_presets)

        # Добавляем небольшие случайные отклонения
        width += random.randint(-50, 50)
        height += random.randint(-50, 50)

        driver.set_window_size(width, height)
        time.sleep(random.uniform(0.5, 1.5))

        # Иногда меняем положение окна
        if random.random() < 0.3:
            driver.set_window_position(
                random.randint(0, 100),
                random.randint(0, 100)
            )
            time.sleep(0.3)

    except Exception as e:
        pass


def simulate_browsing_session(driver, duration_min=10, duration_max=30):
    """Имитация полноценной сессии просмотра"""
    logger = logging.getLogger(__name__)

    try:
        session_duration = random.uniform(duration_min, duration_max)
        logger.info(f"[Пятерочка] Имитация сессии просмотра: {session_duration:.1f} сек")

        start_time = time.time()

        while time.time() - start_time < session_duration:
            # Выбираем случайное действие
            action = random.choices(
                ["scroll", "mouse", "wait", "click", "back_forth", "search"],
                weights=[0.3, 0.25, 0.2, 0.1, 0.1, 0.05],
                k=1
            )[0]

            if action == "scroll":
                random_scroll_behavior(driver)
                time.sleep(random.uniform(1, 3))

            elif action == "mouse":
                simulate_human_mouse_movement(driver)
                time.sleep(random.uniform(0.5, 2))

            elif action == "wait":
                wait_time = random.uniform(2, 6)
                time.sleep(wait_time)

            elif action == "click":
                try:
                    # Ищем кликабельные элементы
                    clickable = driver.find_elements(
                        By.CSS_SELECTOR,
                        "a, button, [role='button'], .product-card, .category-item"
                    )
                    if clickable:
                        element = random.choice(clickable[:8])  # Берем из первых 8
                        ActionChains(driver).move_to_element(element).pause(0.3).click().perform()
                        time.sleep(random.uniform(1.5, 4))

                        # 50% вероятность вернуться назад
                        if random.random() < 0.5:
                            driver.back()
                            time.sleep(random.uniform(2, 4))
                except:
                    pass

            elif action == "back_forth":
                # Прокрутка вперед-назад
                driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(0.8)
                driver.execute_script("window.scrollBy(0, -200);")
                time.sleep(0.5)

            elif action == "search":
                # Имитация поиска
                try:
                    search_box = driver.find_elements(By.CSS_SELECTOR,
                                                      "input[type='search'], input[placeholder*='поиск']")
                    if search_box:
                        search = search_box[0]
                        ActionChains(driver).move_to_element(search).click().perform()
                        time.sleep(0.5)

                        # "Печатаем" случайный текст
                        for char in "сыр":
                            search.send_keys(char)
                            time.sleep(random.uniform(0.05, 0.15))

                        time.sleep(1)
                        search.send_keys(Keys.BACKSPACE * random.randint(1, 3))
                        time.sleep(0.5)
                except:
                    pass

    except Exception as e:
        logger.debug(f"[Пятерочка] Ошибка при имитации сессии: {e}")


def detect_blocked_page(driver):
    """Обнаружение блокировки или капчи"""
    try:
        page_source = driver.page_source.lower()

        # Признаки блокировки
        blocked_keywords = [
            "доступ ограничен",
            "blocked",
            "captcha",
            "recaptcha",
            "проверка безопасности",
            "security check",
            "робот",
            "robot",
            "подтвердите что вы не робот",
            "cloudflare"
        ]

        for keyword in blocked_keywords:
            if keyword in page_source:
                return True

        # Проверяем наличие капчи
        captcha_selectors = [
            "div[class*='captcha']",
            "iframe[src*='recaptcha']",
            "div[class*='recaptcha']",
            "div[id*='captcha']"
        ]

        for selector in captcha_selectors:
            try:
                if driver.find_elements(By.CSS_SELECTOR, selector):
                    return True
            except:
                continue

        return False

    except Exception as e:
        return False
