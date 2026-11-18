-- Staging: marketing spend by lead source and quarter (for channel ROI).
select
    trim(source) as lead_source,
    trim(quarter) as quarter,
    cast(spend_amount as integer) as spend_amount
from {{ ref('raw_marketing_spend') }}
