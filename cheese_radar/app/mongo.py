import os
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
import logging

load_dotenv()


class MongoDBHandler:
    """Обработчик для работы с MongoDB"""

    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self.logger = logging.getLogger(__name__)
        self._connect()

    def _connect(self):
        """Подключение к MongoDB"""
        try:
            MONGO_CONFIG = {
                "username": os.getenv("MONGO_INITDB_ROOT_USERNAME"),
                "password": os.getenv("MONGO_INITDB_ROOT_PASSWORD"),
                "host": os.getenv("MONGO_HOST", "localhost"),
                "port": int(os.getenv("MONGO_PORT", 27017)),
                "authSource": "admin",
            }

            self.logger.info(f"Подключение к MongoDB: {MONGO_CONFIG['host']}:{MONGO_CONFIG['port']}")

            self.client = MongoClient(**MONGO_CONFIG)
            self.db = self.client["prod"]
            self.collection = self.db["products"]

            # Индекс для ускорения поиска
            self.collection.create_index([
                ("store", 1),
                ("name", 1),
                ("price", 1)
            ])

            self.logger.info("Подключение к MongoDB успешно")

        except Exception as e:
            self.logger.error(f"Ошибка подключения к MongoDB: {e}")
            raise

    def save_products(self, products, store_name):
        """
        Сохраняет новые товары в MongoDB

        Returns:
            tuple: (всего_товаров, новых_добавлено)
        """
        if not products:
            return 0, 0

        try:
            total_processed = 0
            new_added = 0
            batch_to_insert = []

            for product in products:
                try:
                    total_processed += 1

                    # Проверяем уникальность
                    query = {
                        "store": store_name,
                        "name": product.get("name"),
                        "price": product.get("price")
                    }

                    exists = self.collection.find_one(query)

                    if not exists:
                        doc = {
                            **product,
                            "store": store_name,
                            "scraped_at": datetime.now(),
                            "inserted_at": datetime.now()
                        }

                        batch_to_insert.append(doc)
                        new_added += 1

                except Exception as e:
                    self.logger.error(f"[{store_name}] Ошибка обработки товара: {e}")
                    continue

            # Вставляем новые товары
            if batch_to_insert:
                result = self.collection.insert_many(batch_to_insert, ordered=False)
                self.logger.info(f"[{store_name}] В MongoDB добавлено {len(result.inserted_ids)} товаров")

            return total_processed, new_added

        except Exception as e:
            self.logger.error(f"[{store_name}] Ошибка сохранения в MongoDB: {e}")
            return 0, 0

    def get_store_products(self, store_name, limit=10000):
        """
        Получает все товары для указанного магазина

        Args:
            store_name: название магазина
            limit: максимальное количество товаров

        Returns:
            list: список товаров
        """
        if self.collection is None:  # ПРАВИЛЬНАЯ ПРОВЕРКА
            self.logger.warning("MongoDB не подключена")
            return []

        try:
            products = list(self.collection.find(
                {"store": store_name},
                {"_id": 0}  # исключаем поле _id
            ).sort("scraped_at", -1).limit(limit))

            self.logger.info(f"Загружено {len(products)} товаров для магазина {store_name}")
            return products

        except Exception as e:
            self.logger.error(f"Ошибка получения товаров для {store_name}: {e}")
            return []

    def close(self):
        """Закрыть соединение"""
        if self.client:
            try:
                self.client.close()
                self.logger.info("Соединение с MongoDB закрыто")
            except:
                pass


mongodb_handler = MongoDBHandler()