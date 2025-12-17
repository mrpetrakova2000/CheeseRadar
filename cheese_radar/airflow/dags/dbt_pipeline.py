from __future__ import annotations
from datetime import timedelta, datetime
import logging
from airflow import DAG
from airflow.operators.bash import BashOperator

log = logging.getLogger(__name__)

DBT_PROJECT_DIR = "/opt/airflow/dbt"
DBT_PROFILE = "cheese_radar"

with DAG(
        dag_id="dbt_cheese_pipeline",
        description="ETL пайплайн для данных о сырах",
        schedule_interval="0 */12 * * *",
        start_date=datetime(2025, 12, 10),
        catchup=False,
        default_args={
            "retries": 2,
            "retry_delay": timedelta(minutes=5),
        },
        tags=["dbt", "cheese", "analytics", "prices"],
) as dag:
    t_dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=f"""
        cd {DBT_PROJECT_DIR} && dbt clean && \
        dbt deps --profiles-dir .
        """,
    )

    t_dbt_debug = BashOperator(
        task_id="dbt_debug",
        bash_command=f"""
        cd {DBT_PROJECT_DIR} && dbt debug --profiles-dir .
        """,
    )

    t_dbt_elementary_init = BashOperator(
        task_id="dbt_elem_init",
        bash_command=f"""
        cd {DBT_PROJECT_DIR} && \
        dbt run --select elementary \
        --profiles-dir . \
        --target elementary
        """,
    )

    t_dbt_run_stg = BashOperator(
        task_id="dbt_run_stg",
        bash_command=f"""
        cd {DBT_PROJECT_DIR} && \
        dbt run --profiles-dir . \
          --select tag:stg
        """,
    )

    t_dbt_run_ods = BashOperator(
        task_id="dbt_run_ods",
        bash_command=f"""
        cd {DBT_PROJECT_DIR} && \
        dbt run --profiles-dir . \
          --select tag:ods \
          --vars '{{"incremental_load": true}}'
        """,
    )

    t_dbt_run_dm = BashOperator(
        task_id="dbt_run_dm",
        bash_command=f"""
        cd {DBT_PROJECT_DIR} && \
        dbt run --profiles-dir . \
          --select tag:dm
        """,
    )

    t_dbt_test_dm = BashOperator(
        task_id="dbt_test",
        bash_command=f"""
        cd {DBT_PROJECT_DIR} && \
        dbt test --profiles-dir . \
          --select tag:error
        """,
    )

    t_dbt_docs_generate = BashOperator(
        task_id="dbt_docs_generate",
        bash_command=f"""
        cd {DBT_PROJECT_DIR} && \
        dbt docs generate --profiles-dir .
        """,
    )

    t_dbt_edr_report = BashOperator(
        task_id="dbt_edr_report",
        bash_command=f"""
        cd {DBT_PROJECT_DIR} && \
        edr report --profile cheese_radar_dbt && \
        --profiles-dir .
        """,
    )

    (
            t_dbt_deps
            >> t_dbt_debug
            >> t_dbt_elementary_init
            >> t_dbt_run_stg
            >> t_dbt_run_ods
            >> t_dbt_run_dm
            >> t_dbt_test_dm
            >> t_dbt_docs_generate
            >> t_dbt_edr_report
    )