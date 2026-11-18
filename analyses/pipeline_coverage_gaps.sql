-- Business question: which segments are below a healthy 3x pipeline
-- coverage for the upcoming quarter, and by how much?
select
    quarter,
    segment,
    open_pipeline,
    quota,
    coverage_ratio,
    -- dollars of pipeline still needed to reach 3x coverage
    greatest(3 * quota - open_pipeline, 0) as pipeline_gap_to_3x
from {{ ref('mart_pipeline_coverage') }}
where coverage_ratio < 3
order by coverage_ratio
