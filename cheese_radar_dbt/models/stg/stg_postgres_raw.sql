{{
    config(
        materialized='incremental',
        unique_key='product_uid',
        tags=['stg', 'products']
    )
}}

SELECT
    {{ dbt_utils.generate_surrogate_key(['name', 'store', 'date_time']) }} as product_uid,

    id as source_id,
    name,
    store,

    price as price_raw,
    discount as discount_raw,
    rating as rating_raw,

    date_time::timestamp as scraped_at,
    DATE(date_time::timestamp) as scraped_date,
    created_at,

    current_timestamp as processed_at

FROM {{ source('postgres', 'products') }}
WHERE name IS NOT NULL
  AND name != ''
  AND store IS NOT NULL

{% if is_incremental() %}
  AND date_time::timestamp > (
    SELECT MAX(scraped_at)
    FROM {{ this }}
  )
{% endif %}
