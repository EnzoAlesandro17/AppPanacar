"""Reglas de que rol puede hacer que accion, centralizadas para reusar entre modulos."""

_GESTIONAN_USUARIOS = ("IT", "BackOffice")
_ACCEDEN_ADMINISTRACION = ("IT", "BackOffice")


def puede_gestionar_usuarios(role):
    return role in _GESTIONAN_USUARIOS


def puede_acceder_administracion(role):
    """Sucursales, Empleados, Usuarios, Validaciones, Contabilidad y
    Preguntas frecuentes: toda la sección "Administración" es exclusiva de
    IT/BackOffice, Asesor no debería ni verla."""
    return role in _ACCEDEN_ADMINISTRACION


def puede_cambiar_password(actor_role, target_role, es_uno_mismo):
    """Jerarquia: IT > BackOffice > Asesor.

    - IT cambia la de cualquiera.
    - BackOffice cambia la de cualquiera menos IT.
    - Asesor solo puede cambiar la propia.
    - Cualquiera puede cambiar la propia.
    """
    if es_uno_mismo:
        return True
    if actor_role == "IT":
        return True
    if actor_role == "BackOffice":
        return target_role != "IT"
    return False


def puede_ver_eliminados(role):
    """Solo IT puede ver listas de registros eliminados, en cualquier módulo."""
    return role == "IT"
