#!/usr/bin/env bash

# Ensure necessary environment variables are set
: "${POSTGRES_SERVER:?Must provide POSTGRES_SERVER}"
: "${POSTGRES_PORT:?Must provide POSTGRES_PORT}"
: "${POSTGRES_DB:?Must provide POSTGRES_DB}"
: "${POSTGRES_USER:?Must provide POSTGRES_USER}"
: "${POSTGRES_PASSWORD:?Must provide POSTGRES_PASSWORD}"

# For psql to use the password non-interactively
export PGPASSWORD="$POSTGRES_PASSWORD"

DBHOST="$POSTGRES_SERVER"
DBPORT="$POSTGRES_PORT"
DBNAME="$POSTGRES_DB"
DBUSER="$POSTGRES_USER"

# Compute the new lists value (floor of sqrt of the row count)
lists=$(psql -h "$DBHOST" -p "$DBPORT" -U "$DBUSER" -d "$DBNAME" -X -t -A -c "SELECT floor(sqrt(count(*)::float))::int FROM chunkandembedding;")
if [ -z "$lists" ]; then
  echo "Failed to compute lists value."
  exit 1
fi

# Compute the new probes value (floor of sqrt(lists))
probes=$(psql -h "$DBHOST" -p "$DBPORT" -U "$DBUSER" -d "$DBNAME" -X -t -A -c "SELECT floor(sqrt($lists::float))::int;")
if [ -z "$probes" ]; then
  echo "Failed to compute probes value."
  exit 1
fi

echo "Computed lists: $lists"
echo "Computed probes: $probes"

# Drop the existing index
psql -h "$DBHOST" -p "$DBPORT" -U "$DBUSER" -d "$DBNAME" -X -c "DROP INDEX IF EXISTS ix_chunk_text_embedding_3_small_vector_l2_ops;" || exit 1

# Create the index with the new lists value
psql -h "$DBHOST" -p "$DBPORT" -U "$DBUSER" -d "$DBNAME" -X -c "CREATE INDEX ix_chunk_text_embedding_3_small_vector_l2_ops ON chunkandembedding USING ivfflat (text_embedding_3_small vector_l2_ops) WITH (lists = $lists);" || exit 1

# Set the probes value
psql -h "$DBHOST" -p "$DBPORT" -U "$DBUSER" -d "$DBNAME" -X -c "SET ivfflat.probes = $probes;" || exit 1

echo "Index recreated successfully."
