-- Business question: do lost deals drag longer than won deals,
-- and which segment has the longest cycle?
select
    segment,
    outcome,
    deal_count,
    avg_cycle_days,
    median_cycle_days
from {{ ref('mart_sales_cycle') }}
order by avg_cycle_days desc
