-- Mart: win rate by segment, deal-size band and rep.
-- Business question: "Who closes best, and where do we win or lose?"
select
    segment,
    deal_size_band,
    owner as rep,
    count(*) as closed_deals,
    sum(case when is_won then 1 else 0 end) as won_deals,
    round(
        sum(case when is_won then 1 else 0 end) / nullif(count(*), 0), 3
    ) as win_rate,
    segment || '|' || deal_size_band || '|' || owner as win_rate_key
from {{ ref('int_opportunity_funnel') }}
where is_closed
group by 1, 2, 3
