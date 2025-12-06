import os
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
import logging

load_dotenv()


class MongoDBHandler:
    """Обработчик для работы с MongoDB (только запись новых данных)"""

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
            self.db = self.client["product_scraper"]
            self.collection = self.db["products"]  # Одна коллекция для всех

            # Индекс для ускорения проверки существования
            self.collection.create_index([
                ("store", 1),
                ("name", 1),
                ("price", 1)
            ])

            self.logger.info("Подключение к MongoDB успешно")

        except Exception as e:
            self.logger.error(f"Ошибка подключения к MongoDB: {e}")
            self.client = None
            self.db = None
            self.collection = None

    def save_products(self, products, store_name):
        """
        Сохраняет новые товары в MongoDB

        Args:
            products: список товаров для сохранения
            store_name: название магазина

        Returns:
            tuple: (всего_обработано, новых_добавлено)
        """
        if not self.collection or not products:
            self.logger.warning(f"[{store_name}] MongoDB не доступна или нет товаров")
            return 0, 0

        try:
            total_processed = 0
            new_added = 0
            batch_to_insert = []

            for product in products:
                try:
                    total_processed += 1

                    # Проверяем уникальность по store+name+price
                    query = {
                        "store": store_name,
                        "name": product.get("name"),
                        "price": product.get("price")
                    }

                    # Проверяем существует ли уже такой товар
                    exists = self.collection.find_one(query)

                    if not exists:
                        # Подготовка документа для вставки
                        doc = {
                            **product,
                            "store": store_name,
                            "scraped_at": datetime.now(),
                            "inserted_at": datetime.now(),
                            "is_new": True
                        }

                        batch_to_insert.append(doc)
                        new_added += 1

                except Exception as e:
                    self.logger.error(f"[{store_name}] Ошибка обработки товара: {e}")
                    continue

            # Массовая вставка новых товаров
            if batch_to_insert:
                try:
                    result = self.collection.insert_many(batch_to_insert, ordered=False)
                    self.logger.info(f"[{store_name}] В MongoDB добавлено {len(result.inserted_ids)} новых товаров")
                except Exception as e:
                    # Частичная вставка, но логируем ошибку
                    self.logger.error(f"[{store_name}] Ошибка при массовой вставке: {e}")
                    # Пробуем вставлять по одному
                    for doc in batch_to_insert:
                        try:
                            self.collection.insert_one(doc)
                        except:
                            continue

            self.logger.info(f"[{store_name}] MongoDB: обработано {total_processed}, новых {new_added}")
            return total_processed, new_added

        except Exception as e:
            self.logger.error(f"[{store_name}] Ошибка сохранения в MongoDB: {e}")
            return 0, 0

    def get_store_stats(self, store_name):
        """Получить статистику по магазину"""
        if not self.collection:
            return {}

        try:
            pipeline = [
                {"$match": {"store": store_name}},
                {"$group": {
                    "_id": "$store",
                    "total": {"$sum": 1},
                    "new": {"$sum": {"$cond": [{"$eq": ["$is_new", True]}, 1, 0]}},
                    "latest": {"$max": "$scraped_at"}
                }}
            ]

            result = list(self.collection.aggregate(pipeline))
            return result[0] if result else {}

        except Exception as e:
            self.logger.error(f"Ошибка получения статистики: {e}")
            return {}

    def close(self):
        """Закрыть соединение"""
        if self.client:
            try:
                self.client.close()
                self.logger.info("Соединение с MongoDB закрыто")
            except:
                pass


# Глобальный экземпляр для повторного использования
mongodb_handler = MongoDBHandler()