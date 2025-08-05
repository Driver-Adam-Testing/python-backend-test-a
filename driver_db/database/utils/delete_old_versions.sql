-- CTE to find all versions with their row numbers based on created_at
WITH version_ranks AS (
  SELECT
    v.id,
    v.primary_asset_id,
    v.created_at,
    ROW_NUMBER() OVER (PARTITION BY v.primary_asset_id ORDER BY v.created_at DESC) AS row_num
  FROM v2_version v
),

-- CTE to identify versions in use
used_versions AS (
  SELECT DISTINCT vn.version_id
  FROM v2_node vn
  JOIN public.document_sources ds ON vn.id = ds.source_node_id
),

-- CTE to select old, unused versions beyond the 10 most recent
old_unused_versions AS (
  SELECT vr.id
  FROM version_ranks vr
  LEFT JOIN used_versions uv ON vr.id = uv.version_id
  WHERE vr.row_num > 10
    AND uv.version_id IS NULL
)

-- Delete identified versions
DELETE FROM v2_version
WHERE id IN (SELECT id FROM old_unused_versions);
