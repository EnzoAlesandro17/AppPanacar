from flask import Blueprint, render_template

from src.auth import login_required, restringir_a_administracion
from src.breadcrumbs import migas

validaciones_bp = Blueprint("validaciones", __name__, url_prefix="/validaciones")
validaciones_bp.before_request(restringir_a_administracion)


@validaciones_bp.route("/")
@login_required
def index():
    return render_template(
        "validaciones/index.html",
        migas=migas(
            ("Sistema de gestión", "administrar.index"),
            ("Administración", "administracion.index"),
            "Validaciones",
        ),
    )
