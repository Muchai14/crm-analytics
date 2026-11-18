-- Staging: activities (calls, emails, meetings, demos on leads/opportunities).
select
    trim(activity_id) as activity_id,
    trim(what_id) as what_id,
    trim(what_type) as what_type,
    trim(activity_type) as activity_type,
    cast(activity_date as date) as activity_date,
    trim(owner) as owner
from {{ ref('raw_activities') }}
