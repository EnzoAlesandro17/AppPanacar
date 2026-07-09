from flask import Flask
from flask_wtf import CSRFProtect

from src.cli import registrar_comandos
from src.config import SECRET_KEY
from src.constants.settings import Settings
from src.constants.validations import formatear_fecha_visual
from src.modules.administrar.administracion.routes import administracion_bp
from src.modules.administrar.branches.db import crear_tabla as crear_tabla_branches
from src.modules.administrar.branches.routes import branches_bp
from src.modules.administrar.clients.db import crear_tabla as crear_tabla_clients
from src.modules.administrar.clients.routes import clients_bp
from src.modules.administrar.configuracion.routes import configuracion_bp
from src.modules.administrar.contabilidad.routes import contabilidad_bp
from src.modules.administrar.employees.db import crear_tabla as crear_tabla_employees
from src.modules.administrar.employees.routes import employees_bp
from src.modules.administrar.informacion_util.db import crear_tabla as crear_tabla_useful_links
from src.modules.administrar.informacion_util.routes import informacion_util_bp
from src.modules.administrar.preguntas_frecuentes.routes import preguntas_frecuentes_bp
from src.modules.administrar.products.db import crear_tabla as crear_tabla_products
from src.modules.administrar.products.db import crear_tabla_compatibilidad
from src.modules.administrar.products.routes import products_bp
from src.modules.administrar.routes import administrar_bp
from src.modules.administrar.siniestros.routes import siniestros_bp
from src.modules.administrar.user.db import crear_tabla as crear_tabla_users
from src.modules.administrar.user.routes import user_bp
from src.modules.administrar.validaciones.claim_statuses.db import crear_tabla as crear_tabla_claim_statuses
from src.modules.administrar.validaciones.claim_statuses.routes import claim_statuses_bp
from src.modules.administrar.validaciones.insurance_companies.db import (
    crear_tabla as crear_tabla_insurance_companies,
)
from src.modules.administrar.validaciones.insurance_companies.routes import insurance_companies_bp
from src.modules.administrar.validaciones.routes import validaciones_bp
from src.modules.administrar.validaciones.vehicle_brands.db import crear_tabla as crear_tabla_vehicle_brands
from src.modules.administrar.validaciones.vehicle_brands.routes import vehicle_brands_bp
from src.modules.administrar.vehicles.db import crear_tabla as crear_tabla_vehicles
from src.modules.administrar.vehicles.routes import vehicles_bp


def _inicializar_tablas():
    # Orden importa: clients y products/compatibilidad tienen FK a estos catálogos;
    # vehicles tiene FK a vehicle_brands; users tiene FK a employees (y employees
    # tiene que existir antes, la migración de datos personales viejos de users
    # inserta filas ahí al arrancar).
    crear_tabla_vehicle_brands()
    crear_tabla_insurance_companies()
    crear_tabla_claim_statuses()
    crear_tabla_branches()
    crear_tabla_clients()
    crear_tabla_products()
    crear_tabla_compatibilidad()
    crear_tabla_vehicles()
    crear_tabla_employees()
    crear_tabla_users()
    crear_tabla_useful_links()


def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    CSRFProtect(app)

    @app.context_processor
    def inyectar_app_name():
        return {"app_name": Settings.APP_NAME, "app_version": Settings.VERSION}

    app.jinja_env.filters["fecha_visual"] = formatear_fecha_visual

    _inicializar_tablas()
    registrar_comandos(app)

    app.register_blueprint(administrar_bp)
    app.register_blueprint(administracion_bp)
    app.register_blueprint(branches_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(validaciones_bp)
    app.register_blueprint(vehicle_brands_bp)
    app.register_blueprint(insurance_companies_bp)
    app.register_blueprint(claim_statuses_bp)
    app.register_blueprint(vehicles_bp)
    app.register_blueprint(siniestros_bp)
    app.register_blueprint(configuracion_bp)
    app.register_blueprint(contabilidad_bp)
    app.register_blueprint(informacion_util_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(preguntas_frecuentes_bp)

    return app
