# CheeseRadar - Автоматизированная система мониторинга рынка сыров

## Описание проекта
* Автоматизированная система мониторинга рынка сыров: от сбора данных через REST-сервис до аналитических витрин.
* Сервис регулярно скрапит данные с сайтов популярных магазинов (первично Магнит) и позволяет отслеживать динамику цен, сравнивать предложения и выбирать выгодные варианты согласно построенным витринам.
* Целевая аудитория: любители сыра, которые не хотят переплачивать.

## Цели проекта
* Обеспечить надежный цикл сбора, агрегации и анализа цен на сыры в магазинах.
* Дать пользователям прозрачные витрины и показатели для быстрого выбора лучшей цены.
* Обеспечить расширяемость пайплайна для подключения новых источников и витрин.

## Структура проекта
```
CheeseRadar/
├── .gitignore # Игнорируемые файлы Git
├── .pre-commit-config.yaml # Настройки pre-commit
├── .pylintrc # Конфигурация линтера
├── README.md # Документация
│
├── cheese_radar/
| ├── app/
│   ├── data/ # Самплы данных
│   ├── constants.py # Константы для парсинга данных
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── main.py
│   ├── mongo.py # Настройка записи в Mongo
│   ├── product_scraper.py # Парсинг магазинов
│   ├── requirements.txt
│   ├── stores.py # Конфигурации магазинов
│   ├── utils.py # Дополнительные функции для парсинга
|   └── .env
| ├── airflow/ # Airflow оркестрация
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── requirements.txt
│   └── dags/
│     ├── dbt_pipeline.py
│     ├── magnit_scraper_dag.py
│     ├── mongo_to_postgres_dag.py
│     ├── mongo_to_postgres.py
│     ├── scraper_tasks.py
│     ├── select_mongo_dag.py
│     ├── select_postgres_dag.py
│     └── dbt_pipeline.py
│
└── cheese_radar_dbt/ # DBT трансформации
```

## Источники данных
На текущий момент сбор осуществляется с сайта Магнит (www.magnit.ru). Разработки по магазинам от X5 временно заморожены из-за возникших трудностей, связанных с усилением антибот-защиты их сайтов. Планируется дальнейшее исследование вариантов и расширение перечня источников.

## Fastapi приложение
Представляет собой REST-сервис, который по эндпойнту /scrape первично извлекает данные о ценах и характеристиках товара с сайтов продуктовых магазинов и сохраняет в Mongo DB.

## Пайплайн
1. DAG: scrape_magnit. Вызов API /scrape, инкрементальная запись в MongoDB (prod.products). Сбор данных автоматически запускается 2 раза в день с перерывом в 12 часов (7 и 19 часов).
2. DAG: sync_products_simple. EL-процесс, сохраняющий новые записи из MongoDB в Postgres (raw.products). Запускается по расписанию через час после скрапинга (8 и 20 часов), для устранения возможных коллизий.
3. DAG: dbt_cheese_pipeline. Состоит из тасок:
* t_dbt_deps - скачивание зависимостей dbt
* t_dbt_debug - проверка работы dbt
* t_dbt_elementary_init - инициализация elementary
* t_dbt_run_stg - запуск моделей stg слоя
* t_dbt_run_ods - запуск моделей ods слоя
* t_dbt_run_dm - запуск моделей dm слоя
* t_dbt_test_dm - запуск тестов на таблицы dm
* t_dbt_docs_generate - генерация документации
* t_dbt_edr_report - генерация отчета elementary

## Инфраструктура
2 Docker-сервиса:
* FastApi (Python 3.11 + Selenium + Beatiful Soup) + Mongo
* Airflow 2.10.5-python3.11 + Postgres 14 + Elementary Report container

## DBT: витрины
Витрины построены по слоям STG -> ODS -> DM.
| Схема | Таблица | Описание | Источник |
| :---  | :---    | :---     | :---     |
| stg | stg_postgres_raw | Сырые данные из MongoDB без трансформаций | raw.products |
| ods | ods_cheese_latest_load | Данные по сырам из последней загрузки с базовыми рассчитанными признаками | stg.stg_postgres_raw |
| ods | ods_cheese_price_history | История цен на сыры с расчетными полями по всем загрузкам | stg.stg_postgres_raw |
| dm | dm_cheese_actual_prices | Актуальные цены на сыры и ключевые бизнес‑метрики по последней загрузке | ods.ods_cheese_latest_load |
| dm | dm_cheese_hist_analytics | Месячные агрегаты по ценам и скидкам на сыры | ods.ods_cheese_price_history |
| dm | dm_cheese_metrics_aggregated | Сводные метрики по магазинам за последнюю загрузку | ods.ods_cheese_latest_load |
| dm | dm_cheese_top_products | Топ‑продукты по категориям за последнюю загрузку | ods.ods_cheese_latest_load |

## Аналитика по витринам
Приведена в файле cheese_analytics.ipynb.
