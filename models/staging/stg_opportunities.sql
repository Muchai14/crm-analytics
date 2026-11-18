-- Staging: opportunities. Cleans raw seed data: trims strings,
-- casts dates/amounts, drops exact duplicates on the natural key.
with source as (
    select * from {{ ref('raw_opportunities') }}
),
deduped as (
    select
        *,
        row_number() over (partition by opportunity_id order by created_date) as _rn
    from source
)
select
    trim(opportunity_id) as opportunity_id,
    trim(account_id) as account_id,
    nullif(trim(primary_contact_id), '') as primary_contact_id,
    trim(name) as opportunity_name,
    trim(stage) as stage,
    cast(amount as integer) as amount,
    cast(probability as integer) as probability,
    cast(close_date as date) as close_date,
    cast(created_date as date) as created_date,
    trim(owner) as owner,
    trim(lead_source) as lead_source,
    trim(segment) as segment,
    nullif(trim(converted_lead_id), '') as converted_lead_id
from deduped
where _rn = 1
