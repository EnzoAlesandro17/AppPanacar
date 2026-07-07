"""Guarda el usuario logueado en la sesión de Flask (por request, no en memoria global).

Reemplaza al viejo src/session.py de la app de escritorio: ahí un usuario
por proceso tenía sentido con Tkinter, pero en un servidor web cada request
puede ser de una sucursal o persona distinta.
"""

from functools import wraps

from flask import redirect, session, url_for


def login_required(vista):
    @wraps(vista)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("user.login"))
        return vista(*args, **kwargs)

    return wrapper
