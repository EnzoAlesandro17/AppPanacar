from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from src.auth import login_required, requiere_ver_eliminados, restringir_a_administracion
from src.breadcrumbs import migas
from src.exceptions import RegistroBorradoExistente, ValidationError
from src.modules.administrar.branches.logic import (
    actualizar_sucursal,
    borrar_sucursal,
    crear_sucursal,
    listar_sucursales,
    obtener_por_id,
    reactivar_sucursal,
    reordenar_sucursales,
)
from src.permissions import puede_ver_eliminados

branches_bp = Blueprint("branches", __name__, url_prefix="/sucursales")
branches_bp.before_request(restringir_a_administracion)


def _migas(*ultimos):
    piezas = [("Sistema de gestión", "administrar.index"), ("Administración", "administracion.index")]
    piezas.append(("Sucursales", "branches.listar") if ultimos else "Sucursales")
    piezas.extend(ultimos)
    return migas(*piezas)


def _datos_del_form():
    return {
        "name": request.form.get("name", "").strip(),
        "code": request.form.get("code", "").strip() or None,
        "country": request.form.get("country", "").strip() or None,
        "city": request.form.get("city", "").strip() or None,
        "address": request.form.get("address", "").strip() or None,
        "email": request.form.get("email", "").strip() or None,
        "phone": request.form.get("phone", "").strip() or None,
    }


@branches_bp.route("/")
@login_required
def listar():
    sucursales = listar_sucursales()
    return render_template("branches/listar.html", sucursales=sucursales, migas=_migas())


@branches_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    if request.method == "POST":
        datos = _datos_del_form()
        try:
            crear_sucursal(**datos)
        except RegistroBorradoExistente as error:
            flash(
                "Ya existe una sucursal borrada con ese code. Podés reactivarla en vez de crear una nueva.",
                "error",
            )
            return render_template(
                "branches/formulario.html", sucursal=datos, accion="nueva",
                borrado_existente_id=error.id_existente, migas=_migas("Nueva sucursal")
            )
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "branches/formulario.html", sucursal=datos, accion="nueva", migas=_migas("Nueva sucursal")
            )
        flash("Sucursal creada.", "success")
        return redirect(url_for("branches.listar"))

    return render_template(
        "branches/formulario.html", sucursal=None, accion="nueva", migas=_migas("Nueva sucursal")
    )


@branches_bp.route("/<int:id_sucursal>/editar", methods=["GET", "POST"])
@login_required
def editar(id_sucursal):
    sucursal = obtener_por_id(id_sucursal)
    if sucursal is None:
        flash("La sucursal no existe.", "error")
        return redirect(url_for("branches.listar"))

    if request.method == "POST":
        datos = _datos_del_form()
        try:
            actualizar_sucursal(id_sucursal, **datos)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "branches/formulario.html", sucursal={**datos, "id": id_sucursal}, accion="editar",
                migas=_migas("Editar sucursal"),
            )
        flash("Sucursal actualizada.", "success")
        return redirect(url_for("branches.listar"))

    return render_template(
        "branches/formulario.html", sucursal=dict(sucursal), accion="editar",
        migas=_migas("Editar sucursal"),
    )


@branches_bp.route("/<int:id_sucursal>/borrar", methods=["POST"])
@login_required
def borrar(id_sucursal):
    if obtener_por_id(id_sucursal) is None:
        flash("La sucursal no existe.", "error")
        return redirect(url_for("branches.listar"))

    borrar_sucursal(id_sucursal)
    flash("Sucursal borrada.", "success")
    return redirect(url_for("branches.listar"))


@branches_bp.route("/borrados")
@login_required
@requiere_ver_eliminados
def borrados():
    sucursales = [s for s in listar_sucursales(incluir_borrados=True) if s["status"] == 0]
    return render_template("branches/borrados.html", sucursales=sucursales, migas=_migas("Borrados"))


@branches_bp.route("/<int:id_sucursal>/reactivar", methods=["POST"])
@login_required
def reactivar(id_sucursal):
    destino = "branches.borrados" if puede_ver_eliminados(session.get("role")) else "branches.listar"

    if obtener_por_id(id_sucursal) is None:
        flash("La sucursal no existe.", "error")
        return redirect(url_for(destino))

    reactivar_sucursal(id_sucursal)
    flash("Sucursal reactivada.", "success")
    return redirect(url_for(destino))


@branches_bp.route("/reordenar", methods=["POST"])
@login_required
def reordenar():
    datos = request.get_json(silent=True) or {}
    reordenar_sucursales(datos.get("orden", []))
    return "", 204
