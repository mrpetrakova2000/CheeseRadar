{% macro clean_price(price_str) %}
    CASE
        WHEN {{ price_str }} IS NOT NULL AND {{ price_str }} != '' THEN
            NULLIF(
                CAST(
                    REGEXP_REPLACE(
                        TRIM({{ price_str }}),
                        ',', '.', 'g'
                    ) AS NUMERIC
                ),
                0
            )
        ELSE NULL
    END
{% endmacro %}

{% macro extract_weight_and_unit(name) %}
    CASE
        WHEN {{ name }} ~ '\d+[.,]?\d*[гкгмл]' THEN
            '{"weight": ' ||
            REGEXP_REPLACE(
                SUBSTRING({{ name }} FROM '(\d+[.,]?\d*)(?=[гкгмл])'),
                ',', '.'
            ) ||
            ', "unit": "' ||
            CASE
                WHEN {{ name }} ~ '\d+[.,]?\d*г' THEN 'г'
                WHEN {{ name }} ~ '\d+[.,]?\d*кг' THEN 'кг'
                WHEN {{ name }} ~ '\d+[.,]?\d*мл' THEN 'мл'
                WHEN {{ name }} ~ '\d+[.,]?\d*л' THEN 'л'
                ELSE 'кг'
            END ||
            '"}'

        ELSE '{"weight": null, "unit": null}'
    END
{% endmacro %}

{% macro extract_weight_value(name) %}
    CAST(
        NULLIF(
            ({{ extract_weight_and_unit(name) }}::JSONB)->>'weight',
            'null'
        ) AS NUMERIC
    )
{% endmacro %}

{% macro extract_weight_unit(name) %}
    NULLIF(
        ({{ extract_weight_and_unit(name) }}::JSONB)->>'unit',
        'null'
    )
{% endmacro %}

{% macro extract_fat_content(name) %}
    CAST(
        REGEXP_REPLACE(
            COALESCE(
                (SELECT (REGEXP_MATCH({{ name }}, '([0-9]+)%'))[1]),
                '0'
            ),
            ',', '.'
        ) AS NUMERIC
    )
{% endmacro %}

{% macro is_sliced(name) %}
    CASE
        WHEN LOWER({{ name }}) LIKE '%нарезка%' THEN TRUE
        WHEN LOWER({{ name }}) LIKE '%слайс%' THEN TRUE
        ELSE FALSE
    END
{% endmacro %}

{% macro is_bzmj(name) %}
    CASE
        WHEN LOWER({{ name }}) LIKE '%бзмж%' THEN TRUE
        ELSE FALSE
    END
{% endmacro %}

{% macro is_creamy(name) %}
    CASE
        WHEN (LOWER({{ name }}) LIKE '%плавлен%' OR LOWER({{ name }}) LIKE '%творожн%')
             AND LOWER({{ name }}) NOT LIKE '%ломт%'
        THEN TRUE
        ELSE FALSE
    END
{% endmacro %}

{% macro clean_discount(discount_str) %}
    CASE
        WHEN {{ discount_str }} IS NOT NULL AND TRIM({{ discount_str }}) != '' THEN
            CAST(
                NULLIF(
                    REGEXP_REPLACE(
                        REGEXP_REPLACE({{ discount_str }}, '[^0-9,.]', '', 'g'),
                        ',', '.'
                    ),
                    ''
                ) AS NUMERIC
            )
        ELSE NULL
    END
{% endmacro %}
