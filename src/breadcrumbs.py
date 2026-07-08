def migas(*pasos):
    """Arma la lista de breadcrumbs para el nav de base.html.

    Cada paso es una tupla (etiqueta, endpoint) o, para el último paso (la
    página actual, sin link), directamente un string con la etiqueta.
    """
    return [(paso, None) if isinstance(paso, str) else paso for paso in pasos]
