"""Guarda el usuario logueado en la sesión de Flask (por request, no en memoria global).

Reemplaza al viejo src/session.py de la app de escritorio: ahí un usuario
por proceso tenía sentido con Tkinter, pero en un servidor web cada request
puede ser de una sucursal o persona distinta.
"""

from datetime import date
from functools import wraps

from flask import flash, redirect, session, url_for

from src.permissions import puede_acceder_administracion, puede_ver_eliminados


def login_required(vista):
    @wraps(vista)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("user.login"))

        # Corte por día calendario: aunque la cookie siga viva, una sesión
        # abierta un día anterior no sirve para hoy. Fuerza login de nuevo
        # al menos una vez por día, sin importar la actividad.
        if session.get("login_date") != date.today().isoformat():
            session.clear()
            flash("Tu sesión expiró. Iniciá sesión de nuevo.", "error")
            return redirect(url_for("user.login"))

        return vista(*args, **kwargs)

    return wrapper


def requiere_ver_eliminados(vista):
    """Para usar en cada vista `borrados()`: solo IT puede ver listas de
    eliminados, en cualquier módulo (BackOffice y Asesor quedan afuera)."""

    @wraps(vista)
    def wrapper(*args, **kwargs):
        if not puede_ver_eliminados(session.get("role")):
            flash("No tenés permiso para ver eliminados.", "error")
            return redirect(url_for("administrar.index"))
        return vista(*args, **kwargs)

    return wrapper


def restringir_a_administracion():
    """Para usar como before_request de blueprints reservados a IT/
    BackOffice (Sucursales, Empleados, Usuarios, Validaciones, Contabilidad,
    Preguntas frecuentes). Deja pasar el request si no hay sesión (para que
    login_required en la vista se encargue del redirect a login); si hay
    sesión pero el rol no alcanza, corta acá con un redirect a home."""
    if "user_id" not in session:
        return None
    if not puede_acceder_administracion(session.get("role")):
        flash("No tenés permiso para acceder a Administración.", "error")
        return redirect(url_for("administrar.index"))
    return None
