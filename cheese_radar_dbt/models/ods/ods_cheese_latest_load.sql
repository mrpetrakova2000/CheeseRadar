{{
    config(
        materialized='table',
        tags=['ods', 'cheeseprice', 'latest_load']
    )
}}

WITH last_load_time AS (
    SELECT MAX(scraped_at) as latest_scrape
    FROM {{ ref('stg_postgres_raw') }}
),

last_load_data AS (
    SELECT
        name,
        store,
        price_raw,
        discount_raw,
        rating_raw,
        scraped_at,
        scraped_date,
        processed_at,

        ROW_NUMBER() OVER (
            PARTITION BY name, store
            ORDER BY scraped_at DESC
        ) as rn
    FROM {{ ref('stg_postgres_raw') }} p
    CROSS JOIN last_load_time lt
    WHERE p.scraped_at = lt.latest_scrape
      AND price_raw IS NOT NULL
      AND price_raw != ''
      AND TRIM(price_raw) != ''
)

SELECT
    name,
    store,
    DATE(scraped_at) as date_added,

    -- Цена
    {{ clean_price('price_raw') }} as price,

    -- Вес и единица измерения
    {{ extract_weight_value('name') }} as weight,
    {{ extract_weight_unit('name') }} as unit,

    -- Жирность
    {{ extract_fat_content('name') }} as fat_content,

    -- Дополнительные признаки
    {{ is_sliced('name') }} as is_sliced,
    {{ is_bzmj('name') }} as is_bzmj,
    {{ is_creamy('name') }} as is_creamy,

    -- Скидка и рейтинг
    {{ clean_discount('discount_raw') }} as discount,
    CAST(rating_raw AS NUMERIC) as rating,

    scraped_at,
    scraped_date,
    processed_at,

    -- Цена за кг
    CASE
        WHEN {{ extract_weight_unit('name') }} = 'кг'
             AND {{ extract_weight_value('name') }} > 0
             AND {{ clean_price('price_raw') }} > 0
        THEN ROUND({{ clean_price('price_raw') }} / {{ extract_weight_value('name') }}, 2)
        WHEN {{ extract_weight_unit('name') }} = 'г'
             AND {{ extract_weight_value('name') }} > 0
             AND {{ clean_price('price_raw') }} > 0
        THEN ROUND(({{ clean_price('price_raw') }} / {{ extract_weight_value('name') }}) * 1000, 2)
        ELSE NULL
    END as price_per_kg,

    current_timestamp as ods_processed_at

FROM last_load_data
WHERE rn = 1
  AND {{ clean_price('price_raw') }} IS NOT NULL
  AND {{ clean_price('price_raw') }} > 0
ORDER BY store, name
