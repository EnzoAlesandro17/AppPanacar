class ValidationError(Exception):
    """Se lanza cuando los datos no cumplen las reglas de validación del negocio."""


class RegistroBorradoExistente(Exception):
    """Se lanza al intentar crear un registro que choca con uno ya borrado
    (mismo valor único, ej. DNI/CUIT, dominio, code): en vez de rechazarlo
    por duplicado, se ofrece reactivar ese id en vez de crear uno nuevo."""

    def __init__(self, id_existente):
        self.id_existente = id_existente
        super().__init__(f"Ya existe un registro borrado con ese valor (id {id_existente}).")
