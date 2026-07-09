from flask import Blueprint, render_template

from src.auth import login_required
from src.breadcrumbs import migas

contabilidad_bp = Blueprint("contabilidad", __name__, url_prefix="/contabilidad")


@contabilidad_bp.route("/")
@login_required
def index():
    return render_template(
        "contabilidad/index.html",
        migas=migas(
            ("Sistema de gestión", "administrar.index"),
            ("Administración", "administracion.index"),
            "Contabilidad",
        ),
    )
