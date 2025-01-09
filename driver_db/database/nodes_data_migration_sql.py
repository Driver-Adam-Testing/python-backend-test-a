# Constants for data migration SQL scripts

# Update derived_contents with content_kind
UPDATE_content_kind_SQL = """
UPDATE derived_contents
SET content_kind = dc_type.type_name
FROM derived_content_types dc_type
WHERE derived_contents.content_type_id = dc_type.id;
"""


# CODEBASE -> PRIMARY ASSET
CODEBASE_TO_PRIMARY_ASSET_SQL = """
INSERT INTO v2_primary_asset (id, display_name, kind, organization_id, created_at, updated_at)
SELECT DISTINCT ON (c.codebase_name, w.organization_id) c.id, c.codebase_name, 'CODEBASE', w.organization_id, c.created_at, c.updated_at
FROM codebases c
JOIN workspaces w on w.id = c.workspace_id
ORDER BY c.codebase_name, w.organization_id, c.created_at;
"""

# PDF -> PRIMARY ASSET
PDF_TO_PRIMARY_ASSET_SQL = """
INSERT INTO v2_primary_asset (id, display_name, kind, organization_id, created_at, updated_at)
SELECT DISTINCT ON (dc.relative_path, w.organization_id) dc.id, dc.content_name, 'FILE', w.organization_id, dc.created_at, dc.updated_at
FROM derived_contents dc
JOIN workspaces w on w.id = dc.workspace_id
WHERE dc.content_kind = 'supplemental-document'
AND dc.source_content_id is NULL
ORDER BY dc.relative_path, w.organization_id, dc.created_at;
"""


# PAGE TEMPLATES -> PRIMARY ASSET
PAGE_TEMPLATES_TO_PRIMARY_ASSET_SQL = """
INSERT INTO v2_primary_asset (id, display_name, kind, organization_id, created_at, updated_at)
SELECT dc.id,
    CASE
        WHEN ROW_NUMBER() OVER (PARTITION BY w.organization_id, dc.content_name ORDER BY dc.created_at) > 1
        THEN dc.content_name || '-' || (ROW_NUMBER() OVER (PARTITION BY w.organization_id, dc.content_name ORDER BY dc.created_at) - 1)::text
        ELSE dc.content_name
    END AS display_name,
    'PAGE_TEMPLATE',
    w.organization_id,
    dc.created_at,
    dc.updated_at
FROM derived_contents dc
JOIN workspaces w on w.id = dc.workspace_id
WHERE dc.content_kind = 'template'
AND dc.content_name is not NULL;
"""

# CODEBASE -> VERSION
CODEBASE_TO_VERSION_SQL = """
INSERT INTO v2_version (id, primary_asset_id, display_name, created_at, updated_at, status)
SELECT c.id, pa.id,
    '0.0.' || ROW_NUMBER() OVER (PARTITION BY w.organization_id, c.codebase_name ORDER BY c.created_at ASC) - 1,
    c.created_at, c.updated_at, 'generation-complete'
FROM codebases c
JOIN workspaces w ON w.id = c.workspace_id
JOIN v2_primary_asset pa ON pa.organization_id = w.organization_id
WHERE pa.display_name = c.codebase_name;
"""


# PDF -> VERSION
PDF_TO_VERSION_SQL = """
INSERT INTO v2_version (id, primary_asset_id, display_name, created_at, updated_at, status)
SELECT dc.id, pa.id,
    '0.0.' || ROW_NUMBER() OVER (PARTITION BY w.organization_id, dc.content_name ORDER BY dc.created_at ASC) - 1,
    dc.created_at, dc.updated_at, 'GENERATION_COMPLETE'
FROM derived_contents dc
JOIN workspaces w ON w.id = dc.workspace_id
JOIN v2_primary_asset pa ON pa.organization_id = w.organization_id
WHERE dc.source_content_id IS NULL
AND dc.content_kind = 'supplemental-document'
AND pa.display_name = dc.content_name;
"""


# SOURCE CONTENT [Directories] -> NODE
DIRECTORIES_TO_NODE_SQL = """
INSERT INTO v2_node (id, version_id, relative_path, created_at, updated_at)
SELECT DISTINCT ON (dc.relative_path, v.id) dc.id, v.id,
    CASE
        WHEN RIGHT(dc.relative_path, 1) = '/' THEN dc.relative_path
        ELSE dc.relative_path || '/'
    END AS relative_path,
    dc.created_at, dc.updated_at
FROM derived_contents dc
JOIN v2_version v ON v.id = dc.codebase_id
WHERE dc.content_kind = 'codebase-directory'
"""

# SOURCE CONTENT [Files] -> NODE
FILES_TO_NODE_SQL = """
INSERT INTO v2_node (id, version_id, relative_path, created_at, updated_at)
SELECT DISTINCT ON (dc.relative_path, v.id) dc.id, v.id, dc.relative_path, dc.created_at, dc.updated_at
FROM derived_contents dc
JOIN v2_version v ON v.id = dc.codebase_id
WHERE dc.content_kind = 'codebase-file'
"""


# SOURCE CONTENT [PDF] -> NODE
PDF_TO_NODE_SQL = """
INSERT INTO v2_node (id, version_id, relative_path, created_at, updated_at)
SELECT dc.id, v.id, dc.relative_path, dc.created_at, dc.updated_at
FROM derived_contents dc
JOIN v2_version v ON v.id = dc.id
WHERE dc.content_kind = 'supplemental-document';
"""


# SOURCE CONTENT [PAGE TEMPLATES] -> NODE
PAGE_TEMPLATES_TO_NODE_SQL = """
INSERT INTO v2_node (id, version_id, relative_path, created_at, updated_at)
SELECT DISTINCT dc.id, v.id, dc.relative_path, dc.created_at, dc.updated_at
FROM derived_contents dc
JOIN v2_version v ON v.id = dc.id
WHERE dc.content_kind = 'template'
"""

# Update derived_contents with node_id for non-standard types
UPDATE_NODE_ID_NON_STANDARD_SQL = """
UPDATE derived_contents
SET node_id = n.id
FROM v2_node n
JOIN v2_version v on n.version_id = v.id
WHERE derived_contents.content_kind NOT IN ('codebase', 'codebase-directory', 'codebase-file', 'application_note', 'supplemental-document')
AND derived_contents.node_id is NULL
AND v.id = derived_contents.codebase_id
AND n.relative_path = derived_contents.relative_path;
"""

# Update derived_contents with node_id for application_note
UPDATE_NODE_ID_APPLICATION_NOTE_SQL = """
UPDATE derived_contents
SET node_id = v2_node.id
FROM v2_node
WHERE derived_contents.content_kind NOT IN ('codebase', 'codebase-directory', 'codebase-file', 'supplemental-document')
AND v2_node.id = derived_contents.id
AND derived_contents.node_id is NULL;
"""

# Update derived_contents with node_id for codebase
UPDATE_NODE_ID_CODEBASE_SQL = """
UPDATE derived_contents
SET node_id = n.id
FROM v2_node n
JOIN v2_version v on n.version_id = v.id
JOIN derived_contents sc on sc.content_kind = 'codebase'
WHERE sc.codebase_id = derived_contents.codebase_id
AND v.id = derived_contents.codebase_id
AND sc.id = derived_contents.source_content_id
AND (n.relative_path = derived_contents.relative_path OR n.relative_path = derived_contents.relative_path || '/')
AND derived_contents.node_id is NULL;
"""


# PAGES -> PRIMARY ASSET
PRIMARY_ASSET__PAGE__PAGE_TEMPLATE = """
INSERT INTO v2_primary_asset (id, display_name, kind, organization_id, created_at, updated_at)
SELECT dc.version_id,
    CASE
        WHEN ROW_NUMBER() OVER (PARTITION BY w.organization_id, dc.content_name ORDER BY dc.created_at) > 1
        THEN dc.content_name || '-' || (ROW_NUMBER() OVER (PARTITION BY w.organization_id, dc.content_name ORDER BY dc.created_at) - 1)::text
        ELSE dc.content_name
    END AS display_name,
    'PAGE',
    w.organization_id,
    dc.created_at,
    dc.updated_at
FROM derived_contents dc
JOIN workspaces w on w.id = dc.workspace_id
WHERE dct.content_kind in('application_note', 'template')
AND dc.content_name is not NULL;
"""

# PAGES -> VERSION
PAGES_TO_VERSION_SQL = """
INSERT INTO v2_version (id, primary_asset_id, display_name, created_at, updated_at, status)
SELECT dc.id, pa.id,
    '0.0.0',
    dc.created_at, dc.updated_at, 'GENERATION_COMPLETE'
FROM derived_contents dc
JOIN v2_primary_asset pa ON dc.id = pa.id
WHERE dc.content_kind = 'application_note';
"""

# SOURCE CONTENT [PAGES] -> NODE
PAGES_TO_NODE_SQL = """
INSERT INTO v2_node (id, version_id, relative_path, created_at, updated_at)
SELECT DISTINCT dc.id, v.id, dc.relative_path, dc.created_at, dc.updated_at
FROM derived_contents dc
JOIN v2_version v ON v.id = dc.id
where dc.content_kind = 'application_note'
"""
