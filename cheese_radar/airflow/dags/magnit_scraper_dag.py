from datetime import datetime, timedelta
import logging
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from scraper_tasks import scrape_magnit

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 12, 7),
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'max_active_runs': 1,
}

logger = logging.getLogger(__name__)


def scrape_magnit_with_check():
    """Функция скрапинга Магнита"""
    logger.info("Начинается скрапинг Магнита")

    result = scrape_magnit()

    # Проверяем результат от API
    if isinstance(result, dict):
        total_in_database = result.get('total_in_database', 0)
        new_products_saved = result.get('new_products_saved', 0)

        # Если сохранено 0 новых продуктов - это ошибка
        if new_products_saved == 0:
            error_msg = (
                f"Скрапинг Магнита завершился с ошибкой: сохранено 0 новых продуктов. "
                f"Всего продуктов в базе: {total_in_database}. "
                f"Сообщение: {result.get('message', 'Нет новых данных')}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f" Скрапинг Магнита завершен успешно")
        logger.info(f"   - Всего продуктов в базе: {total_in_database}")
        logger.info(f"   - Сохранено новых продуктов: {new_products_saved}")

        return result

    error_msg = f"API вернул неожиданный тип данных: {type(result)}. Данные: {result}"
    logger.error(error_msg)
    raise TypeError(error_msg)


with DAG(
        'scrape_magnit',
        default_args=default_args,
        description='Скрапинг магазина Магнит',
        schedule_interval='0 7,19 * * *',
        catchup=False,
        tags=['scraping', 'magnit'],
) as dag:
    start = EmptyOperator(task_id='start')

    scrape_task = PythonOperator(
        task_id='scrape_magnit_data',
        python_callable=scrape_magnit_with_check,
        execution_timeout=timedelta(minutes=30),
        retries=1,
    )

    end = EmptyOperator(task_id='end')

    start >> scrape_task >> end
