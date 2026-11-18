-- Staging: accounts.
select
    trim(account_id) as account_id,
    trim(account_name) as account_name,
    trim(industry) as industry,
    trim(segment) as segment,
    trim(region) as region,
    cast(employee_count as integer) as employee_count,
    cast(created_date as date) as created_date
from {{ ref('raw_accounts') }}
