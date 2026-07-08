from flask import Blueprint, render_template

from src.auth import login_required
from src.breadcrumbs import migas

siniestros_bp = Blueprint("siniestros", __name__, url_prefix="/siniestros")


@siniestros_bp.route("/")
@login_required
def index():
    return render_template(
        "siniestros/index.html",
        migas=migas(("Sistema de gestión", "administrar.index"), "Siniestros"),
    )
