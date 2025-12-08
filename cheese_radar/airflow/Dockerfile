FROM python:3.11-slim-bookworm

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        postgresql-client \
        libpq-dev \
        gcc \
        python3-dev \
        && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    "apache-airflow[postgres]==2.7.3" \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.7.3/constraints-3.11.txt"

RUN useradd -m -u 1000 airflow && \
    mkdir -p /opt/airflow/dags && \
    chown -R airflow:airflow /opt/airflow

USER airflow
WORKDIR /opt/airflow

COPY dags /opt/airflow/dags
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]