
## Files
- **[reindex_vectors.sh](utils/reindex_vectors.sh.driver.md)**: The `reindex_vectors.sh` file is a shell script that prompts the user for PostgreSQL connection details and executes a SQL script to reindex vectors in the specified database, while also timing the operation.
- **[reindex_vectors.sql](utils/reindex_vectors.sql.driver.md)**: The `reindex_vectors.sql` file contains a PL/pgSQL script that recalculates and updates the index parameters for a specific vector index in the database if the new calculated list size significantly exceeds the current one.
