-- Business question: which lead sources deliver the best pipeline ROI
-- over the last four quarters?
select
    lead_source,
    sum(leads) as leads,
    round(sum(converted_leads) / nullif(sum(leads), 0), 3) as conversion_rate,
    sum(pipeline_created) as pipeline_created,
    sum(spend_amount) as spend,
    round(sum(pipeline_created) / nullif(sum(spend_amount), 0), 2) as pipeline_per_dollar
from {{ ref('mart_lead_conversion') }}
group by 1
order by pipeline_per_dollar desc
