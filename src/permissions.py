"""Reglas de que rol puede hacer que accion, centralizadas para reusar entre modulos."""

_GESTIONAN_USUARIOS = ("Admin", "BackOffice")


def puede_gestionar_usuarios(role):
    return role in _GESTIONAN_USUARIOS


def puede_cambiar_password(actor_role, target_role, es_uno_mismo):
    """Jerarquia: Admin > BackOffice > Asesor.

    - Admin cambia la de cualquiera.
    - BackOffice cambia la de cualquiera menos Admin.
    - Asesor solo puede cambiar la propia.
    - Cualquiera puede cambiar la propia.
    """
    if es_uno_mismo:
        return True
    if actor_role == "Admin":
        return True
    if actor_role == "BackOffice":
        return target_role != "Admin"
    return False
