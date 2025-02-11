DO $$
DECLARE
    current_lists int;
    new_lists     int;
    new_probes    int;
BEGIN
    -- 1) Get the current 'lists' from the index definition
    SELECT
        (regexp_matches(pg_get_indexdef(indexrelid), 'lists *= *''([0-9]+)'''))[1]::int
    INTO current_lists
    FROM pg_index i
    JOIN pg_class c ON i.indexrelid = c.oid
    WHERE c.relname = 'ix_chunkandembedding_text_embedding_3_small_vector_l2_ops'
    LIMIT 1;

    IF current_lists IS NULL THEN
        current_lists := 0;
    END IF;

    -- 2) Compute new_lists = floor(sqrt(COUNT(*))) from the table
    SELECT floor(sqrt(count(*)))::int
    INTO new_lists
    FROM "chunkandembedding";

    -- 3) Calculate new_probes as the floor of the square root of new_lists
    new_probes := floor(sqrt(new_lists))::int;

    -- 4) Compare new_lists to current_lists
    IF new_lists > current_lists * 1.5 THEN
        SET maintenance_work_mem = '4GB';
        RAISE NOTICE 'Current lists = %, new lists = %, new_probes = %, proceeding with re-index.',
            current_lists, new_lists, new_probes;

        -- 5) Create a new index with the new 'lists' CONCURRENTLY
        EXECUTE
        'CREATE INDEX new_ix_chunkandembedding_text_embedding_3_small_vector_l2_ops
         ON "chunkandembedding"
         USING ivfflat (text_embedding_3_small vector_l2_ops)
         WITH (lists='|| new_lists || ');';

        -- 6) Drop the old index CONCURRENTLY
        EXECUTE
        'DROP INDEX IF EXISTS ix_chunkandembedding_text_embedding_3_small_vector_l2_ops;';

        -- 7) Rename the newly created index to the old name (optional)
        EXECUTE
        'ALTER INDEX new_ix_chunkandembedding_text_embedding_3_small_vector_l2_ops
         RENAME TO ix_chunkandembedding_text_embedding_3_small_vector_l2_ops;';

        -- 8) Set ivfflat.probes to new_probes
        EXECUTE
        'SET ivfflat.probes = ' || new_probes || ';';

        RAISE NOTICE 'Index rebuilt successfully.';
    ELSE
        RAISE NOTICE 'No rebuild needed. current_lists=%, new_lists=%, new_probes=%', current_lists, new_lists, new_probes;
    END IF;
END;
$$ LANGUAGE plpgsql;


