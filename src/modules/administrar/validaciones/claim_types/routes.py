from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from src.auth import login_required, requiere_ver_eliminados, restringir_a_administracion
from src.breadcrumbs import migas
from src.exceptions import RegistroBorradoExistente, ValidationError
from src.modules.administrar.validaciones.claim_types.logic import (
    actualizar_tipo,
    borrar_tipo,
    crear_tipo,
    listar_tipos,
    obtener_por_id,
    reactivar_tipo,
    reordenar_tipos,
)
from src.permissions import puede_ver_eliminados

claim_types_bp = Blueprint("claim_types", __name__, url_prefix="/tipos-siniestro")
claim_types_bp.before_request(restringir_a_administracion)


def _migas(*ultimos):
    piezas = [
        ("Sistema de gestión", "administrar.index"),
        ("Administración", "administracion.index"),
        ("Validaciones", "validaciones.index"),
    ]
    piezas.append(("Tipos de siniestro", "claim_types.listar") if ultimos else "Tipos de siniestro")
    piezas.extend(ultimos)
    return migas(*piezas)


@claim_types_bp.route("/")
@login_required
def listar():
    tipos = listar_tipos()
    return render_template("claim_types/listar.html", tipos=tipos, migas=_migas())


@claim_types_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        try:
            crear_tipo(name)
        except RegistroBorradoExistente as error:
            flash(
                "Ya existe un tipo borrado con ese nombre. Podés reactivarlo en vez de crear uno nuevo.",
                "error",
            )
            return render_template(
                "claim_types/formulario.html", tipo={"name": name}, accion="nueva",
                borrado_existente_id=error.id_existente, migas=_migas("Nuevo tipo"),
            )
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "claim_types/formulario.html", tipo={"name": name}, accion="nueva",
                migas=_migas("Nuevo tipo"),
            )
        flash("Tipo de siniestro creado.", "success")
        return redirect(url_for("claim_types.listar"))

    return render_template(
        "claim_types/formulario.html", tipo=None, accion="nueva", migas=_migas("Nuevo tipo"),
    )


@claim_types_bp.route("/<int:id_tipo>/editar", methods=["GET", "POST"])
@login_required
def editar(id_tipo):
    tipo = obtener_por_id(id_tipo)
    if tipo is None:
        flash("El tipo de siniestro no existe.", "error")
        return redirect(url_for("claim_types.listar"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        try:
            actualizar_tipo(id_tipo, name)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "claim_types/formulario.html", tipo={"id": id_tipo, "name": name}, accion="editar",
                migas=_migas("Editar tipo"),
            )
        flash("Tipo de siniestro actualizado.", "success")
        return redirect(url_for("claim_types.listar"))

    return render_template(
        "claim_types/formulario.html", tipo=dict(tipo), accion="editar", migas=_migas("Editar tipo"),
    )


@claim_types_bp.route("/<int:id_tipo>/borrar", methods=["POST"])
@login_required
def borrar(id_tipo):
    if obtener_por_id(id_tipo) is None:
        flash("El tipo de siniestro no existe.", "error")
        return redirect(url_for("claim_types.listar"))

    borrar_tipo(id_tipo)
    flash("Tipo de siniestro borrado.", "success")
    return redirect(url_for("claim_types.listar"))


@claim_types_bp.route("/borrados")
@login_required
@requiere_ver_eliminados
def borrados():
    tipos = [t for t in listar_tipos(incluir_borrados=True) if t["status"] == 0]
    return render_template("claim_types/borrados.html", tipos=tipos, migas=_migas("Borrados"))


@claim_types_bp.route("/<int:id_tipo>/reactivar", methods=["POST"])
@login_required
def reactivar(id_tipo):
    destino = "claim_types.borrados" if puede_ver_eliminados(session.get("role")) else "claim_types.listar"

    if obtener_por_id(id_tipo) is None:
        flash("El tipo de siniestro no existe.", "error")
        return redirect(url_for(destino))

    reactivar_tipo(id_tipo)
    flash("Tipo de siniestro reactivado.", "success")
    return redirect(url_for(destino))


@claim_types_bp.route("/reordenar", methods=["POST"])
@login_required
def reordenar():
    datos = request.get_json(silent=True) or {}
    reordenar_tipos(datos.get("orden", []))
    return "", 204
