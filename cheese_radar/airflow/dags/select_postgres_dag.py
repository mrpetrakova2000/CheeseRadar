# import os
# import json
# import logging
# from datetime import datetime, timedelta
# from typing import Dict, Any, List
# from textwrap import shorten
# from tabulate import tabulate
#
# from dotenv import load_dotenv
# from airflow import DAG
# from airflow.decorators import task
# from airflow.models.param import Param
# from sqlalchemy import create_engine, text
#
# load_dotenv()
#
# logger = logging.getLogger(__name__)
#
# with DAG(
#         dag_id='select_postgres_products',
#         schedule=None,
#         start_date=datetime(2025, 12, 8),
#         catchup=False,
#         tags=['postgres', 'select', 'table-output'],
#         render_template_as_native_obj=True,
#         params={
#             "load_type": Param(
#                 default="latest",
#                 type="string",
#                 enum=["latest", "all"],
#                 title="Тип загрузки",
#                 description="'latest': данные последней загрузки, 'all': все данные"
#             ),
#             "store_filter": Param(
#                 default="all",
#                 type="string",
#                 title="Фильтр по магазину",
#                 description="Название магазина (напр., 'Магнит') или 'all' для всех"
#             ),
#             "sort_by": Param(
#                 default="scraped_at",
#                 type="string",
#                 enum=["scraped_at", "price", "rating", "name", "created_at"],
#                 title="Поле для сортировки"
#             ),
#             "sort_order": Param(
#                 default="desc",
#                 type="string",
#                 enum=["asc", "desc"],
#                 title="Порядок сортировки"
#             ),
#             "limit": Param(
#                 default=100,
#                 type="integer",
#                 minimum=1,
#                 maximum=1000,
#                 title="Лимит записей"
#             ),
#             "table_format": Param(
#                 default="grid",
#                 type="string",
#                 enum=["grid", "simple", "github", "psql", "pipe", "orgtbl", "latex", "html"],
#                 title="Формат таблицы",
#                 description="Стиль отображения таблицы"
#             ),
#             "max_table_rows": Param(
#                 default=10,
#                 type="integer",
#                 minimum=1,
#                 maximum=50,
#                 title="Максимум строк в таблице",
#                 description="Сколько строк показать в табличном выводе"
#             ),
#             "truncate_text": Param(
#                 default=True,
#                 type="boolean",
#                 title="Обрезать длинный текст",
#                 description="Сокращать длинные названия для лучшего отображения"
#             ),
#             "max_text_length": Param(
#                 default=30,
#                 type="integer",
#                 minimum=10,
#                 maximum=100,
#                 title="Максимальная длина текста",
#                 description="Максимальная длина текстовых полей в таблице"
#             )
#         }
# ) as dag:
#     @task
#     def select_from_postgres(**context) -> Dict[str, Any]:
#         """Основная задача селекта из PostgreSQL"""
#         params = context['params']
#
#         load_type = params.get('load_type', 'latest')
#         store_filter = params.get('store_filter', 'all')
#         sort_by = params.get('sort_by', 'scraped_at')
#         sort_order = params.get('sort_order', 'desc').upper()
#         limit = params.get('limit', 100)
#
#         engine = None
#         try:
#             # Подключение к PostgreSQL
#             engine = create_engine(
#                 f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
#                 f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
#             )
#
#             sql_parts = [
#                 "SELECT id, product_id, name, price, discount, rating, store, date_time, scraped_at, created_at",
#                 "FROM products"
#             ]
#
#             where_clauses = []
#             query_params = {}
#
#             if store_filter != 'all':
#                 where_clauses.append(f"store = :store_filter")
#                 query_params['store_filter'] = store_filter
#
#             # Фильтр по времени (только последней загрузки)
#             if load_type == 'latest':
#                 # Находим максимальное время в таблице
#                 max_time_sql = "SELECT MAX(scraped_at) as max_time FROM products"
#                 if where_clauses:
#                     max_time_sql += " WHERE " + " AND ".join(where_clauses)
#
#                 with engine.connect() as conn:
#                     result = conn.execute(text(max_time_sql), query_params)
#                     max_time_row = result.fetchone()
#
#                     if max_time_row and max_time_row[0]:
#                         latest_time = max_time_row[0]
#                         # Вычитаем 1 минуту для надёжности
#                         filter_time = latest_time - timedelta(minutes=1)
#                         where_clauses.append(f"scraped_at >= :filter_time")
#                         query_params['filter_time'] = filter_time
#                         logger.info(f"Фильтр по времени: >= {filter_time}")
#
#             if where_clauses:
#                 sql_parts.append(f"WHERE {' AND '.join(where_clauses)}")
#
#             valid_sort_fields = ['scraped_at', 'price', 'rating', 'created_at', 'name']
#             if sort_by not in valid_sort_fields:
#                 sort_by = 'scraped_at'
#             sql_parts.append(f"ORDER BY {sort_by} {sort_order}")
#
#             sql_parts.append(f"LIMIT {limit}")
#
#             full_sql = "\n".join(sql_parts)
#             logger.info(f"Выполняемый SQL: {full_sql}")
#
#             with engine.connect() as conn:
#                 result = conn.execute(text(full_sql), query_params)
#                 rows = result.fetchall()
#
#             results = []
#             columns = ['id', 'product_id', 'name', 'price', 'discount', 'rating',
#                        'store', 'date_time', 'scraped_at', 'created_at']
#
#             for row in rows:
#                 row_dict = dict(zip(columns, row))
#                 # Преобразование datetime для JSON
#                 for date_field in ['scraped_at', 'created_at']:
#                     if row_dict[date_field]:
#                         row_dict[date_field] = row_dict[date_field].isoformat()
#                 results.append(row_dict)
#
#             count_sql = "SELECT COUNT(*) FROM products"
#             if where_clauses:
#                 count_sql += f" WHERE {' AND '.join(where_clauses)}"
#
#             with engine.connect() as conn:
#                 count_result = conn.execute(text(count_sql), query_params)
#                 total_row = count_result.fetchone()
#                 total_count = total_row[0] if total_row else 0
#
#             logger.info(f"Параметры запроса: load_type={load_type}, store_filter={store_filter}, "
#                         f"sort_by={sort_by}, sort_order={sort_order}, limit={limit}")
#             logger.info(f"Найдено записей: {total_count}, возвращено: {len(results)}")
#
#             return {
#                 'status': 'success',
#                 'data': results,
#                 'params_used': {
#                     'load_type': load_type,
#                     'store_filter': store_filter,
#                     'sort_by': sort_by,
#                     'sort_order': sort_order,
#                     'limit': limit
#                 },
#                 'count': len(results),
#                 'total_in_query': total_count,
#                 'columns': columns,
#                 'message': f'Успешно выбрано {len(results)} записей из PostgreSQL',
#                 'sql_query': full_sql
#             }
#
#         except Exception as e:
#             logger.error(f"Ошибка при селекте из PostgreSQL: {e}")
#             return {
#                 'status': 'error',
#                 'params_used': params,
#                 'error': str(e),
#                 'message': 'Ошибка при выполнении запроса к PostgreSQL'
#             }
#         finally:
#             if engine:
#                 engine.dispose()
#
#
#     @task
#     def format_as_table(result: Dict[str, Any], **context) -> Dict[str, Any]:
#         """Форматирует результаты в виде таблицы"""
#         params = context['params']
#
#         if result['status'] == 'error':
#             return {
#                 'status': 'error',
#                 'table_output': f"ОШИБКА: {result.get('error', 'Неизвестная ошибка')}\n"
#                                 f"Сообщение: {result.get('message', '')}",
#                 'metadata': {
#                     'timestamp': datetime.now().isoformat(),
#                     'error_details': result.get('error_details', {})
#                 }
#             }
#
#         data = result.get('data', [])
#         max_rows = params.get('max_table_rows', 10)
#         truncate = params.get('truncate_text', True)
#         max_length = params.get('max_text_length', 30)
#
#         # Подготавливаем данные для таблицы
#         if not data:
#             table_data = [["Нет данных для отображения"]]
#             table_headers = ["Результат"]
#         else:
#             # Ограничиваем количество строк для таблицы
#             display_data = data[:max_rows]
#
#             # Подготавливаем заголовки
#             table_headers = [
#                 'ID', 'Product ID', 'Название', 'Цена', 'Скидка',
#                 'Рейтинг', 'Магазин', 'Дата/время', 'Загружено', 'Создано'
#             ]
#
#             # Подготавливаем строки данных
#             table_data = []
#             for row in display_data:
#                 table_row = []
#
#                 # ID и Product ID
#                 table_row.append(str(row.get('id', ''))[:10])
#                 table_row.append(str(row.get('product_id', ''))[:15])
#
#                 # Название (обрезаем если нужно)
#                 name = row.get('name', '')
#                 if truncate and len(str(name)) > max_length:
#                     table_row.append(shorten(str(name), width=max_length, placeholder="..."))
#                 else:
#                     table_row.append(str(name))
#
#                 # Цена
#                 price = row.get('price', '')
#                 table_row.append(str(price))
#
#                 # Остальные поля
#                 table_row.append(str(row.get('discount', '') or '-'))
#                 table_row.append(str(row.get('rating', '') or '-'))
#
#                 # Магазин
#                 store = row.get('store', '')
#                 if truncate and len(str(store)) > max_length:
#                     table_row.append(shorten(str(store), width=max_length, placeholder="..."))
#                 else:
#                     table_row.append(str(store))
#
#                 # Даты
#                 date_time = str(row.get('date_time', ''))[:19]
#                 scraped_at = str(row.get('scraped_at', ''))[:19]
#                 created_at = str(row.get('created_at', ''))[:19]
#
#                 table_row.append(date_time if date_time else '-')
#                 table_row.append(scraped_at if scraped_at else '-')
#                 table_row.append(created_at if created_at else '-')
#
#                 table_data.append(table_row)
#
#         # Форматируем таблицу
#         table_format = params.get('table_format', 'grid')
#         table_output = tabulate(table_data, headers=table_headers, tablefmt=table_format)
#
#         # Добавляем статистику под таблицей
#         stats = f"\n{'=' * 60}\n"
#         stats += f"СТАТИСТИКА:\n"
#         stats += f"  - Всего найдено записей: {result.get('total_in_query', 0)}\n"
#         stats += f"  - Получено записей: {result.get('count', 0)}\n"
#         stats += f"  - Показано в таблице: {len(display_data) if data else 0}\n"
#
#         if len(data) > max_rows:
#             stats += f"  - Скрыто записей: {len(data) - max_rows}\n"
#
#         stats += f"  - Формат таблицы: {table_format}\n"
#         stats += f"{'=' * 60}\n"
#
#         full_output = table_output + stats
#
#         return {
#             'status': 'success',
#             'table_output': full_output,
#             'table_data': table_data,
#             'table_headers': table_headers,
#             'metadata': {
#                 'timestamp': datetime.now().isoformat(),
#                 'statistics': {
#                     'total_found': result.get('total_in_query', 0),
#                     'returned_count': result.get('count', 0),
#                     'displayed_rows': len(display_data) if data else 0,
#                     'hidden_rows': len(data) - max_rows if len(data) > max_rows else 0
#                 },
#                 'params_used': result.get('params_used', {}),
#                 'sql_query': result.get('sql_query', '')
#             },
#             'message': result.get('message', '')
#         }
#
#
#     @task
#     def log_table_output(formatted_result: Dict[str, Any], **context) -> None:
#         """Логирует табличный вывод"""
#
#         separator = "=" * 80
#
#         logger.info("\n" + separator)
#         logger.info("ТАБЛИЧНЫЙ ВЫВОД РЕЗУЛЬТАТОВ ИЗ POSTGRESQL")
#         logger.info(separator)
#
#         if formatted_result['status'] == 'error':
#             logger.error(f"\n{formatted_result['table_output']}")
#         else:
#             logger.info(f"\n{formatted_result['table_output']}")
#
#             metadata = formatted_result.get('metadata', {})
#             stats = metadata.get('statistics', {})
#
#             logger.info("\n" + "-" * 40)
#             logger.info("ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ:")
#             logger.info(f"   - Время выполнения: {metadata.get('timestamp', 'N/A')}")
#             logger.info(f"   - Всего записей в БД: {stats.get('total_found', 0)}")
#             logger.info(f"   - Получено записей: {stats.get('returned_count', 0)}")
#             logger.info(f"   - Показано в таблице: {stats.get('displayed_rows', 0)}")
#
#             if stats.get('hidden_rows', 0) > 0:
#                 logger.info(f"   - Скрыто записей: {stats.get('hidden_rows', 0)}")
#
#             params_used = metadata.get('params_used', {})
#             logger.info(f"   - Параметры запроса:")
#             for key, value in params_used.items():
#                 logger.info(f"     - {key}: {value}")
#
#         logger.info(separator + "\n")
#
#     postgres_results = select_from_postgres()
#     table_formatted = format_as_table(postgres_results)
#     log_output = log_table_output(table_formatted)
