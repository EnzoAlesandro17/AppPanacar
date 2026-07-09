from flask import Blueprint, render_template

from src.auth import login_required
from src.breadcrumbs import migas

preguntas_frecuentes_bp = Blueprint("preguntas_frecuentes", __name__, url_prefix="/preguntas-frecuentes")


@preguntas_frecuentes_bp.route("/")
@login_required
def index():
    return render_template(
        "preguntas_frecuentes/index.html",
        migas=migas(
            ("Sistema de gestión", "administrar.index"),
            ("Administración", "administracion.index"),
            "Preguntas frecuentes",
        ),
    )
