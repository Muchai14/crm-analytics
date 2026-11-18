-- Business question: which reps have the best win rate on large deals
-- (>$250k), with at least 5 closed large deals for significance?
select
    rep,
    segment,
    closed_deals,
    won_deals,
    win_rate
from {{ ref('mart_win_rate') }}
where deal_size_band = 'Large (>$250k)'
  and closed_deals >= 5
order by win_rate desc
