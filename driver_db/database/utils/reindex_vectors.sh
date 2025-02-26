
echo "You have entered the following details:"
echo "User: $POSTGRES_USER"
echo "Database: $POSTGRES_DB"
echo "Server: $POSTGRES_SERVER"
read -p "Are these details correct? (y/n): " confirmation

if [ "$confirmation" != "y" ]; then
    echo "Please run the script again and enter the correct details."
    exit 1
fi
start_time=$(date +%s)

psql -U $POSTGRES_USER -d $POSTGRES_DB -h $POSTGRES_SERVER -W $POSTGRES_PASSWORD -f reindex_vectors.sql

end_time=$(date +%s)
elapsed_time=$((end_time - start_time))

echo "Reindexing took $elapsed_time seconds."
