#!/bin/sh
set -e

echo "Waiting for MySQL at ${DB_HOST:-db2}:3306..."
until python -c "import socket, os; s = socket.create_connection((os.environ.get('DB_HOST', 'db2'), 3306), timeout=2); s.close()"; do
  sleep 2
done

echo "MySQL is up - starting backend"
exec python app.py
