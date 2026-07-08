import pytest

from src.constants.validations import formatear_fecha_visual, parsear_fecha_visual
from src.exceptions import ValidationError


def test_parsear_fecha_visual_convierte_a_iso():
    assert parsear_fecha_visual("15/03/1990") == "1990-03-15"


@pytest.mark.parametrize("cadena", ["1990-03-15", "15-03-1990", "32/01/2000", "no es una fecha"])
def test_parsear_fecha_visual_rechaza_formato_invalido(cadena):
    with pytest.raises(ValidationError):
        parsear_fecha_visual(cadena)


def test_formatear_fecha_visual_convierte_iso_a_dd_mm_aaaa():
    assert formatear_fecha_visual("1990-03-15") == "15/03/1990"


def test_formatear_fecha_visual_con_vacio_devuelve_vacio():
    assert formatear_fecha_visual(None) == ""
    assert formatear_fecha_visual("") == ""


def test_formatear_fecha_visual_con_algo_que_no_es_iso_lo_devuelve_igual():
    """Cubre el reintento de un formulario: si ya viene en dd/mm/aaaa (porque
    el usuario lo tipeó así y hubo un error de validación en otro campo), no
    hay que romperlo ni reinterpretarlo."""
    assert formatear_fecha_visual("15/03/1990") == "15/03/1990"
