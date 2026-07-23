import os

# APP_ENV=production la setea el servicio de Render (u otro deploy real). Sin
# ella, todo corre en modo desarrollo: local con `python app.py`/`flask run`,
# tests, y el launcher local (que ya genera su propio SECRET_KEY al azar).
IS_PRODUCTION = os.environ.get('APP_ENV') == 'production'

# Base de datos: Postgres siempre (ver RODO.txt, "Migrar de SQLite a Render
# Postgres"). En producción no hay fallback: Render inyecta DATABASE_URL al
# conectar el servicio de Postgres, y si falta el arranque explota en vez de
# correr contra una base que no existe. En desarrollo cae al contenedor local
# (ver RODO.txt para el comando de Docker).
if IS_PRODUCTION:
    DATABASE_URL = os.environ['DATABASE_URL']
else:
    DATABASE_URL = os.environ.get(
        'DATABASE_URL', 'postgresql://panacar:panacar_dev_local@127.0.0.1:5432/panacar'
    )

# Configuración de Flask
# En producción no hay fallback: si falta SECRET_KEY, el arranque explota en
# vez de correr silenciosamente con una clave de desarrollo conocida.
if IS_PRODUCTION:
    SECRET_KEY = os.environ['SECRET_KEY']
else:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-panacar-secret-key')
