FROM python:3.11-alpine

RUN apk add --no-cache postgresql-dev gcc python3-dev musl-dev libffi-dev
RUN pip install --no-cache-dir apache-airflow==2.7.3 psycopg2-binary
RUN apk del gcc python3-dev musl-dev libffi-dev

RUN adduser -D -u 1000 airflow && mkdir -p /opt/airflow/dags
USER airflow
WORKDIR /opt/airflow
COPY dags /opt/airflow/dags

CMD sleep 150 && airflow db init && airflow users create --username admin --password admin123 --firstname Admin --lastname User --role Admin --email admin@example.com && airflow scheduler & airflow webserver --port 8080