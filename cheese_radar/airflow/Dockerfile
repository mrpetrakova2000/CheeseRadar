FROM python:3.11-slim-bookworm

RUN mkdir -p /opt/airflow/logs/scheduler && \
    chown -R airflow:0 /opt/airflow/logs && \
    chmod -R 775 /opt/airflow/logs

COPY requirements.txt /
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /requirements.txt
USER airflow
