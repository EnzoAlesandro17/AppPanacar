"""Reglas de que rol puede hacer que accion, centralizadas para reusar entre modulos."""

_GESTIONAN_USUARIOS = ("Admin", "Supervisor")


def puede_gestionar_usuarios(role):
    return role in _GESTIONAN_USUARIOS


def puede_cambiar_password(actor_role, target_role, es_uno_mismo):
    """Jerarquia: Admin > Supervisor. Vendedor no tiene password.

    - Admin cambia la de cualquiera (Admin o Supervisor).
    - Supervisor cambia la de cualquiera menos Admin.
    - Vendedor no tiene password: ni la cambia ni se la cambian.
    - Cualquiera (menos Vendedor) puede cambiar la propia.
    """
    if actor_role == "Vendedor" or target_role == "Vendedor":
        return False
    if es_uno_mismo:
        return True
    if actor_role == "Admin":
        return True
    if actor_role == "Supervisor":
        return target_role != "Admin"
    return False
