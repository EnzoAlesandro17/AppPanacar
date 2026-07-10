from flask import Blueprint, render_template

from src.auth import login_required, requiere_ver_bitacora, restringir_a_administracion
from src.breadcrumbs import migas
from src.modules.administrar.bitacora.logic import listar_eventos

bitacora_bp = Blueprint("bitacora", __name__, url_prefix="/bitacora")
bitacora_bp.before_request(restringir_a_administracion)


@bitacora_bp.route("/")
@login_required
@requiere_ver_bitacora
def index():
    eventos = listar_eventos()
    return render_template(
        "bitacora/listar.html",
        eventos=eventos,
        migas=migas(
            ("Sistema de gestión", "administrar.index"),
            ("Administración", "administracion.index"),
            "Bitácora",
        ),
    )
