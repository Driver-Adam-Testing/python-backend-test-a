MIGRATE_CODEBASE = """
BEGIN;

------------------------------------------------------------------------------
-- 1) Prepare and Insert Primary Assets & Versions
------------------------------------------------------------------------------
CREATE TEMP TABLE version_rows AS
SELECT * FROM (
    SELECT
        CASE
            WHEN dc.version_id IS NOT NULL THEN dc.version_id
            ELSE dc.id
        END AS version_id_resolved,
        -- version_id_from_dc_codebase is an inaccurate name; version id is version_id_resolved
        dc.id                   AS version_id_from_dc_codebase,
        w.organization_id       AS org_id,
        c.codebase_name,
        c.id                    AS codebase_id,
        dc.created_at,
        dc.updated_at,

        CASE
            WHEN dc.relative_path IS NOT NULL
                 AND RIGHT(dc.relative_path, 1) <> '/'
            THEN dc.relative_path || '/'
            ELSE dc.relative_path
        END AS relative_path_dir,

        ir.id AS inspector_version_id,
        CASE
            WHEN ir.display_name = 'Unversioned'
            THEN ir.display_name || ROW_NUMBER() OVER (
                PARTITION BY w.organization_id, c.codebase_name
                ORDER BY dc.created_at
            )
            WHEN ir.display_name IS NOT NULL
            THEN ir.display_name
            ELSE '0.0.' || ROW_NUMBER() OVER (
                PARTITION BY w.organization_id, c.codebase_name
                ORDER BY dc.created_at
            )
        END AS version_display_name,

        (dc.metadata ->> 'github_repo_id') AS repository_id,

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
) AS temp;
CREATE TEMP TABLE version_rows_marked AS
SELECT * FROM  (
    SELECT
        ocv1.*,
        -- We use the first version's ID as the "primary asset" ID
        ocv2.version_id_resolved AS primary_asset_id
    FROM version_rows ocv1
    JOIN version_rows ocv2
      ON ocv1.org_id = ocv2.org_id
     AND ocv1.codebase_name = ocv2.codebase_name
    WHERE ocv2.codebase_version_order = 1
) AS temp2;
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
    vr.primary_asset_id,
    vr.codebase_name,
    vr.repository_id,
    vr.org_id,
    'CODEBASE',
    vr.created_at,
    vr.updated_at
FROM version_rows_marked vr
WHERE vr.codebase_version_order = 1
RETURNING id;

INSERT INTO v2_version (
    id,
    primary_asset_id,
    display_name,
    status,
    created_at,
    updated_at,
    previous_version_id
)
SELECT
    vr.version_id_resolved,
    vr.primary_asset_id,
    vr.version_display_name,
    'GENERATION-COMPLETE',
    vr.created_at,
    vr.updated_at,
    vr.previous_version_id
FROM version_rows_marked vr;

------------------------------------------------------------------------------
-- 2) Insert Nodes
------------------------------------------------------------------------------
CREATE TEMP TABLE deduped_nodes AS
SELECT * FROM (
    SELECT
        dc.id,
        vr.version_id_resolved,
        dc.content_kind,
        CASE
          WHEN (dc.content_kind = 'codebase-directory' AND RIGHT(dc.relative_path, 1) <> '/')
            THEN dc.relative_path || '/'
          ELSE dc.relative_path
        END AS relative_path,
        dc.created_at,
        dc.updated_at,
        dc.metadata,
        ROW_NUMBER() OVER (
            PARTITION BY vr.version_id_resolved, dc.relative_path
            ORDER BY dc.created_at DESC
        ) AS rn,
        ROW_NUMBER() OVER (
            PARTITION BY dc.id
            ORDER BY dc.created_at DESC
        ) AS rn2
    FROM derived_contents dc
    JOIN workspaces w
      ON w.id = dc.workspace_id
    JOIN version_rows_marked vr
      ON vr.codebase_id = dc.codebase_id
    WHERE dc.content_kind IN ('codebase-directory','codebase-file')
      AND (
        dc.version_id = vr.inspector_version_id
        OR dc.version_id = dc.codebase_id
      )
) AS temp3;

INSERT INTO v2_node (
    id,
    version_id,
    kind,
    relative_path,
    created_at,
    updated_at,
    misc_metadata
)
SELECT
    id,
    version_id_resolved,
    CASE
        WHEN content_kind = 'codebase-directory' THEN 'CODEBASE_DIRECTORY'::enum_node_kind
        WHEN content_kind = 'codebase-file'      THEN 'CODEBASE_FILE'::enum_node_kind
        ELSE 'OTHER'::enum_node_kind
    END,
    relative_path,
    created_at,
    updated_at,
    metadata
FROM deduped_nodes
WHERE rn = 1
  AND rn2 = 1;

------------------------------------------------------------------------------
-- 3) Update Derived Contents - Child -> Node
------------------------------------------------------------------------------
UPDATE derived_contents
SET node_id = n.id
FROM v2_node n
WHERE (n.id = derived_contents.source_content_id
  OR n.id = derived_contents.id)
  AND derived_contents.node_id IS NULL;

------------------------------------------------------------------------------
-- 4) Update Derived Contents - Top Level -> Node
------------------------------------------------------------------------------
UPDATE derived_contents
SET node_id = n.id
FROM v2_node n
JOIN version_rows_marked vr
  ON vr.relative_path_dir = n.relative_path
 AND n.version_id = vr.version_id_resolved
WHERE derived_contents.source_content_id = vr.version_id_from_dc_codebase;

UPDATE derived_contents
SET content_kind = 'TOP_LEVEL_SHORT_SENTENCE'
FROM v2_node n
JOIN version_rows_marked vr
  ON vr.relative_path_dir = n.relative_path
 AND n.version_id = vr.version_id_from_dc_codebase
WHERE derived_contents.source_content_id = vr.version_id_from_dc_codebase
AND content_kind = 'short_sentence_description';

UPDATE derived_contents
SET content_kind = 'TOP_LEVEL_SHORT_PARAGRAPH'
FROM v2_node n
JOIN version_rows_marked vr
  ON vr.relative_path_dir = n.relative_path
 AND n.version_id = vr.version_id_from_dc_codebase
WHERE derived_contents.source_content_id = vr.version_id_from_dc_codebase
AND content_kind = 'short_paragraph_description';

UPDATE derived_contents
SET content_kind = 'TOP_LEVEL_TERSE_SENTENCE'
FROM v2_node n
JOIN version_rows_marked vr
  ON vr.relative_path_dir = n.relative_path
 AND n.version_id = vr.version_id_from_dc_codebase
WHERE derived_contents.source_content_id = vr.version_id_from_dc_codebase
AND content_kind = 'terse_sentence_description';

UPDATE derived_contents
SET content_kind = 'TOP_LEVEL_LONG_DESCRIPTION'
FROM v2_node n
JOIN version_rows_marked vr
  ON vr.relative_path_dir = n.relative_path
 AND n.version_id = vr.version_id_from_dc_codebase
WHERE derived_contents.source_content_id = vr.version_id_from_dc_codebase
AND content_kind = 'long_description';

------------------------------------------------------------------------------
-- 5) Final Select (optional)
------------------------------------------------------------------------------
SELECT *
FROM v2_node
ORDER BY created_at DESC;

COMMIT;
"""
