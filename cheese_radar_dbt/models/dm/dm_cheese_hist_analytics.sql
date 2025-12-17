{{
    config(
        materialized='table',
        tags=['dm', 'dashboard']
    )
}}

WITH history AS (
    SELECT
        name,
        store,
        price_per_kg,
        discount,
        scraped_at
    FROM {{ ref('ods_cheese_price_history') }}
    WHERE scraped_at >= CURRENT_DATE - INTERVAL '30 days'
),

latest_data AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY name, store
            ORDER BY scraped_at DESC
        ) = 1 as is_latest
    FROM history
)

SELECT
    name,
    store,

    MAX(CASE WHEN is_latest THEN price_per_kg END) as price_per_kg_now,
    MAX(CASE WHEN is_latest THEN discount END) as discount_now,

    ROUND(AVG(price_per_kg), 2) as price_month_avg,
    ROUND(MIN(price_per_kg), 2) as price_month_min,
    ROUND(MAX(price_per_kg), 2) as price_month_max,

    ROUND(
        MAX(CASE WHEN is_latest THEN price_per_kg END) - AVG(price_per_kg),
        2
    ) as diff_vs_avg,
    ROUND(
        (MAX(CASE WHEN is_latest THEN price_per_kg END) - AVG(price_per_kg)) /
        NULLIF(AVG(price_per_kg), 0) * 100,
        1
    ) as diff_vs_avg_pct,

    CASE
        WHEN MAX(CASE WHEN is_latest THEN price_per_kg END) < AVG(price_per_kg) * 0.95
        THEN 'дешевле чем обычно'
        WHEN MAX(CASE WHEN is_latest THEN price_per_kg END) > AVG(price_per_kg) * 1.05
        THEN 'дороже чем обычно'
        ELSE 'обычная цена'
    END as price_comment,

    CASE
        WHEN MAX(CASE WHEN is_latest THEN discount END) > 10 THEN 'хорошая скидка'
        WHEN MAX(CASE WHEN is_latest THEN price_per_kg END) < AVG(price_per_kg)
        THEN 'низкая цена'
        ELSE 'стандарт'
    END as deal_status

FROM latest_data
GROUP BY name, store
HAVING COUNT(*) >= 3
ORDER BY store, name