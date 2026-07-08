from flask import Blueprint, render_template

from src.auth import login_required
from src.breadcrumbs import migas

administrar_bp = Blueprint("administrar", __name__)


@administrar_bp.route("/")
@login_required
def index():
    return render_template("administrar/index.html", migas=migas("Sistema de gestión"))
