-- Mart: sales cycle length by segment and outcome.
-- Business question: "How long does it take to close, and do lost deals drag longer?"
select
    segment,
    case when is_won then 'Won' else 'Lost' end as outcome,
    count(*) as deal_count,
    round(avg(sales_cycle_days), 1) as avg_cycle_days,
    round(median(sales_cycle_days), 1) as median_cycle_days,
    min(sales_cycle_days) as min_cycle_days,
    max(sales_cycle_days) as max_cycle_days,
    segment || '|' || case when is_won then 'Won' else 'Lost' end as cycle_key
from {{ ref('int_opportunity_funnel') }}
where is_closed
group by 1, 2
