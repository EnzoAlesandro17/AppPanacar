from flask import Flask, redirect, url_for
from flask_wtf import CSRFProtect

from src.cli import registrar_comandos
from src.config import SECRET_KEY
from src.constants.settings import Settings
from src.modules.administrar.branches.db import crear_tabla as crear_tabla_branches
from src.modules.administrar.branches.routes import branches_bp
from src.modules.administrar.clients.db import crear_tabla as crear_tabla_clients
from src.modules.administrar.clients.routes import clients_bp
from src.modules.administrar.products.db import crear_tabla as crear_tabla_products
from src.modules.administrar.products.db import crear_tabla_compatibilidad
from src.modules.administrar.products.routes import products_bp
from src.modules.administrar.routes import administrar_bp
from src.modules.administrar.user.db import crear_tabla as crear_tabla_users
from src.modules.administrar.user.routes import user_bp


def _inicializar_tablas():
    # Orden importa: users tiene FK a branches.
    crear_tabla_branches()
    crear_tabla_clients()
    crear_tabla_products()
    crear_tabla_compatibilidad()
    crear_tabla_users()


def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    CSRFProtect(app)

    @app.context_processor
    def inyectar_app_name():
        return {"app_name": Settings.APP_NAME}

    _inicializar_tablas()
    registrar_comandos(app)

    app.register_blueprint(administrar_bp)
    app.register_blueprint(branches_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(user_bp)

    @app.route("/")
    def index():
        return redirect(url_for("administrar.index"))

    return app
