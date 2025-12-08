FROM apache/airflow:slim-3.1.4rc1-python3.11

COPY requirements.txt /
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /requirements.txt

COPY --chmod=755 entrypoint.sh /entrypoint.sh
COPY dags /opt/airflow/dags

USER airflow

ENTRYPOINT ["/entrypoint.sh"]