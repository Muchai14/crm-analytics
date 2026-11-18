-- Mart: pipeline coverage by quarter and segment.
-- Business question: "Do we have enough open pipeline to hit this quarter's quota?"
-- Rule of thumb: healthy coverage is ~3x quota.
with open_pipe as (
    select
        close_quarter,
        segment,
        sum(amount) as open_pipeline,
        count(*) as num_open_deals
    from {{ ref('int_opportunity_funnel') }}
    where is_open
    group by 1, 2
)
select
    p.close_quarter as quarter,
    p.segment,
    p.open_pipeline,
    q.quota_amount as quota,
    round(p.open_pipeline / nullif(q.quota_amount, 0), 2) as coverage_ratio,
    p.num_open_deals,
    p.close_quarter || '|' || p.segment as coverage_key
from open_pipe as p
left join {{ ref('stg_quotas') }} as q
    on q.quarter = p.close_quarter
    and q.segment = p.segment
