{% test accepted_range(model, column_name, min_value=0, max_value=100) %}
    {{ config(tags = ['warn']) }}

    select *
    from {{ model }}
    where {{ column_name }} is not null
      and ({{ column_name }} < {{ min_value }}
           or {{ column_name }} > {{ max_value }})
{% endtest %}
