from datetime import timedelta

from flask import Flask, request, session
from flask_wtf import CSRFProtect

from src.cli import registrar_comandos
from src.config import SECRET_KEY
from src.constants.settings import Settings
from src.constants.validations import formatear_fecha_visual
from src.modules.administrar.administracion.routes import administracion_bp
from src.modules.administrar.bitacora.db import crear_tabla as crear_tabla_bitacora
from src.modules.administrar.bitacora.logic import registrar_evento
from src.modules.administrar.bitacora.routes import bitacora_bp
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
from src.modules.administrar.siniestros.db import crear_tabla as crear_tabla_siniestros
from src.modules.administrar.siniestros.routes import siniestros_bp
from src.modules.administrar.tasks.db import crear_tabla as crear_tabla_tasks
from src.modules.administrar.tasks.logic import contar_no_vistas
from src.modules.administrar.tasks.routes import tasks_bp
from src.modules.administrar.user.db import crear_tabla as crear_tabla_users
from src.modules.administrar.user.routes import user_bp
from src.modules.administrar.validaciones.claim_statuses.db import crear_tabla as crear_tabla_claim_statuses
from src.modules.administrar.validaciones.claim_statuses.routes import claim_statuses_bp
from src.modules.administrar.validaciones.claim_types.db import crear_tabla as crear_tabla_claim_types
from src.modules.administrar.validaciones.claim_types.routes import claim_types_bp
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
    crear_tabla_claim_types()
    crear_tabla_branches()
    crear_tabla_clients()
    crear_tabla_products()
    crear_tabla_compatibilidad()
    crear_tabla_vehicles()
    crear_tabla_employees()
    crear_tabla_users()
    crear_tabla_siniestros()
    crear_tabla_useful_links()
    crear_tabla_bitacora()
    crear_tabla_tasks()


def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    # Vencimiento de la cookie de sesión: respaldo a nivel cookie del corte por
    # día calendario que hace login_required() en src/auth.py (ese es el que
    # realmente fuerza "una sesión no sirve para otro día"; esto solo evita que
    # la cookie en sí quede viva más de un día si nunca se vuelve a pisar).
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=Settings.SESSION_LIFETIME_HOURS)
    app.config["SESSION_REFRESH_EACH_REQUEST"] = False
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    CSRFProtect(app)

    @app.context_processor
    def inyectar_app_name():
        return {"app_name": Settings.APP_NAME, "app_version": Settings.VERSION}

    @app.context_processor
    def inyectar_contador_tareas():
        if "user_id" not in session:
            return {}
        return {"tareas_sin_ver": contar_no_vistas(session["user_id"], session.get("branch_ids"))}

    app.jinja_env.filters["fecha_visual"] = formatear_fecha_visual

    _ENDPOINTS_SIN_BITACORA = {"user.login", "user.logout"}

    @app.after_request
    def _registrar_en_bitacora(response):
        """Bitácora liviana: si el request deja un flash sin consumir (recién
        seteado, antes de que la próxima página lo muestre y lo vacíe) y hay
        sesión iniciada, lo graba. login/logout se loguean aparte en sus
        propias vistas porque un login exitoso no flashea nada."""
        if "user_id" in session and request.endpoint not in _ENDPOINTS_SIN_BITACORA:
            flashes = session.get("_flashes")
            if flashes:
                categoria, mensaje = flashes[-1]
                registrar_evento(
                    user_id=session.get("user_id"),
                    username=session.get("username"),
                    ip_address=request.remote_addr,
                    method=request.method,
                    path=request.path,
                    category=categoria,
                    message=mensaje,
                )
        return response

    _inicializar_tablas()
    registrar_comandos(app)

    app.register_blueprint(administrar_bp)
    app.register_blueprint(administracion_bp)
    app.register_blueprint(bitacora_bp)
    app.register_blueprint(branches_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(validaciones_bp)
    app.register_blueprint(vehicle_brands_bp)
    app.register_blueprint(insurance_companies_bp)
    app.register_blueprint(claim_statuses_bp)
    app.register_blueprint(claim_types_bp)
    app.register_blueprint(vehicles_bp)
    app.register_blueprint(siniestros_bp)
    app.register_blueprint(configuracion_bp)
    app.register_blueprint(contabilidad_bp)
    app.register_blueprint(informacion_util_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(preguntas_frecuentes_bp)
    app.register_blueprint(tasks_bp)

    return app
