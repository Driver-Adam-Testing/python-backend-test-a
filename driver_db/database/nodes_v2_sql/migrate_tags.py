MIGRATE_TAGS = """

WITH tags_primary_asset_ids AS (
    SELECT
        t.tag_id as tag_id,
        t.content_id as content_id
        CASE
            WHEN pa.id IS NOT NULL
                THEN pa.id -- this should cover codebases, pages, and templates
            WHEN pa.id IS NULL AND v.id IS NOT NULL
                THEN v.primary_asset_id -- this should cover pdfs
        END as primary_asset_id
    FROM tags_contents t
    LEFT JOIN v2_primary_asset pa on t.content_id = pa.id
    LEFT JOIN v2_version v on t.content_id = v.id
),
ins_v2_primary_asset_tag AS (
    INSERT INTO v2_primary_asset_tag (
        tag_id,
        primary_asset_id
    )
    SELECT
        tag_id,
        primary_asset_id
    FROM tags_primary_asset_ids
    RETURNING tag_id
)

"""
