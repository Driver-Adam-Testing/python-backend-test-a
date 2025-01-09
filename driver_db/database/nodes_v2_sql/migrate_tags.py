MIGRATE_TAGS = """

WITH tags_primary_asset_ids AS (
SELECT DISTINCT
    t.tag_id as tag_id,
    v.primary_asset_id as primary_asset_id
FROM tags_contents t
JOIN derived_contents dc on t.content_id = dc.id
LEFT JOIN v2_node n on (dc.node_id = n.id or n.relative_path = CONCAT(dc.relative_path, '/'))
LEFT JOIN v2_version v on v.id = n.version_id
where v.primary_asset_id is NOT NULL
)
INSERT INTO v2_primary_asset_tag (
    tag_id,
    primary_asset_id
)
SELECT
    tag_id,
    primary_asset_id
FROM tags_primary_asset_ids
RETURNING tag_id;

"""
