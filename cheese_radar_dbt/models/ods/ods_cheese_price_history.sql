{{
    config(
        materialized='incremental',
        unique_key=['name', 'store', 'scraped_at'],
        tags=['ods', 'cheeseprice', 'history']
    )
}}

WITH base_data AS (
    SELECT
        name,
        store,
        price_raw,
        discount_raw,
        scraped_at,
        scraped_date,
        processed_at,

        {{ clean_price('price_raw') }} as price,
        {{ extract_weight_value('name') }} as weight,
        {{ extract_weight_unit('name') }} as unit,
        {{ extract_fat_content('name') }} as fat_content,
        {{ is_sliced('name') }} as is_sliced,
        {{ is_bzmj('name') }} as is_bzmj,
        {{ is_creamy('name') }} as is_creamy,
        {{ clean_discount('discount_raw') }} as discount,
        CAST(rating_raw AS NUMERIC) as rating

    FROM {{ ref('stg_postgres_raw') }}
    WHERE price_raw IS NOT NULL
      AND price_raw != ''
      AND TRIM(price_raw) != ''
)

SELECT
    name,
    store,
    scraped_date as date_added,

    price,
    weight,
    unit,
    fat_content,
    is_sliced,
    is_bzmj,
    is_creamy,
    discount,

    scraped_at,
    scraped_date,
    processed_at,

    -- Цена за кг
    CASE
        WHEN unit = 'кг' AND weight > 0 AND price > 0
        THEN ROUND(price / weight, 2)
        WHEN unit = 'г' AND weight > 0 AND price > 0
        THEN ROUND((price / weight) * 1000, 2)
        ELSE NULL
    END as price_per_kg,

    LAG(price) OVER (
        PARTITION BY name, store
        ORDER BY scraped_at
    ) as prev_price,

    LAG(scraped_at) OVER (
        PARTITION BY name, store
        ORDER BY scraped_at
    ) as prev_scraped_at,

    current_timestamp as ods_processed_at

FROM base_data
WHERE price IS NOT NULL
  AND price > 0

{% if is_incremental() %}
    AND processed_at >= (
        SELECT COALESCE(MAX(processed_at), '1900-01-01'::timestamp)
        FROM {{ this }}
    )
{% endif %}

ORDER BY name, store, scraped_at DESC
