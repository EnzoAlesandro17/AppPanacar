from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from src.auth import login_required
from src.exceptions import ValidationError
from src.modules.administrar.branches.logic import listar_sucursales
from src.modules.administrar.user.logic import (
    ROLES,
    actualizar_usuario,
    borrar_usuario,
    crear_usuario,
    iniciar_sesion,
    listar_usuarios,
    obtener_por_id,
    reactivar_usuario,
)
from src.permissions import puede_gestionar_usuarios

user_bp = Blueprint("user", __name__, url_prefix="/user")


def _requiere_gestion_usuarios():
    """None si el usuario en sesión puede gestionar usuarios; si no, un redirect listo para devolver."""
    if not puede_gestionar_usuarios(session.get("role")):
        flash("No tenés permiso para gestionar usuarios.", "error")
        return redirect(url_for("administrar.index"))
    return None


def _datos_del_form():
    branch_id = request.form.get("branch_id", "").strip()
    return {
        "name": request.form.get("name", "").strip(),
        "last_name": request.form.get("last_name", "").strip(),
        "dni": request.form.get("dni", "").strip(),
        "code": request.form.get("code", "").strip() or None,
        "username": request.form.get("username", "").strip() or None,
        "email": request.form.get("email", "").strip() or None,
        "birth_date": request.form.get("birth_date", "").strip() or None,
        "phone": request.form.get("phone", "").strip() or None,
        "role": request.form.get("role", "").strip(),
        "branch_id": int(branch_id) if branch_id else None,
    }


@user_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        try:
            usuario = iniciar_sesion(username, password)
        except ValidationError as error:
            flash(str(error), "error")
            return redirect(url_for("user.login"))

        session["user_id"] = usuario["id"]
        session["name"] = f"{usuario['name']} {usuario['last_name']}"
        session["role"] = usuario["role"]
        return redirect(url_for("administrar.index"))

    return render_template("user/login.html")


@user_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("user.login"))


@user_bp.route("/")
@login_required
def listar():
    usuarios = listar_usuarios()
    return render_template("user/listar.html", usuarios=usuarios)


@user_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    redireccion = _requiere_gestion_usuarios()
    if redireccion:
        return redireccion

    sucursales = listar_sucursales()

    if request.method == "POST":
        datos = _datos_del_form()
        password = request.form.get("password", "").strip() or None
        try:
            crear_usuario(password=password, **datos)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "user/formulario.html", usuario=datos, accion="nueva", roles=ROLES, sucursales=sucursales
            )
        flash("Usuario creado.", "success")
        return redirect(url_for("user.listar"))

    return render_template(
        "user/formulario.html", usuario=None, accion="nueva", roles=ROLES, sucursales=sucursales
    )


@user_bp.route("/<int:id_usuario>/editar", methods=["GET", "POST"])
@login_required
def editar(id_usuario):
    redireccion = _requiere_gestion_usuarios()
    if redireccion:
        return redireccion

    usuario = obtener_por_id(id_usuario)
    if usuario is None:
        flash("El usuario no existe.", "error")
        return redirect(url_for("user.listar"))

    sucursales = listar_sucursales()

    if request.method == "POST":
        datos = _datos_del_form()
        password = request.form.get("password", "").strip() or None
        quitar_branch_id = not request.form.get("branch_id", "").strip()
        try:
            actualizar_usuario(id_usuario, password=password, quitar_branch_id=quitar_branch_id, **datos)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "user/formulario.html",
                usuario={**datos, "id": id_usuario},
                accion="editar",
                roles=ROLES,
                sucursales=sucursales,
            )
        flash("Usuario actualizado.", "success")
        return redirect(url_for("user.listar"))

    return render_template(
        "user/formulario.html", usuario=dict(usuario), accion="editar", roles=ROLES, sucursales=sucursales
    )


@user_bp.route("/<int:id_usuario>/borrar", methods=["POST"])
@login_required
def borrar(id_usuario):
    redireccion = _requiere_gestion_usuarios()
    if redireccion:
        return redireccion

    if obtener_por_id(id_usuario) is None:
        flash("El usuario no existe.", "error")
        return redirect(url_for("user.listar"))

    if id_usuario == session.get("user_id"):
        flash("No podés borrar tu propio usuario.", "error")
        return redirect(url_for("user.listar"))

    borrar_usuario(id_usuario)
    flash("Usuario borrado.", "success")
    return redirect(url_for("user.listar"))


@user_bp.route("/borrados")
@login_required
def borrados():
    redireccion = _requiere_gestion_usuarios()
    if redireccion:
        return redireccion

    usuarios = [u for u in listar_usuarios(incluir_borrados=True) if u["status"] == 0]
    return render_template("user/borrados.html", usuarios=usuarios)


@user_bp.route("/<int:id_usuario>/reactivar", methods=["POST"])
@login_required
def reactivar(id_usuario):
    redireccion = _requiere_gestion_usuarios()
    if redireccion:
        return redireccion

    if obtener_por_id(id_usuario) is None:
        flash("El usuario no existe.", "error")
        return redirect(url_for("user.borrados"))

    reactivar_usuario(id_usuario)
    flash("Usuario reactivado.", "success")
    return redirect(url_for("user.borrados"))
