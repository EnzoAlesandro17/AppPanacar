import os

# Rutas base
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Configuración de base de datos
DB_FOLDER = 'data'
DB_NAME = 'database.db'
DB_PATH = os.path.join(BASE_DIR, DB_FOLDER, DB_NAME)

# Configuración de Flask
# En producción hay que setear la variable de entorno SECRET_KEY; este valor
# fijo solo sirve para desarrollo local.
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-panacar-secret-key')