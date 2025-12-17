{{
    config(
        materialized='table',
        tags=['dm', 'metrics', 'aggregated']
    )
}}

WITH current_data AS (
    SELECT *
    FROM {{ ref('ods_cheese_latest_load') }}
),

store_metrics AS (
    SELECT
        store,

        COUNT(*) as total_products,

        ROUND(AVG(price), 2) as avg_price,
        ROUND(MIN(price), 2) as min_price,
        ROUND(MAX(price), 2) as max_price,
        ROUND(AVG(price_per_kg), 2) as avg_price_per_kg,
        ROUND(MIN(price_per_kg), 2) as min_price_per_kg,
        ROUND(MAX(price_per_kg), 2) as max_price_per_kg,

        COUNT(CASE WHEN discount > 0 THEN 1 END) as discounted_products,
        ROUND(AVG(CASE WHEN discount > 0 THEN discount END), 2) as avg_discount,
        ROUND(MAX(discount), 2) as max_discount,
        -- Вычисляем процент товаров со скидкой сразу здесь
        ROUND(
            COUNT(CASE WHEN discount > 0 THEN 1 END)::DECIMAL
            / NULLIF(COUNT(*), 0)
            * 100,
            2
        ) as discount_coverage_pct,

        COUNT(CASE WHEN rating IS NOT NULL THEN 1 END) as rated_products,
        ROUND(AVG(rating), 2) as avg_rating,
        ROUND(
            COUNT(CASE WHEN rating IS NOT NULL THEN 1 END)::DECIMAL
            / NULLIF(COUNT(*), 0)
            * 100,
            2
        ) as rating_coverage_pct,

        ROUND(AVG(weight), 2) as avg_weight,
        ROUND(AVG(CASE WHEN unit = 'г' THEN weight END), 2) as avg_weight_grams,

        ROUND(AVG(fat_content), 2) as avg_fat_content,
        COUNT(CASE WHEN fat_content IS NOT NULL THEN 1 END) as products_with_fat_info,
        ROUND(
            COUNT(CASE WHEN fat_content IS NOT NULL THEN 1 END)::DECIMAL
            / NULLIF(COUNT(*), 0)
            * 100,
            2
        ) as fat_info_coverage_pct,

        COUNT(CASE WHEN is_sliced THEN 1 END) as sliced_count,
        COUNT(CASE WHEN is_bzmj THEN 1 END) as bzmj_count,
        COUNT(CASE WHEN is_creamy THEN 1 END) as creamy_count

    FROM current_data
    GROUP BY store
),

price_distribution AS (
    SELECT
        store,

        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price_per_kg) as price_per_kg_q1,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_per_kg) as price_per_kg_median,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price_per_kg) as price_per_kg_q3,

        ROUND(STDDEV(price_per_kg), 2) as price_per_kg_stddev

    FROM current_data
    WHERE price_per_kg IS NOT NULL
    GROUP BY store
)

SELECT
    sm.store,

    sm.total_products,

    sm.avg_price,
    sm.min_price,
    sm.max_price,
    sm.avg_price_per_kg,
    sm.min_price_per_kg,
    sm.max_price_per_kg,

    pd.price_per_kg_q1,
    pd.price_per_kg_median,
    pd.price_per_kg_q3,
    pd.price_per_kg_stddev,

    sm.discounted_products,
    sm.avg_discount,
    sm.max_discount,
    sm.discount_coverage_pct,

    sm.rated_products,
    sm.avg_rating,
    sm.rating_coverage_pct,

    sm.avg_weight,
    sm.avg_weight_grams,

    sm.avg_fat_content,
    sm.products_with_fat_info,
    sm.fat_info_coverage_pct,

    sm.sliced_count,
    sm.bzmj_count,
    sm.creamy_count,
    ROUND(sm.sliced_count::DECIMAL / sm.total_products * 100, 2) as sliced_pct,
    ROUND(sm.bzmj_count::DECIMAL / sm.total_products * 100, 2) as bzmj_pct,

    CASE
        WHEN sm.avg_price_per_kg < 700 THEN 'Бюджетный'
        WHEN sm.avg_price_per_kg BETWEEN 700 AND 1200 THEN 'Средний'
        WHEN sm.avg_price_per_kg > 1200 THEN 'Премиум'
        ELSE 'Неизвестно'
    END as store_price_category,

    CASE
        WHEN sm.discount_coverage_pct > 30 THEN 'Много акций'
        WHEN sm.discount_coverage_pct > 15 THEN 'Умеренные акции'
        ELSE 'Мало акций'
    END as store_promo_category,

    current_timestamp as metrics_calculated_at

FROM store_metrics sm
LEFT JOIN price_distribution pd ON sm.store = pd.store
ORDER BY sm.total_products DESC