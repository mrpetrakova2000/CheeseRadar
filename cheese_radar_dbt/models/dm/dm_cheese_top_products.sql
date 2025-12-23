{{
    config(
        materialized='table',
        tags=['dm', 'top', 'products']
    )
}}

WITH current_data AS (
    SELECT *
    FROM {{ ref('ods_cheese_latest_load') }}
),

ranked_products AS (
    SELECT
        name,
        store,
        price,
        price_per_kg,
        discount,
        rating,
        fat_content,
        weight,
        unit,
        is_sliced,
        is_bzmj,
        is_creamy,
        scraped_at,

        ROW_NUMBER() OVER (
            ORDER BY price_per_kg ASC
        ) as rank_cheapest,

        ROW_NUMBER() OVER (
            ORDER BY discount DESC NULLS LAST
        ) as rank_best_discount,

        ROW_NUMBER() OVER (
            ORDER BY rating DESC NULLS LAST
        ) as rank_best_rating,

        ROW_NUMBER() OVER (
            ORDER BY price_per_kg / NULLIF(fat_content, 0) ASC
        ) as rank_best_value

    FROM current_data
    WHERE price_per_kg IS NOT NULL
)

SELECT
    name,
    store,
    price,
    ROUND(price_per_kg, 2) as price_per_kg,
    discount,
    rating,
    fat_content,
    weight,
    unit,
    is_sliced,
    is_bzmj,
    is_creamy,
    scraped_at,

    rank_cheapest,
    rank_best_discount,
    rank_best_rating,
    rank_best_value,

    CASE
        WHEN rank_cheapest <= 10 THEN true
        ELSE false
    END as in_top_10_cheapest,

    CASE
        WHEN rank_best_discount <= 10 THEN true
        ELSE false
    END as in_top_10_discounts,

    CASE
        WHEN rank_best_rating <= 10 THEN true
        ELSE false
    END as in_top_10_ratings,

    CASE
        WHEN rank_cheapest <= 10 OR rank_best_discount <= 10 OR rank_best_rating <= 10
        THEN true
        ELSE false
    END as in_any_top_10,

    CASE
        WHEN rank_cheapest <= 5 THEN 'Самый дешевый'
        WHEN rank_best_discount <= 5 THEN 'Лучшая скидка'
        WHEN rank_best_rating <= 5 THEN 'Лучший рейтинг'
        WHEN rank_best_value <= 5 THEN 'Лучшее соотношение цена/жирность'
        ELSE 'Стандартный'
    END as recommendation_type,

    current_timestamp as ranked_at

FROM ranked_products
WHERE rank_cheapest <= 20
   OR rank_best_discount <= 20
   OR rank_best_rating <= 20
   OR rank_best_value <= 20
ORDER BY
    rank_cheapest,
    rank_best_discount,
    scraped_at DESC
