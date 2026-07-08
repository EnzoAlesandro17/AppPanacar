import pytest

from src.constants.validations import (
    limpiar_documento,
    validar_anio_vehiculo,
    validar_campos_obligatorios,
    validar_cuit,
    validar_dni,
    validar_documento,
    validar_dominio,
    validar_email,
    validar_fecha,
    validar_mayor_edad,
    validar_password,
    validar_telefono,
)
from src.exceptions import ValidationError

CUIT_VALIDO = "20100000009"


def test_validar_email_acepta_formato_valido():
    validar_email("gerente@panacar.com")


@pytest.mark.parametrize("email", ["sin-arroba.com", "@sinusuario.com", "usuario@sindominio"])
def test_validar_email_rechaza_formato_invalido(email):
    with pytest.raises(ValidationError):
        validar_email(email)


@pytest.mark.parametrize("telefono", ["+54 9 341 5018444", "341 5018444", "34150184441234"])
def test_validar_telefono_acepta_e164(telefono):
    limpio = validar_telefono(telefono)
    assert " " not in limpio


@pytest.mark.parametrize("telefono", ["123", "abcdefgh", "+" + "1" * 20])
def test_validar_telefono_rechaza_formato_invalido(telefono):
    with pytest.raises(ValidationError):
        validar_telefono(telefono)


@pytest.mark.parametrize("dni", ["1234567", "12345678"])
def test_validar_dni_acepta_7_u_8_digitos(dni):
    validar_dni(dni)


@pytest.mark.parametrize("dni", ["123456", "123456789", "1234567a"])
def test_validar_dni_rechaza_formato_invalido(dni):
    with pytest.raises(ValidationError):
        validar_dni(dni)


def test_validar_cuit_acepta_digito_verificador_correcto():
    assert validar_cuit(CUIT_VALIDO) == CUIT_VALIDO


def test_validar_cuit_acepta_con_guiones():
    con_guiones = f"{CUIT_VALIDO[:2]}-{CUIT_VALIDO[2:10]}-{CUIT_VALIDO[10]}"
    assert validar_cuit(con_guiones) == CUIT_VALIDO


def test_validar_cuit_rechaza_digito_verificador_incorrecto():
    invalido = CUIT_VALIDO[:-1] + str((int(CUIT_VALIDO[-1]) + 1) % 10)
    with pytest.raises(ValidationError):
        validar_cuit(invalido)


def test_validar_cuit_rechaza_longitud_invalida():
    with pytest.raises(ValidationError):
        validar_cuit("123")


def test_validar_documento_detecta_dni():
    assert validar_documento("12345678") == "12345678"


def test_validar_documento_detecta_cuit():
    assert validar_documento(CUIT_VALIDO) == CUIT_VALIDO


def test_validar_documento_rechaza_longitud_invalida():
    with pytest.raises(ValidationError):
        validar_documento("123456789")


def test_limpiar_documento_saca_guiones_y_espacios():
    assert limpiar_documento("20-100000009") == "20100000009"


@pytest.mark.parametrize("password", ["1234567", "a" * 65])
def test_validar_password_rechaza_longitud_invalida(password):
    with pytest.raises(ValidationError):
        validar_password(password)


@pytest.mark.parametrize("password", ["12345678", "a" * 64])
def test_validar_password_acepta_longitud_valida(password):
    validar_password(password)


def test_validar_campos_obligatorios_rechaza_vacio():
    with pytest.raises(ValidationError):
        validar_campos_obligatorios({"name": "Juan", "last_name": ""})


def test_validar_campos_obligatorios_acepta_todos_cargados():
    validar_campos_obligatorios({"name": "Juan", "last_name": "Perez"})


def test_validar_fecha_rechaza_formato_invalido():
    with pytest.raises(ValidationError):
        validar_fecha("31/12/2000")


def test_validar_mayor_edad_rechaza_menor():
    fecha = validar_fecha("2015-01-01")
    with pytest.raises(ValidationError):
        validar_mayor_edad(fecha, edad_minima=18)


def test_validar_mayor_edad_acepta_mayor():
    fecha = validar_fecha("1990-01-01")
    validar_mayor_edad(fecha, edad_minima=18)


@pytest.mark.parametrize("dominio,esperado", [("abc123", "ABC123"), ("ab-123-cd", "AB123CD")])
def test_validar_dominio_acepta_formatos_argentinos(dominio, esperado):
    assert validar_dominio(dominio) == esperado


@pytest.mark.parametrize("dominio", ["ABCD123", "AB1234C", "123ABC"])
def test_validar_dominio_rechaza_formato_invalido(dominio):
    with pytest.raises(ValidationError):
        validar_dominio(dominio)


def test_validar_anio_vehiculo_rechaza_fuera_de_rango():
    with pytest.raises(ValidationError):
        validar_anio_vehiculo(1899)


def test_validar_anio_vehiculo_rechaza_no_numerico():
    with pytest.raises(ValidationError):
        validar_anio_vehiculo("no-es-un-anio")


def test_validar_anio_vehiculo_acepta_rango_valido():
    assert validar_anio_vehiculo("2020") == 2020
