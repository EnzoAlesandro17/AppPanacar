from flask import Blueprint, render_template, session

from src.auth import login_required
from src.breadcrumbs import migas
from src.permissions import puede_acceder_administracion

administrar_bp = Blueprint("administrar", __name__)


@administrar_bp.route("/")
@login_required
def index():
    return render_template(
        "administrar/index.html",
        migas=migas("Sistema de gestión"),
        puede_administracion=puede_acceder_administracion(session.get("role")),
    )
