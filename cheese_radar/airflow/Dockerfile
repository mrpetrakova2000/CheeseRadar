FROM apache/airflow:2.10.5

COPY requirements.txt /
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /requirements.txt

COPY --chmod=755 entrypoint.sh /entrypoint.sh

USER airflow

ENTRYPOINT ["/entrypoint.sh"]