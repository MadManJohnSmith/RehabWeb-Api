# RehabWeb-Api — Django 6 + DRF + MySQL
# Imagen para desarrollo: corre `manage.py runserver` con auto-reload.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dependencias del sistema para compilar `mysqlclient` y utilidades varias.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        build-essential \
        pkg-config \
        default-libmysqlclient-dev \
        default-mysql-client \
        curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias Python primero para aprovechar la cache de Docker.
COPY requirements.txt ./
RUN pip install -r requirements.txt

# El código se monta como volumen en dev (ver docker-compose.yml),
# así que esta copia solo aplica si se construye la imagen "standalone".
COPY . .

EXPOSE 8000

# Script de arranque: espera la DB por TCP (evita problemas de TLS entre
# MariaDB-client y MySQL 8), migra y arranca el dev server.
# Normalizamos line endings (Windows commit con CRLF rompería el shebang).
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN sed -i 's/\r$//' /usr/local/bin/docker-entrypoint.sh \
 && chmod +x /usr/local/bin/docker-entrypoint.sh

CMD ["/usr/local/bin/docker-entrypoint.sh"]
