MIGRATE_CODEBASE = """
WITH ordered_codebase_versions AS (
    SELECT
        dc.id                   AS version_id_from_dc_codebase,        -- the derived_content ID
        w.organization_id       AS org_id,            -- from the workspace
        c.codebase_name         AS codebase_name,
        c.id                    AS codebase_id,
        dc.created_at,
        dc.updated_at,

        -- If relative_path is in your table, keep it or adapt.
        -- We'll do a quick case to ensure a trailing slash, if desired:
        CASE
            WHEN dc.relative_path IS NOT NULL
                 AND RIGHT(dc.relative_path, 1) <> '/'
            THEN dc.relative_path || '/'
            ELSE dc.relative_path
        END AS relative_path_dir,

        -- If you have an "inspection_versions" join (left or inner) to get
        -- an inspector_version_id + display_name:
        ir.id            AS inspector_version_id,
        CASE
            WHEN ir.display_name = 'Unversioned'
                THEN ir.display_name
                 || ROW_NUMBER() OVER (
                        PARTITION BY w.organization_id, c.codebase_name
                        ORDER BY dc.created_at
                    )
            WHEN ir.display_name IS NOT NULL
                 THEN ir.display_name
            ELSE '0.0.'
                 || ROW_NUMBER() OVER (
                        PARTITION BY w.organization_id, c.codebase_name
                        ORDER BY dc.created_at
                    )
        END AS version_display_name,

        -- Parse out the GitHub repo ID from the JSON.
        -- If your JSON is in a column like 'dc.misc_metadata', do:
        (dc.metadata ->> 'github_repo_id') AS repository_id,

        -- Provide a row_number partitioned by (org_id, codebase_name)
        -- sorted by creation time:
        ROW_NUMBER() OVER (
            PARTITION BY w.organization_id, c.codebase_name
            ORDER BY dc.created_at
        ) AS codebase_version_order

    FROM derived_contents dc
    JOIN codebases c
      ON c.id = dc.codebase_id
    JOIN workspaces w
      ON w.id = dc.workspace_id
    LEFT JOIN inspection_versions ir
      ON ir.id = dc.version_id

    WHERE dc.content_kind = 'codebase'
),
version_rows AS (
    select ocv1.*, ocv2.version_id_from_dc_codebase as primary_asset_id
    from ordered_codebase_versions ocv1
    join ordered_codebase_versions ocv2 on ocv1.org_id = ocv2.org_id
    WHERE ocv1.codebase_name = ocv2.codebase_name
    AND ocv2.codebase_version_order = 1
)
,
ins_primary_asset_raw AS (
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
        vr.primary_asset_id,      -- reuse the old derived_contents.id as PK
        vr.codebase_name,       -- display_name = codebase_name
        vr.repository_id,                    -- repository_id (if any)
        vr.org_id,
        'CODEBASE',
        vr.created_at,
        vr.updated_at
    FROM version_rows vr
        WHERE vr.codebase_version_order = 1
    RETURNING id
)
,
ins_ver AS (
    INSERT INTO v2_version
    (
        id,
        primary_asset_id,
        display_name,
        status,
        created_at,
        updated_at
    )
    SELECT
        vr.version_id_from_dc_codebase,
        vr.primary_asset_id,
        vr.version_display_name,
        'GENERATION-COMPLETE',
        vr.created_at,
        vr.updated_at
    FROM version_rows vr
)
     , deduped_nodes AS (
    SELECT
        dc.id,
        vr.version_id_from_dc_codebase,
        dc.relative_path,
        dc.created_at,
        dc.updated_at,
        dc.metadata,
        ROW_NUMBER() OVER (
            PARTITION BY vr.version_id_from_dc_codebase, dc.relative_path
            ORDER BY dc.created_at DESC
        ) AS rn,
        ROW_NUMBER() OVER (
            PARTITION BY dc.id
            ORDER BY dc.created_at DESC
        ) AS rn2
    FROM derived_contents dc
    JOIN workspaces w
      ON w.id = dc.workspace_id
    JOIN version_rows vr
      ON vr.codebase_id = dc.codebase_id
    WHERE dc.content_kind IN ('codebase-directory','codebase-file')
      AND (
        dc.version_id = vr.inspector_version_id
        OR dc.version_id = dc.codebase_id
      )
),
ins_node AS (
    INSERT INTO v2_node
    (
        id,
        version_id,
        relative_path,
        created_at,
        updated_at,
        misc_metadata
    )
    SELECT
        id,
        version_id_from_dc_codebase,
        relative_path,
        created_at,
        updated_at,
        metadata
    FROM deduped_nodes
    WHERE rn = 1 and rn2 = 1
)
,
update_derived_content AS (
    UPDATE derived_contents
    SET node_id = n.id
    FROM v2_node n
    WHERE n.id = derived_contents.source_content_id
    AND derived_contents.node_id is NULL
),
update_derived_content_top_level AS (
    UPDATE derived_contents
    SET node_id = n.id
    FROM v2_node n
    JOIN version_rows vr on vr.relative_path_dir = n.relative_path and n.version_id = vr.version_id_from_dc_codebase
    WHERE derived_contents.source_content_id = vr.version_id_from_dc_codebase
)

SELECT * FROM deduped_nodes;

"""
