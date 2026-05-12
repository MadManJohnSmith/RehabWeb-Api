#!/bin/sh
set -e

HOST="${MYSQL_HOST:-db}"
PORT="${MYSQL_PORT:-3306}"

echo "Esperando a MySQL en ${HOST}:${PORT}..."

python - <<PYEOF
import socket, sys, time, os
host = os.environ.get("MYSQL_HOST", "db")
port = int(os.environ.get("MYSQL_PORT", "3306"))
for attempt in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"MySQL TCP OK en {host}:{port} (intento {attempt + 1})")
            sys.exit(0)
    except OSError:
        time.sleep(2)
print("Timeout esperando a MySQL", file=sys.stderr)
sys.exit(1)
PYEOF

echo "Aplicando migraciones de Django..."
python manage.py migrate --noinput

echo "Iniciando Django runserver en 0.0.0.0:8000"
exec python manage.py runserver 0.0.0.0:8000
