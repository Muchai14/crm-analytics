-- Staging: leads. Same cleaning pattern as stg_opportunities.
with source as (
    select * from {{ ref('raw_leads') }}
),
deduped as (
    select
        *,
        row_number() over (partition by lead_id order by created_date) as _rn
    from source
)
select
    trim(lead_id) as lead_id,
    trim(company) as company,
    trim(first_name) || ' ' || trim(last_name) as lead_name,
    trim(email) as email,
    trim(source) as lead_source,
    trim(status) as status,
    cast(created_date as date) as created_date,
    cast(converted_date as date) as converted_date,
    trim(owner) as owner,
    nullif(trim(converted_opportunity_id), '') as converted_opportunity_id
from deduped
where _rn = 1
