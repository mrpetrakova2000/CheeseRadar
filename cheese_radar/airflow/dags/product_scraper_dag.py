from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from scraper_tasks import *

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 12, 6),
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'max_active_runs': 1,
}

with DAG(
        'product_scraper_sequential',
        default_args=default_args,
        description='Последовательный скрапинг магазинов с чтением данных о ценах на сыр',
        schedule_interval='0 3 * * *',
        catchup=False,
        tags=['scraping'],
) as dag:
    start = EmptyOperator(task_id='start')

    magnit_task = PythonOperator(
        task_id='scrape_magnit',
        python_callable=scrape_magnit,
    )

    perekrestok_task = PythonOperator(
        task_id='scrape_perekrestok',
        python_callable=scrape_perekrestok,
    )

    lenta_task = PythonOperator(
        task_id='scrape_lenta',
        python_callable=scrape_lenta,
        trigger_rule='all_done',
    )

    end = EmptyOperator(task_id='end', trigger_rule='all_done')

    # Поток выполнения: последовательно
    start >> magnit_task >> perekrestok_task >> lenta_task >> end
