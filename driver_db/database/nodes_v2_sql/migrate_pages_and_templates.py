MIGRATE_PAGES = """

WITH pages AS (
    SELECT
        dc.id,
        w.organization_id              AS org_id,
        dc.content_name,
        dc.relative_path,
        dc.created_at,
        dc.updated_at,
        dc.content_kind,

        -- Use ROW_NUMBER to differentiate duplicate content_name
        ROW_NUMBER() OVER (
            PARTITION BY w.organization_id, dc.content_name
            ORDER BY dc.created_at
        ) AS rn
    FROM derived_contents dc
    JOIN workspaces w
      ON w.id = dc.workspace_id
    WHERE dc.content_kind IN ('application_note', 'template')
      AND dc.content_name IS NOT NULL
),

ins_primary_asset AS (
    -- Insert a row into v2_primary_asset for each "page."
    -- We reuse dc.id as the primary key. If the same content_name appears multiple times
    -- for the same org, "rn" will be > 1, so we add a suffix to display_name.
    INSERT INTO v2_primary_asset (
        id,
        display_name,
        repository_id,
        organization_id,
        kind,
        created_at,
        updated_at
    )
    SELECT
        p.id,  -- Reuse derived_contents.id as primary_asset.id
        CASE
            WHEN p.rn > 1
                 THEN p.content_name || '-' || (p.rn - 1)::text
            ELSE p.content_name
        END            AS display_name,
        NULL           AS repository_id,
        p.org_id       AS organization_id,
        CASE
          WHEN p.content_kind = 'template'         THEN 'PAGE_TEMPLATE'
          WHEN p.content_kind = 'application_note' THEN 'PAGE'
        END            AS kind,
        p.created_at,
        p.updated_at
    FROM pages p

    -- Don't reference p.* in RETURNING to avoid "missing FROM-clause" errors.
    -- If you need a 'RETURNING', only return columns from v2_primary_asset itself:
    RETURNING id
),

ins_version AS (
    -- Insert a row into v2_version, again reusing p.id
    -- for both the version "id" and the primary_asset_id.
    INSERT INTO v2_version (
        id,
        primary_asset_id,
        display_name,
        created_at,
        updated_at,
        status
    )
    SELECT
        p.id,      -- version.id = dc.id
        p.id,      -- primary_asset_id = same dc.id
        'v' || p.rn::text  AS display_name,  -- e.g. "v1", "v2" for duplicates
        p.created_at,
        p.updated_at,
        'GENERATION-COMPLETE'
    FROM pages p
    RETURNING id
),

ins_node AS (
    -- Insert a row into v2_node, also reusing p.id for both node.id and version_id.
    INSERT INTO v2_node (
        id,
        version_id,
        relative_path,
        created_at,
        updated_at
    )
    SELECT
        p.id,      -- node.id = dc.id
        p.id,      -- version_id = same dc.id
        p.relative_path,
        p.created_at,
        p.updated_at
    FROM pages p
    RETURNING id
),

ins_update AS (
    -- Update each derived_contents so node_id points to its own id.
    UPDATE derived_contents d
    SET node_id = d.id
    WHERE d.content_kind IN ('application_note', 'template')
      AND d.content_name IS NOT NULL
    RETURNING d.*
)

SELECT *
FROM ins_update;

"""
