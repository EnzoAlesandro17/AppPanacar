from flask import Blueprint, render_template

from src.auth import login_required
from src.breadcrumbs import migas

configuracion_bp = Blueprint("configuracion", __name__, url_prefix="/configuracion")


@configuracion_bp.route("/")
@login_required
def index():
    return render_template(
        "configuracion/index.html",
        migas=migas(("Sistema de gestión", "administrar.index"), "Configuración"),
    )
