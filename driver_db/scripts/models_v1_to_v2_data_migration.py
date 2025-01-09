from database.config import settings
from sqlalchemy import create_engine, text


def run_migration() -> None:
    # Create a database engine using the settings from config.py
    engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))

    # Define your SQL queries for migration
    migration_queries = [
        """
        -- Migrate CODEBASES to primary assets
        --
        INSERT INTO v2_primary_asset (id, display_name, organization_id, created_at, updated_at)
        SELECT DISTINCT ON (dc.codebase_id) dc.id, c.codebase_name, w.organization_id, c.created_at, c.updated_at
        FROM derived_contents dc
        JOIN codebases c on c.id = dc.codebase_id
        JOIN derived_content_types dct on dc.content_type_id = dct.id
        JOIN workspaces w on w.id = dc.workspace_id
        WHERE dct.type_name = 'codebase'
        AND dc.source_content_id is NULL
        ORDER BY dc.codebase_id, dc.created_at;
        """,
        """
        -- Migrate pdfs to primary assets
        --
        INSERT INTO v2_primary_asset (id, display_name, organization_id, created_at, updated_at)
        SELECT dc.id, dc.content_name, w.organization_id, dc.created_at, dc.updated_at
        FROM derived_contents dc
        JOIN derived_content_types dct on dc.content_type_id = dct.id
        JOIN workspaces w on w.id = dc.workspace_id
        WHERE dct.type_name = 'supplemental-document'
        AND dc.source_content_id is NULL;
        """,
        """
        -- Migrate PAGES to primary assets
        --
        INSERT INTO v2_primary_asset (id, display_name, organization_id, created_at, updated_at)
        SELECT dc.id,
               COALESCE(dc.content_name, dc.relative_path),
               w.organization_id,
               dc.created_at,
               dc.updated_at
        FROM derived_contents dc
        JOIN derived_content_types dct on dc.content_type_id = dct.id
        JOIN workspaces w on w.id = dc.workspace_id
        WHERE dct.type_name = 'application_note'
        AND dc.source_content_id is NULL;
        """,
        """
        -- Create new versions for v2_version
        --
        INSERT INTO v2_version (id, primary_asset_id, display_name, created_at, updated_at)
        SELECT uuid_generate_v4(), pa.id, '0.0.0', NOW(), NOW()
        FROM v2_primary_asset pa;
        """,
        """
        -- Migrate CODEBASE FOLDER and CODEBASE FILES to v2_node
        --
        INSERT INTO v2_node (id, version_id, relative_path, created_at, updated_at)
        SELECT DISTINCT dc.id, v.id, dc.relative_path, dc.created_at, dc.updated_at
        FROM derived_contents dc
        JOIN derived_content_types dc_type ON dc.content_type_id = dc_type.id
        JOIN derived_contents source ON source.codebase_id = dc.codebase_id
        JOIN derived_content_types source_type ON source.content_type_id = source_type.id
        JOIN v2_version v ON v.primary_asset_id = source.id
        WHERE source_type.type_name = 'codebase'
        AND dc_type.type_name in ('codebase-directory','codebase-file')
        """,
        """
        -- Migrate PAGES and PDFs to v2_node
        --
        INSERT INTO v2_node (id, version_id, relative_path, created_at, updated_at)
        SELECT DISTINCT dc.id, v.id, dc.relative_path, dc.created_at, dc.updated_at
        FROM derived_contents dc
        JOIN derived_content_types dc_type ON dc.content_type_id = dc_type.id
        JOIN v2_version v ON v.primary_asset_id = dc.id
        where dc_type.type_name in ('supplemental-document', 'application_note')
        """,
        """
        -- Migrate contents to v2_content
        --
        INSERT INTO v2_content (id, node_id, text, content_type, created_at, updated_at)
        SELECT dc.id, n.id, dc.content, dct.type_name, dc.created_at, dc.updated_at
        FROM derived_contents dc
        JOIN derived_content_types dct ON dc.content_type_id = dct.id
        JOIN v2_node n ON n.id = dc.source_content_id
        WHERE dc.content IS NOT NULL;
        """,
        """
        -- Migrate chunkandembeddings to v2_chunk
        --
        INSERT INTO v2_chunk (id, content_id, text, text_embedding_3_small, chunk_number, created_at, updated_at)
        SELECT ce.id, c.id, ce.text, ce.text_embedding_3_small, ce.chunk_number, ce.created_at, ce.updated_at
        FROM chunkandembedding ce
        JOIN derived_contents dc ON dc.id = ce.content_id
        JOIN v2_content c ON c.id = dc.id;
        """,
    ]

    # Execute each query within a transaction
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            for query in migration_queries:
                connection.execute(text(query))
                print(f"Successfully executed query: {query}")

            # Fetch and print top 10 rows from each v2 table
            v2_tables = [
                "v2_primary_asset",
                "v2_version",
                "v2_node",
                "v2_content",
                "v2_chunk",
            ]
            for table in v2_tables:
                result = connection.execute(text(f"SELECT * FROM {table} LIMIT 10"))
                rows = result.fetchall()
                print(f"Top 10 rows from {table}:")
                for row in rows:
                    print(row)

        except Exception as e:
            print(f"Error executing query: {query}\n{e}")
        transaction.rollback()


if __name__ == "__main__":
    run_migration()
