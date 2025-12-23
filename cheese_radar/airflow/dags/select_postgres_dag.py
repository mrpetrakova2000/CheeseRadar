import os
import logging
from datetime import datetime
from typing import Dict, Any
from textwrap import shorten
from tabulate import tabulate

from dotenv import load_dotenv
from airflow import DAG
from airflow.decorators import task
from airflow.models.param import Param
from sqlalchemy import create_engine, text
from sqlalchemy.engine import reflection

load_dotenv()

logger = logging.getLogger(__name__)

with DAG(
    dag_id="select_postgres_products",
    schedule=None,
    start_date=datetime(2025, 12, 8),
    catchup=False,
    tags=["postgres", "select", "table-output"],
    render_template_as_native_obj=True,
    params={
        "schema_name": Param(
            default="public",
            type="string",
            title="Схема (schema)",
            description="Название схемы PostgreSQL",
        ),
        "table_name": Param(
            default="products",
            type="string",
            title="Таблица",
            description="Название таблицы для просмотра",
        ),
        "limit": Param(default=100, type="integer", minimum=1, maximum=1000, title="Лимит записей"),
        "table_format": Param(
            default="grid",
            type="string",
            enum=["grid", "simple", "github", "psql", "pipe", "orgtbl", "latex", "html"],
            title="Формат таблицы",
        ),
        "max_table_rows": Param(
            default=10, type="integer", minimum=1, maximum=50, title="Максимум строк в таблице"
        ),
        "truncate_text": Param(default=True, type="boolean", title="Обрезать длинный текст"),
        "max_text_length": Param(
            default=30, type="integer", minimum=10, maximum=100, title="Максимальная длина текста"
        ),
    },
) as dag:

    @task
    def get_schemas_and_tables(**context) -> Dict[str, Any]:
        """Получает список схем и таблиц"""
        engine = None
        try:
            engine = create_engine(
                f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
                f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
            )

            with engine.connect() as conn:
                # Список схем
                schemas_result = conn.execute(
                    text(
                        """
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                    ORDER BY schema_name
                """
                    )
                )
                schemas = [row[0] for row in schemas_result.fetchall()]

                # Список таблиц для всех схем
                tables_result = conn.execute(
                    text(
                        """
                    SELECT table_schema, table_name
                    FROM information_schema.tables
                    WHERE table_schema NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                    ORDER BY table_schema, table_name
                """
                    )
                )
                tables = [(row[0], row[1]) for row in tables_result.fetchall()]

            return {
                "status": "success",
                "schemas": schemas,
                "tables": tables,
                "message": f"Найдено схем: {len(schemas)}, таблиц: {len(tables)}",
            }
        except Exception as e:
            logger.error(f"Ошибка получения схем/таблиц: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            if engine:
                engine.dispose()

    @task
    def select_from_postgres(**context) -> Dict[str, Any]:
        """Простой SELECT * из указанной таблицы"""
        params = context["params"]
        schema_name = params.get("schema_name", "public")
        table_name = params.get("table_name", "products")
        print(schema_name, table_name)
        limit = params.get("limit", 100)

        engine = None
        try:
            engine = create_engine(
                f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
                f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
            )

            column_names = []
            with engine.connect() as conn:
                conn.execution_options(isolation_level="AUTOCOMMIT")

                columns_result = conn.execute(
                    text(
                        """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = :schema
                    AND table_name = :table
                    ORDER BY ordinal_position
                """
                    ),
                    {"schema": schema_name, "table": table_name},
                )
                column_names = [row[0] for row in columns_result.fetchall()]

            if not column_names:
                raise ValueError(f"Таблица {schema_name}.{table_name} не найдена или пуста")

            logger.info(
                f"Таблица {schema_name}.{table_name}: {len(column_names)} столбцов - {column_names}"
            )

            # Простой SQL: SELECT * с лимитом
            sql_query = f"""
            SELECT *
            FROM {schema_name}.{table_name}
            LIMIT {limit}
            """

            logger.info(f"Выполняемый SQL: {sql_query}")

            # Выполняем запрос
            with engine.connect() as conn:
                result = conn.execute(text(sql_query))
                rows = result.fetchall()

            # Форматируем результаты
            results = []
            for row in rows:
                row_dict = dict(zip(column_names, row))
                # Преобразование datetime для JSON
                for key, value in row_dict.items():
                    if hasattr(value, "isoformat"):
                        row_dict[key] = value.isoformat()
                results.append(row_dict)

            # Подсчет общего количества записей в таблице
            count_sql = f"SELECT COUNT(*) FROM {schema_name}.{table_name}"
            with engine.connect() as conn:
                count_result = conn.execute(text(count_sql))
                total_row = count_result.fetchone()
                total_count = total_row[0] if total_row else 0

            logger.info(
                f"Таблица: {schema_name}.{table_name}, всего записей: {total_count}, выбрано: {len(results)}"
            )

            return {
                "status": "success",
                "data": results,
                "params_used": {
                    "schema_name": schema_name,
                    "table_name": table_name,
                    "limit": limit,
                },
                "count": len(results),
                "total_in_table": total_count,
                "columns": column_names,
                "schema_table": f"{schema_name}.{table_name}",
                "message": f"Выбрано {len(results)} из {total_count} записей в таблице {schema_name}.{table_name}",
                "sql_query": sql_query,
            }

        except Exception as e:
            # Полное логирование ошибки
            error_msg = str(e)
            logger.error(f"Ошибка при селекте из {schema_name}.{table_name}: {error_msg}")

            return {
                "status": "error",
                "params_used": params,
                "error": error_msg,
                "message": f"Ошибка при выполнении запроса к {schema_name}.{table_name}",
            }
        finally:
            if engine:
                engine.dispose()

    @task
    def format_as_table(result: Dict[str, Any], **context) -> Dict[str, Any]:
        """Форматирует результаты в виде таблицы"""
        params = context["params"]

        if result["status"] == "error":
            return {
                "status": "error",
                "table_output": f"ОШИБКА: {result.get('error', 'Неизвестная ошибка')}",
                "metadata": {"timestamp": datetime.now().isoformat()},
            }

        data = result.get("data", [])
        max_rows = params.get("max_table_rows", 10)
        truncate = params.get("truncate_text", True)
        max_length = params.get("max_text_length", 30)
        schema_table = result.get("schema_table", "unknown")
        table_format = params.get("table_format", "grid")

        if not data:
            table_data = [["Нет данных для отображения"]]
            table_headers = ["Результат"]
        else:
            display_data = data[:max_rows]
            columns = result.get("columns", [])

            # Создаем заголовки (обрезаем длинные имена)
            table_headers = []
            for col in columns:
                header = col.replace("_", " ").title()
                if len(header) > 12:
                    header = shorten(header, width=12, placeholder="...")
                table_headers.append(header)

            # Данные таблицы
            table_data = []
            for row in display_data:
                table_row = []
                for col in columns:
                    value = str(row.get(col, ""))
                    if truncate and len(value) > max_length:
                        value = shorten(value, width=max_length, placeholder="...")
                    table_row.append(value)
                table_data.append(table_row)

        table_output = tabulate(table_data, headers=table_headers, tablefmt=table_format)

        # Статистика
        stats = f"\n{'=' * 60}\n"
        stats += f"ТАБЛИЦА: {schema_table}\n"
        stats += f"Всего записей в таблице: {result.get('total_in_table', 0)}\n"
        stats += f"Выбрано записей: {result.get('count', 0)}\n"
        stats += f"Показано в таблице: {len(table_data) if data else 0}\n"
        stats += f"{'=' * 60}\n"

        return {
            "status": "success",
            "table_output": table_output + stats,
            "table_data": table_data,
            "table_headers": table_headers,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "schema_table": schema_table,
                "columns": result.get("columns", []),
                "total_records": result.get("total_in_table", 0),
                "selected_records": result.get("count", 0),
            },
        }

    @task
    def log_table_output(formatted_result: Dict[str, Any], **context) -> None:
        """Логирует табличный вывод"""
        separator = "=" * 80
        logger.info("\n" + separator)
        logger.info("РЕЗУЛЬТАТЫ ИЗ POSTGRESQL")
        logger.info(separator)

        if formatted_result["status"] == "error":
            logger.error(formatted_result["table_output"])
        else:
            logger.info(formatted_result["table_output"])

            metadata = formatted_result.get("metadata", {})
            logger.info(f"Таблица: {metadata.get('schema_table', 'N/A')}")
            logger.info(f"Всего записей в таблице: {metadata.get('total_records', 0)}")

        logger.info(separator + "\n")

    # Запуск задач
    schemas_tables = get_schemas_and_tables()
    postgres_results = select_from_postgres()
    table_formatted = format_as_table(postgres_results)
    log_output = log_table_output(table_formatted)
