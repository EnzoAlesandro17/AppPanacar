from flask import Blueprint, render_template

from src.auth import login_required, restringir_a_administracion
from src.breadcrumbs import migas

administracion_bp = Blueprint("administracion", __name__, url_prefix="/administracion")
administracion_bp.before_request(restringir_a_administracion)


@administracion_bp.route("/")
@login_required
def index():
    return render_template(
        "administracion/index.html",
        migas=migas(("Sistema de gestión", "administrar.index"), "Administración"),
    )
