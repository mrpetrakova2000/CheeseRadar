from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from mongo_to_postgres import move_magnit_products, move_perekrestok_products

default_args = {
    "owner": "airflow",
    "start_date": datetime(2025, 12, 7),
    "retries": 1,
}

with DAG(
    "sync_products_simple",
    default_args=default_args,
    schedule_interval="0 8,20 * * *",
    catchup=False,
) as dag:
    sync_magnit = PythonOperator(
        task_id="sync_magnit",
        python_callable=move_magnit_products,
    )

    sync_perekrestok = PythonOperator(
        task_id="sync_perekrestok",
        python_callable=move_perekrestok_products,
    )

    sync_magnit >> sync_perekrestok
