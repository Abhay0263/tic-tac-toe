#!/bin/sh
set -e

echo "Waiting for MySQL..."
until nc -z db2 3306; do
  sleep 2
done

echo "MySQL is up - starting backend"
exec python app.py
