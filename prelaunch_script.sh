echo PGPASSWORD=$DB_TABLE_PASS createdb -h $DB_HOST -U $DB_TABLE_USER -O $DB_TABLE_USER $DB_TABLE_NAME
PGPASSWORD=$DB_TABLE_PASS createdb -h $DB_HOST -U $DB_TABLE_USER -O $DB_TABLE_USER $DB_TABLE_NAME

python3 /app/pocketAPI/manage.py migrate