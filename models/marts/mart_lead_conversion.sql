-- Mart: lead-to-opportunity conversion and channel ROI by source and quarter.
-- Business question: "Which lead sources convert best and return the most
-- pipeline per marketing dollar?"
with leads as (
    select
        lead_id,
        lead_source,
        cast(year(created_date) as varchar) || '-Q' || cast(quarter(created_date) as varchar) as lead_quarter,
        status = 'Converted' as is_converted,
        converted_opportunity_id
    from {{ ref('stg_leads') }}
),
pipeline as (
    -- pipeline dollars created by converted leads (via their opportunity)
    select
        l.lead_source,
        l.lead_quarter,
        sum(o.amount) as pipeline_created
    from leads as l
    join {{ ref('stg_opportunities') }} as o
        on o.opportunity_id = l.converted_opportunity_id
    where l.is_converted
    group by 1, 2
),
agg as (
    select
        lead_source,
        lead_quarter,
        count(*) as leads,
        sum(case when is_converted then 1 else 0 end) as converted_leads
    from leads
    group by 1, 2
)
select
    a.lead_source,
    a.lead_quarter as quarter,
    a.leads,
    a.converted_leads,
    round(a.converted_leads / nullif(a.leads, 0), 3) as conversion_rate,
    coalesce(p.pipeline_created, 0) as pipeline_created,
    s.spend_amount,
    round(s.spend_amount / nullif(a.leads, 0), 2) as cost_per_lead,
    round(coalesce(p.pipeline_created, 0) / nullif(s.spend_amount, 0), 2) as pipeline_per_dollar,
    a.lead_source || '|' || a.lead_quarter as conversion_key
from agg as a
left join pipeline as p
    on p.lead_source = a.lead_source
    and p.lead_quarter = a.lead_quarter
left join {{ ref('stg_marketing_spend') }} as s
    on s.lead_source = a.lead_source
    and s.quarter = a.lead_quarter
