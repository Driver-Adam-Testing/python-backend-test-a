MIGRATE_TOP_LEVEL = """
BEGIN;

UPDATE derived_contents dc1
SET content_kind = 'TOP_LEVEL_TERSE_SENTENCE'
FROM derived_contents dc2
WHERE dc1.source_content_id = dc2.id
and dc2.content_kind = 'codebase'
and dc1.content_kind = 'terse_sentence_description';

UPDATE derived_contents dc1
SET content_kind = 'TOP_LEVEL_SHORT_SENTENCE'
FROM derived_contents dc2
WHERE dc1.source_content_id = dc2.id
and dc2.content_kind = 'codebase'
and dc1.content_kind = 'short_sentence_description';

UPDATE derived_contents dc1
SET content_kind = 'TOP_LEVEL_SHORT_PARAGRAPH'
FROM derived_contents dc2
WHERE dc1.source_content_id = dc2.id
and dc2.content_kind = 'codebase'
and dc1.content_kind = 'short_paragraph_description';

UPDATE derived_contents dc1
SET content_kind = 'TOP_LEVEL_LONG_DESCRIPTION'
FROM derived_contents dc2
WHERE dc1.source_content_id = dc2.id
and dc2.content_kind = 'codebase'
and dc1.content_kind = 'long_description';

COMMIT;
"""
