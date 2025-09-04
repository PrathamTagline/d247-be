#!/bin/sh
set -e

echo "Waiting for Postgres..."

until python -c "import psycopg2; psycopg2.connect(host='d247-db', port=5432, user='postgres', password='postgres', dbname='d247')" >/dev/null 2>&1; do
  sleep 2
done

echo "Postgres is ready"

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"

