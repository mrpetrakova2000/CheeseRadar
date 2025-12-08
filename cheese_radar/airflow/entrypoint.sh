#!/bin/bash
sleep 120
airflow db init
airflow users create --username admin --password admin123 --firstname Admin --lastname User --role Admin --email admin@example.com
airflow scheduler &
exec airflow webserver --port 8080