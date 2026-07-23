import os

# Rutas base
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Configuración de base de datos
DB_FOLDER = 'data'
DB_NAME = 'database.db'
DB_PATH = os.path.join(BASE_DIR, DB_FOLDER, DB_NAME)

# APP_ENV=production la setea el servicio de Render (u otro deploy real). Sin
# ella, todo corre en modo desarrollo: local con `python app.py`/`flask run`,
# tests, y el launcher local (que ya genera su propio SECRET_KEY al azar).
IS_PRODUCTION = os.environ.get('APP_ENV') == 'production'

# Configuración de Flask
# En producción no hay fallback: si falta SECRET_KEY, el arranque explota en
# vez de correr silenciosamente con una clave de desarrollo conocida.
if IS_PRODUCTION:
    SECRET_KEY = os.environ['SECRET_KEY']
else:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-panacar-secret-key')