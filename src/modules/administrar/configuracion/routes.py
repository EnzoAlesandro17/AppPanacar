from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from src.auth import login_required
from src.breadcrumbs import migas
from src.exceptions import ValidationError
from src.modules.administrar.user.logic import TEMAS, actualizar_tema

configuracion_bp = Blueprint("configuracion", __name__, url_prefix="/configuracion")


@configuracion_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        theme = request.form.get("theme", "").strip()
        try:
            actualizar_tema(session["user_id"], theme)
        except ValidationError as error:
            flash(str(error), "error")
            return redirect(url_for("configuracion.index"))
        session["theme"] = theme
        flash("Tema actualizado.", "success")
        return redirect(url_for("configuracion.index"))

    return render_template(
        "configuracion/index.html",
        temas=TEMAS,
        migas=migas(("Sistema de gestión", "administrar.index"), "Configuración"),
    )
