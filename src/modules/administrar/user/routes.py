from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from src.auth import login_required
from src.breadcrumbs import migas
from src.constants.validations import parsear_fecha_visual
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
    reordenar_usuarios,
    verificar_contrasena,
)
from src.permissions import puede_gestionar_usuarios

user_bp = Blueprint("user", __name__, url_prefix="/usuarios")


def _migas(*ultimos):
    piezas = [
        ("Sistema de gestión", "administrar.index"),
        ("Administración", "administracion.index"),
    ]
    piezas.append(("Usuarios", "user.listar") if ultimos else "Usuarios")
    piezas.extend(ultimos)
    return migas(*piezas)


def _requiere_gestion_usuarios():
    """None si el usuario en sesión puede gestionar usuarios; si no, un redirect listo para devolver."""
    if not puede_gestionar_usuarios(session.get("role")):
        flash("No tenés permiso para gestionar usuarios.", "error")
        return redirect(url_for("administrar.index"))
    return None


def _fecha_nacimiento_del_form():
    cadena = request.form.get("birth_date", "").strip()
    return parsear_fecha_visual(cadena) if cadena else None


def _datos_del_form():
    branch_id = request.form.get("branch_id", "").strip()
    return {
        "name": request.form.get("name", "").strip(),
        "last_name": request.form.get("last_name", "").strip(),
        "dni": request.form.get("dni", "").strip(),
        "code": request.form.get("code", "").strip() or None,
        "username": request.form.get("username", "").strip() or None,
        "email": request.form.get("email", "").strip() or None,
        "birth_date": _fecha_nacimiento_del_form(),
        "phone": request.form.get("phone", "").strip() or None,
        "role": request.form.get("role", "").strip(),
        "branch_id": int(branch_id) if branch_id else None,
    }


def _datos_del_form_perfil():
    """Como _datos_del_form pero sin role/branch_id: la autogestión nunca
    puede tocar esos dos campos, solo la edición desde /usuarios (Admin/
    BackOffice). Se arma a propósito como función separada, no filtrando el
    dict de _datos_del_form, para que sea imposible colar esos campos por
    error en el futuro."""
    return {
        "name": request.form.get("name", "").strip(),
        "last_name": request.form.get("last_name", "").strip(),
        "dni": request.form.get("dni", "").strip(),
        "code": request.form.get("code", "").strip() or None,
        "username": request.form.get("username", "").strip() or None,
        "email": request.form.get("email", "").strip() or None,
        "birth_date": _fecha_nacimiento_del_form(),
        "phone": request.form.get("phone", "").strip() or None,
    }


def _iniciales(name, last_name):
    """Dos letras para el avatar del header: inicial del nombre + inicial del apellido."""
    return (name[0] + last_name[0]).upper()


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
        session["iniciales"] = _iniciales(usuario["name"], usuario["last_name"])
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
    return render_template("user/listar.html", usuarios=usuarios, migas=_migas())


@user_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    redireccion = _requiere_gestion_usuarios()
    if redireccion:
        return redireccion

    sucursales = listar_sucursales()

    if request.method == "POST":
        password = request.form.get("password", "").strip() or None
        try:
            datos = _datos_del_form()
            crear_usuario(password=password, **datos)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "user/formulario.html", usuario=dict(request.form), accion="nueva", roles=ROLES,
                sucursales=sucursales, migas=_migas("Nuevo usuario"),
            )
        flash("Usuario creado.", "success")
        return redirect(url_for("user.listar"))

    return render_template(
        "user/formulario.html", usuario=None, accion="nueva", roles=ROLES, sucursales=sucursales,
        migas=_migas("Nuevo usuario"),
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
        password = request.form.get("password", "").strip() or None
        quitar_branch_id = not request.form.get("branch_id", "").strip()
        try:
            datos = _datos_del_form()
            actualizar_usuario(id_usuario, password=password, quitar_branch_id=quitar_branch_id, **datos)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "user/formulario.html",
                usuario={**dict(request.form), "id": id_usuario},
                accion="editar",
                roles=ROLES,
                sucursales=sucursales,
                migas=_migas("Editar usuario"),
            )
        flash("Usuario actualizado.", "success")
        return redirect(url_for("user.listar"))

    return render_template(
        "user/formulario.html", usuario=dict(usuario), accion="editar", roles=ROLES, sucursales=sucursales,
        migas=_migas("Editar usuario"),
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
    return render_template("user/borrados.html", usuarios=usuarios, migas=_migas("Borrados"))


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


@user_bp.route("/reordenar", methods=["POST"])
@login_required
def reordenar():
    redireccion = _requiere_gestion_usuarios()
    if redireccion:
        return redireccion

    datos = request.get_json(silent=True) or {}
    reordenar_usuarios(datos.get("orden", []))
    return "", 204


@user_bp.route("/perfil", methods=["GET", "POST"])
@login_required
def perfil():
    """Autogestión: cualquier usuario logueado edita sus propios datos,
    sin pasar por _requiere_gestion_usuarios (a diferencia de /editar).
    Nunca recibe ni toca role/branch_id (ver _datos_del_form_perfil) para
    que nadie pueda subirse de rol editando su propia cuenta."""
    usuario = obtener_por_id(session["user_id"])
    if usuario is None:
        flash("Tu usuario no existe.", "error")
        return redirect(url_for("user.logout"))

    if request.method == "POST":
        password_nueva = request.form.get("password", "").strip() or None
        password_actual = request.form.get("password_actual", "").strip() or None
        try:
            datos = _datos_del_form_perfil()
            if password_nueva:
                if not password_actual or not verificar_contrasena(usuario["username"], password_actual):
                    raise ValidationError("La contraseña actual no es correcta.")
            actualizar_usuario(session["user_id"], password=password_nueva, **datos)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "user/formulario.html",
                usuario={**dict(request.form), "id": session["user_id"]},
                accion="perfil",
                migas=migas(("Sistema de gestión", "administrar.index"), "Mi cuenta"),
            )
        session["name"] = f"{datos['name']} {datos['last_name']}"
        session["iniciales"] = _iniciales(datos["name"], datos["last_name"])
        flash("Tus datos se actualizaron.", "success")
        return redirect(url_for("user.perfil"))

    return render_template(
        "user/formulario.html",
        usuario=dict(usuario),
        accion="perfil",
        migas=migas(("Sistema de gestión", "administrar.index"), "Mi cuenta"),
    )
