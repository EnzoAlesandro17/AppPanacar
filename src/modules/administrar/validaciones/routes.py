from flask import Blueprint, render_template

from src.auth import login_required

validaciones_bp = Blueprint("validaciones", __name__, url_prefix="/validaciones")


@validaciones_bp.route("/")
@login_required
def index():
    return render_template("validaciones/index.html")
