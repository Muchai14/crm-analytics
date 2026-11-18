-- Staging: contacts.
select
    trim(contact_id) as contact_id,
    trim(account_id) as account_id,
    trim(first_name) || ' ' || trim(last_name) as contact_name,
    trim(email) as email,
    trim(title) as title,
    cast(created_date as date) as created_date
from {{ ref('raw_contacts') }}
