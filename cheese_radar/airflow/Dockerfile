FROM apache/airflow:2.10.5-python3.11

USER root
RUN apt-get update && apt-get install -y git curl
USER airflow

COPY requirements.txt /
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /requirements.txt

RUN pip install --no-cache-dir  \
    dbt-core==1.7.16 \
    dbt-postgres==1.7.16 \
    elementary-data==0.20.1

COPY dags/ /opt/airflow/dags/usd

RUN mkdir -p /opt/airflow/dbt && chown airflow:root /opt/airflow/dbt

WORKDIR /opt/airflow/dbt
ENV PATH="/home/airflow/.local/bin:/usr/local/bin:${PATH}"