FROM apache/airflow:2.10.5

COPY requirements.txt /
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /requirements.txt

USER airflow

COPY dags /opt/airflow/dags
COPY plugins /opt/airflow/plugins

CMD ["bash", "-c", "sleep 10 && airflow db init 2>/dev/null || true && airflow users create --username admin --firstname Admin --lastname User --role Admin --email admin@example.com --password admin 2>/dev/null || true && airflow scheduler & exec airflow webserver --port 8080"]