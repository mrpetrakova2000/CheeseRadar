import os
import logging
from datetime import datetime, timedelta
from sqlalchemy import func

from dotenv import load_dotenv
from pymongo import MongoClient
from sqlalchemy import Column, Integer, String, DateTime, text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

logger = logging.getLogger(__name__)

Base = declarative_base()


class Product(Base):
    __tablename__ = "products"
    __table_args__ = {'schema': 'raw'}

    id = Column(Integer, primary_key=True)
    product_id = Column(String)
    name = Column(String)
    price = Column(String)
    discount = Column(String)
    rating = Column(String)
    store = Column(String)
    date_time = Column(String)
    scraped_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)


def clean_price(price):
    try:
        if isinstance(price, str):
            price = price.replace('руб', '').replace('₽', '').replace(' ', '')
            price = price.replace(',', '.')
        return float(price)
    except:
        return 0.0


def move_products_to_postgres(store_name=None):
    """Перенос данных в Postgres"""
    logger.info(f"Перенос данных для магазина: {store_name or 'все'}")

    try:
        engine = create_engine(
            f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
            f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}",
            pool_pre_ping=True,
            connect_args={'connect_timeout': 30}
        )

        # Пробное подключение к PostgreSQL
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("PostgreSQL подключен успешно")

    except Exception as e:
        logger.error(f"Ошибка подключения к PostgreSQL: {e}")
        logger.error(f"Параметры: host={os.getenv('POSTGRES_HOST')}, "
                     f"port={os.getenv('POSTGRES_PORT')}, db={os.getenv('POSTGRES_DB')}")
        return {
            "status": "error",
            "store": store_name or "all",
            "error": f"PostgreSQL connection failed: {str(e)}"
        }

    try:
        client = MongoClient(
            host=os.getenv("MONGO_HOST"),
            port=int(os.getenv("MONGO_PORT")),
            username=os.getenv("MONGO_INITDB_ROOT_USERNAME"),
            password=os.getenv("MONGO_INITDB_ROOT_PASSWORD"),
            serverSelectionTimeoutMS=5000
        )

        client.admin.command('ping')
        logger.info("MongoDB подключен успешно")

    except Exception as e:
        logger.error(f"Ошибка подключения к MongoDB: {e}")
        return {
            "status": "error",
            "store": store_name or "all",
            "error": f"MongoDB connection failed: {str(e)}"
        }

    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        session.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))
        session.execute(text("GRANT ALL ON SCHEMA raw TO airflow"))
        session.commit()
        logger.info("Схема raw создана")

        # Определяем время последней загрузки
        last_scraped_time = session.query(func.max(Product.scraped_at)).scalar()
        if last_scraped_time:
            # Для инкрементальной загрузки - загружаем данные после последнего scraped_at
            # Минус 1 минута на всякий случай, чтобы не пропустить записи
            load_from_time = last_scraped_time - timedelta(minutes=1)
            logger.info(f"Загрузка данных, созданных после: {load_from_time}")
        else:
            # Первая загрузка - загружаем все данные
            load_from_time = None
            logger.info("Первая загрузка - загрузка всех данных")

        # Получаем данные из MongoDB
        collection = client["prod"]["products"]
        query = {"store": store_name} if store_name else {}

        # Добавляем фильтр по времени для инкрементальной загрузки
        if load_from_time:
            if isinstance(load_from_time, datetime):
                load_from_str = load_from_time.strftime('%Y-%m-%d %H:%M:%S')
                query["scraped_at"] = {"$gt": load_from_str}
            else:
                query["scraped_at"] = {"$gt": load_from_time}

        mongo_data = collection.find(query, {
            "_id": 1,
            "name": 1,
            "price": 1,
            "discount": 1,
            "rating": 1,
            "store": 1,
            "date_time": 1,
            "scraped_at": 1
        })

        # Перенос данных
        count = 0
        skipped = 0
        existing_ids = {str(p[0]) for p in session.query(Product.product_id).all()}

        for item in mongo_data:
            try:
                product_id = str(item.get("_id", ""))

                # Пропускаем если уже есть
                if product_id in existing_ids:
                    skipped += 1
                    continue

                product = Product(
                    product_id=product_id,
                    name=str(item.get("name", "")),
                    price=clean_price(item.get("price", 0)),
                    discount=str(item.get("discount", "")) if item.get("discount") else None,
                    rating=str(item.get("rating", "")) if item.get("rating") else None,
                    store=str(item.get("store", "")),
                    date_time=str(item.get("date_time", "")),
                    scraped_at=item.get("scraped_at")
                )
                session.add(product)
                count += 1

                # Промежуточный коммит каждые 100 записей
                if count % 100 == 0:
                    session.commit()
                    logger.info(f"Обработано {count} записей...")

            except Exception as e:
                logger.error(f"Ошибка при обработке товара: {e}")
                continue

        session.commit()

        logger.info(f"Перенесено {count} товаров для магазина: {store_name or 'все'}")
        if skipped > 0:
            logger.info(f"Пропущено {skipped} товаров (уже есть в базе)")

        return {
            "status": "success",
            "store": store_name or "all",
            "transferred": count,
            "skipped": skipped
        }

    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        session.rollback()
        return {
            "status": "error",
            "store": store_name or "all",
            "error": str(e)
        }

    finally:
        client.close()
        session.close()


def move_magnit_products():
    return move_products_to_postgres("Магнит")


def move_perekrestok_products():
    return move_products_to_postgres("Перекрёсток")


def move_all_products():
    return move_products_to_postgres()
