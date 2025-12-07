import os
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
import logging

load_dotenv()


class MongoDBHandler:
    """Обработчик для работы с MongoDB - всегда пишет все данные"""

    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self.logger = logging.getLogger(__name__)
        self._connect()

    def _connect(self):
        """Подключение к MongoDB"""
        try:
            username = os.getenv("MONGO_INITDB_ROOT_USERNAME")
            password = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
            host = os.getenv("MONGO_HOST", "localhost")
            port = int(os.getenv("MONGO_PORT", 27017))

            self.logger.info(f"Подключение к MongoDB: {host}:{port}")

            self.client = MongoClient(
                host=host,
                port=port,
                username=username,
                password=password
            )
            self.db = self.client["prod"]
            self.collection = self.db["products"]

            self.logger.info("Подключение к MongoDB успешно")

        except Exception as e:
            self.logger.error(f"Ошибка подключения к MongoDB: {e}")
            raise

    def save_products(self, products, store_name):
        """
        Сохраняет все товары в MongoDB

        Returns:
            tuple: (всего товаров, сохранено товаров)
        """
        if not products:
            self.logger.info(f"[{store_name}] Нет товаров для сохранения")
            return 0, 0

        try:
            total_processed = len(products)
            batch_to_insert = []
            now = datetime.now()

            for product in products:
                try:
                    doc = {
                        **product,
                        "store": store_name,
                        "scraped_at": now
                    }

                    batch_to_insert.append(doc)

                except Exception as e:
                    self.logger.error(f"[{store_name}] Ошибка обработки товара: {e}")
                    continue

            if batch_to_insert:
                result = self.collection.insert_many(batch_to_insert, ordered=False)
                self.logger.info(f"[{store_name}] В MongoDB записано {len(result.inserted_ids)} товаров")
                return total_processed, len(result.inserted_ids)

            return total_processed, 0

        except Exception as e:
            self.logger.error(f"[{store_name}] Ошибка сохранения в MongoDB: {e}")
            return 0, 0

    def get_store_products(self, store_name, limit=10000):
        """Получает все товары для указанного магазина"""
        if self.collection is None:
            self.logger.warning("MongoDB не подключена")
            return []

        try:
            products = list(self.collection.find(
                {"store": store_name},
                {"_id": 0}
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
