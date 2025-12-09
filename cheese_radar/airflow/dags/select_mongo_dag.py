import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from dotenv import load_dotenv
from pymongo import MongoClient
from airflow import DAG
from airflow.decorators import task
from airflow.models.param import Param

load_dotenv()

logger = logging.getLogger(__name__)

with DAG(
        dag_id='select_mongo_products',
        schedule=None,
        start_date=datetime(2025, 12, 8),
        catchup=False,
        tags=['mongo', 'select'],
        render_template_as_native_obj=True,
        params={
            "load_type": Param(
                default="latest",
                type="string",
                enum=["latest", "all"],
                title="Тип загрузки",
                description="'latest': данные последней загрузки, 'all': все данные"
            ),
            "store_filter": Param(
                default="all",
                type="string",
                title="Фильтр по магазину",
                description="Название магазина (напр., 'Магнит') или 'all' для всех"
            ),
            "sort_by": Param(
                default="scraped_at",
                type="string",
                enum=["scraped_at", "price", "rating", "name"],
                title="Поле для сортировки"
            ),
            "sort_order": Param(
                default="desc",
                type="string",
                enum=["asc", "desc"],
                title="Порядок сортировки"
            ),
            "limit": Param(
                default=100,
                type="integer",
                minimum=1,
                maximum=1000,
                title="Лимит записей"
            ),
            "json_indent": Param(
                default=2,
                type="integer",
                minimum=0,
                maximum=8,
                title="Отступ JSON",
                description="0 - без отступов, 2 или 4 - для читаемости"
            ),
            "max_sample_display": Param(
                default=5,
                type="integer",
                minimum=0,
                maximum=20,
                title="Максимум примеров",
                description="Сколько примеров показать в выводе (0 - все)"
            )
        }
) as dag:
    @task
    def select_from_mongo(**context) -> Dict[str, Any]:
        """Основная задача селекта из MongoDB"""
        params = context['params']

        load_type = params.get('load_type', 'latest')
        store_filter = params.get('store_filter', 'all')
        sort_by = params.get('sort_by', 'scraped_at')
        sort_order = params.get('sort_order', 'desc')
        limit = params.get('limit', 100)

        client = None
        try:
            client = MongoClient(
                host=os.getenv("MONGO_HOST"),
                port=int(os.getenv("MONGO_PORT")),
                username=os.getenv("MONGO_INITDB_ROOT_USERNAME"),
                password=os.getenv("MONGO_INITDB_ROOT_PASSWORD")
            )

            db = client["prod"]
            collection = db["products"]

            query = {}

            if store_filter != 'all':
                query['store'] = store_filter

            if load_type == 'latest':
                # Находим максимальное время в коллекции с учетом фильтра магазина
                find_query = query.copy()
                latest_record = collection.find_one(
                    find_query,
                    sort=[('scraped_at', -1)]
                )
                if latest_record and 'scraped_at' in latest_record:
                    latest_time = latest_record['scraped_at']
                    filter_time = latest_time - timedelta(minutes=1)
                    query['scraped_at'] = {'$gte': filter_time}
                    logger.info(f"Фильтр по времени: >= {filter_time}")

            sort_order_val = -1 if sort_order == 'desc' else 1

            cursor = collection.find(
                query,
                {
                    '_id': 1,
                    'name': 1,
                    'price': 1,
                    'discount': 1,
                    'rating': 1,
                    'store': 1,
                    'date_time': 1,
                    'scraped_at': 1
                }
            ).sort(sort_by, sort_order_val).limit(limit)

            results = []
            for item in cursor:
                item['_id'] = str(item['_id'])
                if 'scraped_at' in item and item['scraped_at']:
                    item['scraped_at'] = item['scraped_at'].isoformat()
                results.append(item)

            total_count = collection.count_documents(query)
            returned_count = len(results)

            logger.info(f"Параметры запроса: load_type={load_type}, store_filter={store_filter}, "
                        f"sort_by={sort_by}, sort_order={sort_order}, limit={limit}")
            logger.info(f"Найдено записей: {total_count}, возвращено: {returned_count}")

            return {
                'status': 'success',
                'params_used': {
                    'load_type': load_type,
                    'store_filter': store_filter,
                    'sort_by': sort_by,
                    'sort_order': sort_order,
                    'limit': limit
                },
                'count': returned_count,
                'total_in_query': total_count,
                'data': results if results else [],
                'message': f'Успешно выбрано {returned_count} записей из MongoDB'
            }

        except Exception as e:
            logger.error(f"Ошибка при селекте из MongoDB: {e}")
            return {
                'status': 'error',
                'params_used': params,
                'error': str(e),
                'message': 'Ошибка при выполнении запроса к MongoDB'
            }
        finally:
            if client:
                client.close()


    @task
    def format_results(result: Dict[str, Any], **context) -> str:
        """Форматирует результаты в JSON"""
        params = context['params']
        json_indent = params.get('json_indent', 2)
        max_sample = params.get('max_sample_display', 5)

        if result['status'] == 'error':
            error_output = {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error_details": {
                    "message": result.get('message'),
                    "error": result.get('error'),
                    "params_used": result.get('params_used', {})
                }
            }
            return json.dumps(error_output, indent=json_indent, ensure_ascii=False, default=str)

        data_to_display = result.get('data', [])

        # Если нужно ограничить количество отображаемых примеров
        if max_sample > 0 and len(data_to_display) > max_sample:
            sample_data = data_to_display[:max_sample]
            has_more = True
        else:
            sample_data = data_to_display
            has_more = False

        formatted_result = {
            "status": "success",
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "execution_id": context.get('ti', {}).execution_date.isoformat() if context.get('ti') else None,
                "dag_run_id": context.get('dag_run', {}).run_id if context.get('dag_run') else None,
                "params_used": result.get('params_used', {}),
                "statistics": {
                    "total_found": result.get('total_in_query', 0),
                    "returned_count": result.get('count', 0),
                    "sample_size": len(sample_data),
                    "has_more_data": has_more
                }
            },
            "data_sample": sample_data,
            "summary": result.get('message', '')
        }

        if has_more:
            formatted_result["metadata"]["statistics"]["hidden_records"] = len(data_to_display) - max_sample

        # Форматируем в JSON
        pretty_json = json.dumps(
            formatted_result,
            indent=json_indent,
            ensure_ascii=False,
            default=str,
            sort_keys=True
        )

        return pretty_json


    @task
    def log_pretty_json(pretty_json: str, **context) -> None:
        """Логирует отформатированный JSON"""
        params = context['params']
        json_indent = params.get('json_indent', 2)

        separator = "=" * 80

        logger.info("\n" + separator)
        logger.info("РЕЗУЛЬТАТ ВЫПОЛНЕНИЯ")
        logger.info(separator)

        logger.info(f"\n{pretty_json}")

        logger.info("\n" + "-" * 40)
        logger.info("КРАТКАЯ ИНФОРМАЦИЯ:")

        try:
            parsed = json.loads(pretty_json)
            if parsed.get('status') == 'success':
                stats = parsed['metadata']['statistics']
                logger.info(f"   - Статус: УСПЕШНО")
                logger.info(f"   - Найдено записей: {stats['total_found']}")
                logger.info(f"   - Получено записей: {stats['returned_count']}")
                logger.info(f"   - Примеров показано: {stats['sample_size']}")
                if stats.get('has_more_data'):
                    logger.info(f"   - Скрыто записей: {stats.get('hidden_records', 0)}")
                logger.info(f"   - Сообщение: {parsed.get('summary', '')}")
            else:
                error_info = parsed.get('error_details', {})
                logger.info(f"   - Статус: ОШИБКА")
                logger.info(f"   - Ошибка: {error_info.get('error', 'Неизвестная ошибка')}")
                logger.info(f"   - Сообщение: {error_info.get('message', '')}")
        except:
            logger.info("   - Результат не может быть распарсен как JSON")

        logger.info(separator + "\n")


    mongo_results = select_from_mongo()
    formatted_json = format_results(mongo_results)
    log_pretty_json(formatted_json)