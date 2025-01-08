MIGRATE_PDFS = """
--------------------------------------------------------------------------------
-- 1) pdfs CTE: gather all rows where content_kind = 'supplemental-document'
--    We keep old_id = dc.id, plus a ROW_NUMBER() so each row becomes a separate
--    version. Also generate a "row_key" to identify each row uniquely.
--------------------------------------------------------------------------------
WITH pdfs AS (
    SELECT
        dc.id                       AS old_id,
        w.organization_id           AS org_id,
        dc.content_name,
        dc.relative_path,
        dc.created_at,
        dc.updated_at,
        dc.content_kind,

        ROW_NUMBER() OVER (
            PARTITION BY w.organization_id, dc.content_name
            ORDER BY dc.created_at
        ) AS version_num,

        -- Build a row key combining (org_id + content_name + old_id).
        -- This ensures we can do bridging in subsequent CTEs.
        CONCAT(
            w.organization_id::text, '||',
            dc.content_name, '||',
            dc.id::text
        ) AS row_key
    FROM derived_contents dc
    JOIN workspaces w ON w.id = dc.workspace_id
    WHERE dc.content_kind = 'supplemental-document'
      AND dc.content_name IS NOT NULL
),

--------------------------------------------------------------------------------
-- 2) distinct_pdfs: pick exactly one row from each (org_id, content_name)
--    group to become the "chosen_id" for the new v2_primary_asset.
--------------------------------------------------------------------------------
distinct_pdfs AS (
    SELECT DISTINCT ON (p.org_id, p.content_name)
        p.org_id,
        p.content_name,
        p.created_at,
        p.updated_at,
        p.content_kind,
        p.old_id AS chosen_id
    FROM pdfs p
    ORDER BY p.org_id, p.content_name, p.created_at
),

--------------------------------------------------------------------------------
-- 3) Insert one row per group into v2_primary_asset, reusing the chosen_id.
--------------------------------------------------------------------------------
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
        dp.chosen_id,       -- reuse old derived_contents.id for the asset PK
        dp.content_name,    -- or any naming for display_name
        NULL,
        dp.org_id,
        'FILE',
        dp.created_at,
        dp.updated_at
    FROM distinct_pdfs dp

    -- Return only columns from v2_primary_asset itself.
    RETURNING id
),

--------------------------------------------------------------------------------
-- 4) Bridge: link v2_primary_asset.id back to distinct_pdfs
--    so we know for each (org_id, content_name) which was chosen.
--------------------------------------------------------------------------------
primary_asset_bridge AS (
    SELECT
        pa.id         AS primary_asset_id,
        dp.org_id,
        dp.content_name
    FROM ins_primary_asset_raw pa
    -- Rejoin distinct_pdfs by matching the same id
    JOIN distinct_pdfs dp ON dp.chosen_id = pa.id
),

--------------------------------------------------------------------------------
-- 5) Insert all versions. We can't reference p.* in RETURNING directly,
--    so we only RETURN columns from v2_version. Then we do another bridging step.
--------------------------------------------------------------------------------
ins_version_raw AS (
    INSERT INTO v2_version (
        id,
        primary_asset_id,
        display_name,
        created_at,
        updated_at,
        status
    )
    SELECT
        p.old_id,  -- or use uuid_generate_v4() if you prefer new IDs
        pab.primary_asset_id,
        'v' || p.version_num::text,  -- e.g. "v1", "v2", ...
        p.created_at,
        p.updated_at,
        'GENERATION_COMPLETE'
    FROM pdfs p
    JOIN primary_asset_bridge pab
      ON p.org_id       = pab.org_id
     AND p.content_name = pab.content_name

    -- We only return columns from v2_version (the newly inserted table):
    RETURNING id
),

--------------------------------------------------------------------------------
-- 6) version_bridge: rejoin the newly inserted versions with the original pdfs,
--    so we can get each row's old_id, relative_path, timestamps, etc.
--    We rely on a row_key or something that can tie them back.
--------------------------------------------------------------------------------
version_bridge AS (
    SELECT
        v.id                      AS version_id,
        p.old_id,
        p.relative_path,
        p.created_at,
        p.updated_at,
        p.row_key
    FROM ins_version_raw v
    JOIN pdfs p
      ON p.old_id::text = v.id::text
      -- Because we used p.old_id = v.id in ins_version_raw
),

--------------------------------------------------------------------------------
-- 7) Insert a node for each version. We can reuse version_id for node.id or
--    generate a fresh one. We'll do "reuse version_id" in this example.
--------------------------------------------------------------------------------
ins_node_raw AS (
    INSERT INTO v2_node (
        id,
        version_id,
        kind,
        relative_path,
        created_at,
        updated_at
    )
    SELECT
        vb.version_id,   -- node.id = version_id for 1:1
        vb.version_id,   -- version_id
        'OTHER' AS kind, -- node kind is other
        vb.relative_path,
        vb.created_at,
        vb.updated_at
    FROM version_bridge vb
    RETURNING id
),

--------------------------------------------------------------------------------
-- 8) node_bridge: link the newly inserted nodes back to pdfs row info
--------------------------------------------------------------------------------
node_bridge AS (
    SELECT
        n.id AS node_id,
        vb.old_id
    FROM ins_node_raw n
    JOIN version_bridge vb
      ON n.id = vb.version_id
),

--------------------------------------------------------------------------------
-- 9) Finally, update derived_contents.node_id
--------------------------------------------------------------------------------
ins_update AS (
    UPDATE derived_contents d
    SET node_id = nb.node_id
    FROM node_bridge nb
    WHERE d.id = nb.old_id
    RETURNING d.*
)

SELECT * FROM ins_update;

"""
