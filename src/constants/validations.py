import re
from datetime import date, datetime

from src.exceptions import ValidationError

_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_DNI_REGEX = re.compile(r"^\d{7,8}$")
_CUIT_REGEX = re.compile(r"^\d{11}$")
_PHONE_REGEX = re.compile(r"^\+?\d{8,15}$")  # Formato E.164 (estándar ITU-T)
_DOMINIO_VIEJO_REGEX = re.compile(r"^[A-Z]{3}\d{3}$")
_DOMINIO_MERCOSUR_REGEX = re.compile(r"^[A-Z]{2}\d{3}[A-Z]{2}$")
_FORMATO_FECHA = "%Y-%m-%d"

_PASSWORD_MIN_LENGTH = 8
_PASSWORD_MAX_LENGTH = 64


def validar_email(email):
    if not _EMAIL_REGEX.match(email):
        raise ValidationError("El email no tiene un formato válido.")


def validar_telefono(phone):
    """Valida formato E.164 (estándar internacional ITU-T): "+" opcional seguido
    de 8 a 15 dígitos en total. No exige un largo fijo porque varía según el
    país (ej: +54 9 341 5018444 o 341 5018444 son ambos válidos).

    Devuelve el teléfono normalizado (solo dígitos y el "+" opcional al
    inicio, sin espacios ni guiones).
    """
    limpio = re.sub(r"[\s-]", "", phone)
    if not _PHONE_REGEX.match(limpio):
        raise ValidationError(
            "El teléfono debe tener entre 8 y 15 dígitos (formato internacional "
            "E.164), con o sin '+' al inicio, ej: +54 9 341 5018444."
        )
    return limpio


def validar_dni(dni):
    if not _DNI_REGEX.match(dni):
        raise ValidationError("El DNI debe tener entre 7 y 8 dígitos, sin puntos ni letras.")


_MULTIPLICADORES_CUIT = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)


def _digito_verificador_cuit(primeros_diez):
    suma = sum(int(digito) * multiplicador for digito, multiplicador in zip(primeros_diez, _MULTIPLICADORES_CUIT))
    resto = 11 - (suma % 11)
    if resto == 11:
        return 0
    if resto == 10:
        return None  # No existe dígito verificador válido para esta combinación.
    return resto


def validar_cuit(cuit):
    """Valida formato (11 dígitos, XX-XXXXXXXX-X) y dígito verificador (módulo 11, igual que AFIP).

    Devuelve el CUIT normalizado (solo dígitos, sin guiones).
    """
    limpio = re.sub(r"-", "", cuit)
    if not _CUIT_REGEX.match(limpio):
        raise ValidationError("El CUIT debe tener 11 dígitos, ej: 20-12345678-9.")

    verificador = _digito_verificador_cuit(limpio[:10])
    if verificador is None or verificador != int(limpio[10]):
        raise ValidationError("El CUIT no es válido: el dígito verificador no coincide.")

    return limpio


def validar_dominio(dominio):
    """Valida el dominio (patente) argentino: formato viejo (ABC123) o Mercosur
    (AB123CD). Devuelve el dominio normalizado (mayúsculas, sin espacios ni guiones).
    """
    limpio = re.sub(r"[\s-]", "", dominio).upper()
    if not _DOMINIO_VIEJO_REGEX.match(limpio) and not _DOMINIO_MERCOSUR_REGEX.match(limpio):
        raise ValidationError("El dominio debe tener formato ABC123 (viejo) o AB123CD (Mercosur).")
    return limpio


def validar_anio_vehiculo(year):
    """Valida que el año sea un entero entre 1900 y el año próximo (modelos que
    salen a la venta con el año siguiente al calendario actual)."""
    try:
        year_int = int(year)
    except (TypeError, ValueError):
        raise ValidationError("El año debe ser un número.")

    anio_maximo = date.today().year + 1
    if year_int < 1900 or year_int > anio_maximo:
        raise ValidationError(f"El año debe estar entre 1900 y {anio_maximo}.")
    return year_int


def validar_fecha(fecha_str):
    """Valida formato AAAA-MM-DD y devuelve un date."""
    try:
        return datetime.strptime(fecha_str, _FORMATO_FECHA).date()
    except (ValueError, TypeError):
        raise ValidationError("La fecha debe tener formato AAAA-MM-DD y ser una fecha válida.")


_FORMATO_FECHA_VISUAL = "%d/%m/%Y"


def parsear_fecha_visual(cadena):
    """Convierte una fecha ingresada en formato argentino (dd/mm/aaaa) al
    formato ISO (aaaa-mm-dd) que se guarda en la base. `validar_fecha` y
    `validar_mayor_edad` siguen trabajando en ISO; esta función es la que
    traduce lo que tipea el usuario antes de llegar ahí."""
    try:
        fecha = datetime.strptime(cadena, _FORMATO_FECHA_VISUAL).date()
    except (ValueError, TypeError):
        raise ValidationError("La fecha debe tener formato dd/mm/aaaa y ser una fecha válida.")
    return fecha.strftime(_FORMATO_FECHA)


def formatear_fecha_visual(fecha_iso):
    """Convierte una fecha guardada en ISO (aaaa-mm-dd) a formato argentino
    (dd/mm/aaaa) para mostrarla en los formularios. Si no es una fecha ISO
    válida (ej. viene de un reintento con lo que el usuario ya había
    tipeado), la devuelve sin tocar."""
    if not fecha_iso:
        return ""
    try:
        return datetime.strptime(fecha_iso, _FORMATO_FECHA).strftime(_FORMATO_FECHA_VISUAL)
    except ValueError:
        return fecha_iso


def validar_mayor_edad(fecha_nacimiento, edad_minima=18):
    """Recibe un date (ver validar_fecha) y valida una edad mínima."""
    hoy = date.today()
    edad = hoy.year - fecha_nacimiento.year - (
        (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
    )
    if edad < edad_minima:
        raise ValidationError(f"La persona debe ser mayor de {edad_minima} años.")


def validar_password(password):
    """Valida longitud según NIST SP 800-63B (el estándar actual de la comunidad
    para políticas de contraseñas): mínimo 8 caracteres, máximo 64.

    A propósito no exige reglas de complejidad (mayúsculas, números,
    símbolos): ese mismo estándar desaconseja forzarlas porque en la
    práctica generan contraseñas predecibles (ej: "Password1!") sin mejorar
    la seguridad real, y terminan siendo más difíciles de recordar.
    """
    if len(password) < _PASSWORD_MIN_LENGTH:
        raise ValidationError(f"La contraseña debe tener al menos {_PASSWORD_MIN_LENGTH} caracteres.")
    if len(password) > _PASSWORD_MAX_LENGTH:
        raise ValidationError(f"La contraseña no puede superar los {_PASSWORD_MAX_LENGTH} caracteres.")


def validar_campos_obligatorios(campos):
    """Recibe {nombre_campo: valor} y lanza ValidationError con el primero vacío."""
    for campo, valor in campos.items():
        if not valor or not str(valor).strip():
            raise ValidationError(f"Falta {campo}")


def limpiar_documento(valor):
    return valor.replace("-", "").replace(" ", "")


def validar_documento(dni_cuit):
    """Detecta si es DNI (7-8 dígitos) o CUIT (11 dígitos), valida y devuelve el valor normalizado."""
    limpio = limpiar_documento(dni_cuit)
    if len(limpio) in (7, 8):
        validar_dni(limpio)
    elif len(limpio) == 11:
        validar_cuit(limpio)
    else:
        raise ValidationError("El documento debe tener 7-8 dígitos (DNI) u 11 dígitos (CUIT).")
    return limpio
