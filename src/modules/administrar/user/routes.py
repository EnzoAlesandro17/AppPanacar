from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from src.auth import login_required, requiere_ver_eliminados
from src.breadcrumbs import migas
from src.exceptions import RegistroBorradoExistente, ValidationError
from src.modules.administrar.branches.logic import listar_sucursales
from src.modules.administrar.employees.logic import listar_empleados
from src.modules.administrar.employees.logic import obtener_por_id as obtener_empleado_por_id
from src.modules.administrar.user.logic import (
    ROLES,
    actualizar_usuario,
    borrar_usuario,
    crear_usuario,
    iniciar_sesion,
    listar_usuarios,
    obtener_por_id,
    obtener_sucursales_ids_usuario,
    reactivar_usuario,
    reordenar_usuarios,
    verificar_contrasena,
)
from src.permissions import puede_gestionar_usuarios, puede_ver_eliminados

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


def _branch_ids_del_form():
    return [int(valor) for valor in request.form.getlist("branch_ids") if valor.strip()]


def _datos_del_form():
    employee_id = request.form.get("employee_id", "").strip()
    return {
        "username": request.form.get("username", "").strip(),
        "role": request.form.get("role", "").strip(),
        "employee_id": int(employee_id) if employee_id else None,
        "branch_ids": _branch_ids_del_form(),
    }


def _iniciales(texto, texto2=""):
    """Dos letras para el avatar del header."""
    if texto2:
        return (texto[0] + texto2[0]).upper()
    return texto[:2].upper()


def _nombre_sesion(usuario):
    """(nombre_para_mostrar, iniciales) para guardar en la sesión al loguearse.

    Si el usuario tiene un empleado vinculado usa su nombre/apellido; si no
    (login sin empleado, ej. una cuenta técnica), usa el username."""
    if usuario["employee_id"]:
        empleado = obtener_empleado_por_id(usuario["employee_id"])
        if empleado is not None:
            return f"{empleado['name']} {empleado['last_name']}", _iniciales(empleado["name"], empleado["last_name"])
    return usuario["username"], _iniciales(usuario["username"])


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

        nombre, iniciales = _nombre_sesion(usuario)
        session["user_id"] = usuario["id"]
        session["name"] = nombre
        session["iniciales"] = iniciales
        session["role"] = usuario["role"]
        session["branch_ids"] = obtener_sucursales_ids_usuario(usuario["id"])
        return redirect(url_for("administrar.index"))

    return render_template("user/login.html")


@user_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("user.login"))


@user_bp.route("/")
@login_required
def listar():
    redireccion = _requiere_gestion_usuarios()
    if redireccion:
        return redireccion

    usuarios = listar_usuarios()
    return render_template("user/listar.html", usuarios=usuarios, migas=_migas())


@user_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    redireccion = _requiere_gestion_usuarios()
    if redireccion:
        return redireccion

    empleados = listar_empleados()
    sucursales = listar_sucursales()

    if request.method == "POST":
        password = request.form.get("password", "").strip() or None
        try:
            datos = _datos_del_form()
            crear_usuario(password=password, **datos)
        except RegistroBorradoExistente as error:
            flash(
                "Ya existe un usuario borrado con ese nombre de usuario. "
                "Podés reactivarlo en vez de crear uno nuevo.",
                "error",
            )
            return render_template(
                "user/formulario.html", usuario=dict(request.form), accion="nueva", roles=ROLES,
                empleados=empleados, sucursales=sucursales, sucursales_seleccionadas=_branch_ids_del_form(),
                borrado_existente_id=error.id_existente, migas=_migas("Nuevo usuario"),
            )
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "user/formulario.html", usuario=dict(request.form), accion="nueva", roles=ROLES,
                empleados=empleados, sucursales=sucursales, sucursales_seleccionadas=_branch_ids_del_form(),
                migas=_migas("Nuevo usuario"),
            )
        flash("Usuario creado.", "success")
        return redirect(url_for("user.listar"))

    return render_template(
        "user/formulario.html", usuario=None, accion="nueva", roles=ROLES, empleados=empleados,
        sucursales=sucursales, sucursales_seleccionadas=[], migas=_migas("Nuevo usuario"),
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

    empleados = listar_empleados()
    sucursales = listar_sucursales()

    if request.method == "POST":
        password = request.form.get("password", "").strip() or None
        quitar_employee_id = not request.form.get("employee_id", "").strip()
        try:
            datos = _datos_del_form()
            actualizar_usuario(id_usuario, password=password, quitar_employee_id=quitar_employee_id, **datos)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "user/formulario.html",
                usuario={**dict(request.form), "id": id_usuario},
                accion="editar",
                roles=ROLES,
                empleados=empleados,
                sucursales=sucursales,
                sucursales_seleccionadas=_branch_ids_del_form(),
                migas=_migas("Editar usuario"),
            )
        flash("Usuario actualizado.", "success")
        return redirect(url_for("user.listar"))

    return render_template(
        "user/formulario.html", usuario=dict(usuario), accion="editar", roles=ROLES, empleados=empleados,
        sucursales=sucursales, sucursales_seleccionadas=obtener_sucursales_ids_usuario(id_usuario),
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
@requiere_ver_eliminados
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

    destino = "user.borrados" if puede_ver_eliminados(session.get("role")) else "user.listar"

    if obtener_por_id(id_usuario) is None:
        flash("El usuario no existe.", "error")
        return redirect(url_for(destino))

    reactivar_usuario(id_usuario)
    flash("Usuario reactivado.", "success")
    return redirect(url_for(destino))


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
    """Autogestión: solo usuario y contraseña. Los datos personales viven en
    Empleados (Administración), no acá — la separación es a propósito."""
    usuario = obtener_por_id(session["user_id"])
    if usuario is None:
        flash("Tu usuario no existe.", "error")
        return redirect(url_for("user.logout"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password_nueva = request.form.get("password", "").strip() or None
        password_actual = request.form.get("password_actual", "").strip() or None
        try:
            if password_nueva:
                if not password_actual or not verificar_contrasena(usuario["username"], password_actual):
                    raise ValidationError("La contraseña actual no es correcta.")
            actualizar_usuario(session["user_id"], username=username, password=password_nueva)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "user/perfil.html",
                usuario={**dict(request.form), "id": session["user_id"]},
                migas=migas(("Sistema de gestión", "administrar.index"), "Mi cuenta"),
            )

        usuario_actualizado = obtener_por_id(session["user_id"])
        nombre, iniciales = _nombre_sesion(usuario_actualizado)
        session["name"] = nombre
        session["iniciales"] = iniciales
        flash("Tus datos se actualizaron.", "success")
        return redirect(url_for("user.perfil"))

    return render_template(
        "user/perfil.html",
        usuario=dict(usuario),
        migas=migas(("Sistema de gestión", "administrar.index"), "Mi cuenta"),
    )
