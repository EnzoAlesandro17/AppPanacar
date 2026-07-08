from src.breadcrumbs import migas


def test_migas_convierte_string_final_en_paso_sin_link():
    resultado = migas(("Sistema de gestión", "administrar.index"), "Sucursales")

    assert resultado == [("Sistema de gestión", "administrar.index"), ("Sucursales", None)]


def test_migas_respeta_tuplas_explicitas():
    resultado = migas(("Inicio", "administrar.index"), ("Administración", "administracion.index"))

    assert resultado == [("Inicio", "administrar.index"), ("Administración", "administracion.index")]


def test_migas_sin_pasos_devuelve_lista_vacia():
    assert migas() == []
