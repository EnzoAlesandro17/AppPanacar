from flask import Blueprint, render_template

from src.auth import login_required

administrar_bp = Blueprint("administrar", __name__, url_prefix="/administrar")


@administrar_bp.route("/")
@login_required
def index():
    return render_template("administrar/index.html")
