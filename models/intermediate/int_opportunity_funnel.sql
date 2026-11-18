-- Intermediate: opportunity funnel state machine.
-- Adds stage ordering, open/closed/won flags, quarter grain, deal-size bands
-- and (for closed deals) the realized sales cycle in days.
select
    o.opportunity_id,
    o.account_id,
    o.opportunity_name,
    o.stage,
    case o.stage
        when 'Prospecting' then 1
        when 'Qualification' then 2
        when 'Needs Analysis' then 3
        when 'Proposal' then 4
        when 'Closed Won' then 5
        when 'Closed Lost' then 5
    end as stage_order,
    o.amount,
    case
        when o.amount < 50000 then 'Small (<$50k)'
        when o.amount < 250000 then 'Mid ($50k-$250k)'
        else 'Large (>$250k)'
    end as deal_size_band,
    o.probability,
    o.close_date,
    o.created_date,
    -- quarter grain derived from forecast/actual close date, format YYYY-Qn
    cast(year(o.close_date) as varchar) || '-Q' || cast(quarter(o.close_date) as varchar) as close_quarter,
    o.owner,
    o.lead_source,
    o.segment,
    o.converted_lead_id,
    o.stage in ('Closed Won', 'Closed Lost') as is_closed,
    o.stage = 'Closed Won' as is_won,
    o.stage not in ('Closed Won', 'Closed Lost') as is_open,
    -- sales cycle only meaningful once the deal is closed
    case
        when o.stage in ('Closed Won', 'Closed Lost')
            then date_diff('day', o.created_date, o.close_date)
    end as sales_cycle_days
from {{ ref('stg_opportunities') }} as o
