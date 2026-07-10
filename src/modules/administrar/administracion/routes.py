from flask import Blueprint, render_template, session

from src.auth import login_required, restringir_a_administracion
from src.breadcrumbs import migas
from src.permissions import puede_ver_bitacora

administracion_bp = Blueprint("administracion", __name__, url_prefix="/administracion")
administracion_bp.before_request(restringir_a_administracion)


@administracion_bp.route("/")
@login_required
def index():
    return render_template(
        "administracion/index.html",
        puede_bitacora=puede_ver_bitacora(session.get("role")),
        migas=migas(("Sistema de gestión", "administrar.index"), "Administración"),
    )
