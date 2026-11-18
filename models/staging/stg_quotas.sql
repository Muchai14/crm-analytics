-- Staging: quarterly sales quotas by segment.
select
    trim(segment) as segment,
    trim(quarter) as quarter,
    cast(quota_amount as integer) as quota_amount
from {{ ref('raw_quotas') }}
