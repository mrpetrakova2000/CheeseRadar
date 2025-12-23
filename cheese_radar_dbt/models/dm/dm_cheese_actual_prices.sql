{{
    config(
        materialized='table',
        tags=['dm', 'current', 'cheeseprices']
    )
}}

WITH current_data AS (
    SELECT
        name,
        store,
        date_added,
        price,
        weight,
        unit,
        fat_content,
        is_sliced,
        is_bzmj,
        is_creamy,
        discount,
        rating,
        price_per_kg,
        scraped_at
    FROM {{ ref('ods_cheese_latest_load') }}
)

SELECT
    name,
    store,
    date_added,
    price,
    weight,
    unit,
    fat_content,
    is_sliced,
    is_bzmj,
    is_creamy,
    discount,
    rating,
    price_per_kg,
    scraped_at,

    CASE
        WHEN price_per_kg < 500 THEN 'Очень дешево (<500 руб/кг)'
        WHEN price_per_kg BETWEEN 500 AND 800 THEN 'Дешево (500-800 руб/кг)'
        WHEN price_per_kg BETWEEN 801 AND 1200 THEN 'Средняя (801-1200 руб/кг)'
        WHEN price_per_kg BETWEEN 1201 AND 2000 THEN 'Дорого (1201-2000 руб/кг)'
        WHEN price_per_kg > 2000 THEN 'Очень дорого (>2000 руб/кг)'
        ELSE 'Неизвестно'
    END as price_category,

    CASE
        WHEN fat_content < 20 THEN 'Низкая (<20%)'
        WHEN fat_content BETWEEN 20 AND 30 THEN 'Средняя (20-30%)'
        WHEN fat_content BETWEEN 31 AND 45 THEN 'Высокая (31-45%)'
        WHEN fat_content > 45 THEN 'Очень высокая (>45%)'
        ELSE 'Не указана'
    END as fat_category,

    CASE
        WHEN unit = 'г' AND weight < 150 THEN 'Маленькая (<150г)'
        WHEN unit = 'г' AND weight BETWEEN 150 AND 300 THEN 'Средняя (150-300г)'
        WHEN unit = 'г' AND weight BETWEEN 301 AND 500 THEN 'Большая (301-500г)'
        WHEN unit = 'г' AND weight > 500 THEN 'Очень большая (>500г)'
        WHEN unit = 'кг' THEN 'Килограммовый'
        ELSE 'Другая'
    END as size_category,

    discount > 0 as has_discount,
    rating IS NOT NULL as has_rating,
    is_sliced as is_sliced_cheese,
    is_bzmj as is_bzmj_cheese,
    is_creamy as is_creamy_cheese,

    CASE
        WHEN discount > 15 AND price_per_kg < 1000 THEN 'Отличная сделка'
        WHEN discount > 10 AND price_per_kg < 1200 THEN 'Хорошая цена'
        WHEN price_per_kg < 700 THEN 'Бюджетный вариант'
        WHEN rating > 4.0 THEN 'Высокий рейтинг'
        ELSE 'Стандартное предложение'
    END as recommendation,

    current_timestamp as snapshot_created_at

FROM current_data
ORDER BY
    store,
    price_per_kg ASC,
    scraped_at DESC
