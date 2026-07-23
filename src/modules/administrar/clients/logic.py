import sqlite3

from src.constants.validations import (
    limpiar_documento,
    validar_campos_obligatorios,
    validar_documento,
    validar_email,
    validar_telefono,
)
from src.db.connection import obtener_conexion
from src.exceptions import RegistroBorradoExistente, ValidationError
from src.modules.administrar.branches.db import TABLA as TABLA_BRANCHES
from src.modules.administrar.clients.db import TABLA, TABLA_SUCURSALES


def _validar_datos(name, last_name, dni_cuit, phone, email):
    validar_campos_obligatorios({"name": name, "last_name": last_name, "dni_cuit": dni_cuit})

    dni_cuit_normalizado = validar_documento(dni_cuit)

    if email:
        validar_email(email)

    telefono_normalizado = validar_telefono(phone) if phone else None

    return dni_cuit_normalizado, telefono_normalizado


def _traducir_error_integridad(error):
    mensaje = str(error)
    if f"{TABLA}.dni_cuit" in mensaje:
        return ValidationError("Ya existe un cliente con ese DNI/CUIT.")
    return ValidationError("Ya existe un cliente con alguno de esos datos únicos.")


def _sincronizar_sucursales_cliente(conexion, id_cliente, branch_ids):
    """Reemplaza el set de sucursales asociadas a un cliente por branch_ids.
    branch_ids=None no toca nada (se usa en updates parciales); una lista
    vacía borra todas las asociaciones."""
    if branch_ids is None:
        return

    for branch_id in branch_ids:
        sucursal = conexion.execute(
            f"SELECT id FROM {TABLA_BRANCHES} WHERE id = ? AND status = 1", (branch_id,)
        ).fetchone()
        if sucursal is None:
            raise ValidationError("Una de las sucursales indicadas no existe.")

    conexion.execute(f"DELETE FROM {TABLA_SUCURSALES} WHERE client_id = ?", (id_cliente,))
    for branch_id in branch_ids:
        conexion.execute(
            f"INSERT INTO {TABLA_SUCURSALES} (client_id, branch_id) VALUES (?, ?)",
            (id_cliente, branch_id),
        )


def obtener_sucursales_ids_cliente(id_cliente):
    """Ids de las sucursales asociadas a un cliente."""
    with obtener_conexion() as conexion:
        filas = conexion.execute(
            f"SELECT branch_id FROM {TABLA_SUCURSALES} WHERE client_id = ?", (id_cliente,)
        ).fetchall()
        return [fila["branch_id"] for fila in filas]


def visible_para_sucursales(id_cliente, branch_ids_sesion):
    """True si el cliente debería ser visible para alguien con esas sucursales.

    Un cliente sin ninguna sucursal asignada queda visible para todos (dato
    sin asignar, no oculto); si tiene alguna, hace falta compartir al menos
    una con la sesión. branch_ids_sesion=None significa sin restricción."""
    if branch_ids_sesion is None:
        return True
    sucursales_cliente = obtener_sucursales_ids_cliente(id_cliente)
    if not sucursales_cliente:
        return True
    return any(branch_id in branch_ids_sesion for branch_id in sucursales_cliente)


def _buscar_borrado_por_dni_cuit(conexion, dni_cuit_normalizado):
    return conexion.execute(
        f"SELECT id FROM {TABLA} WHERE dni_cuit = ? AND status = 0", (dni_cuit_normalizado,)
    ).fetchone()


def crear_cliente(name, last_name, dni_cuit, phone=None, email=None, branch_ids=None):
    """Valida y crea un cliente nuevo. Devuelve el id generado.

    Si ya existe un cliente borrado con ese mismo DNI/CUIT, no crea uno
    nuevo: levanta RegistroBorradoExistente para que la vista ofrezca
    reactivar el que ya estaba en vez de chocar con el UNIQUE."""
    dni_cuit_normalizado, telefono_normalizado = _validar_datos(name, last_name, dni_cuit, phone, email)

    with obtener_conexion() as conexion:
        borrado = _buscar_borrado_por_dni_cuit(conexion, dni_cuit_normalizado)
        if borrado is not None:
            raise RegistroBorradoExistente(borrado["id"])

        try:
            cursor = conexion.execute(
                f"""
                INSERT INTO {TABLA} (name, last_name, dni_cuit, phone, email)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, last_name, dni_cuit_normalizado, telefono_normalizado, email),
            )
            id_cliente = cursor.lastrowid
            _sincronizar_sucursales_cliente(conexion, id_cliente, branch_ids if branch_ids is not None else [])
            conexion.commit()
            return id_cliente
        except sqlite3.IntegrityError as error:
            raise _traducir_error_integridad(error) from error


def obtener_por_id(id_cliente):
    with obtener_conexion() as conexion:
        return conexion.execute(f"SELECT * FROM {TABLA} WHERE id = ?", (id_cliente,)).fetchone()


def obtener_por_dni_cuit(dni_cuit):
    limpio = limpiar_documento(dni_cuit)
    with obtener_conexion() as conexion:
        return conexion.execute(f"SELECT * FROM {TABLA} WHERE dni_cuit = ?", (limpio,)).fetchone()


def listar_clientes(incluir_borrados=False, branch_ids=None):
    """branch_ids=None no filtra por sucursal. Si se pasa una lista, solo
    devuelve clientes sin ninguna sucursal asignada (dato sin asignar,
    visible para todos) o que comparten alguna con branch_ids."""
    condiciones = []
    parametros = []

    if not incluir_borrados:
        condiciones.append(f"{TABLA}.status = 1")

    if branch_ids is not None:
        placeholders = ", ".join("?" for _ in branch_ids) if branch_ids else "NULL"
        condiciones.append(
            f"""(
                NOT EXISTS (SELECT 1 FROM {TABLA_SUCURSALES} WHERE {TABLA_SUCURSALES}.client_id = {TABLA}.id)
                OR EXISTS (
                    SELECT 1 FROM {TABLA_SUCURSALES}
                    WHERE {TABLA_SUCURSALES}.client_id = {TABLA}.id
                        AND {TABLA_SUCURSALES}.branch_id IN ({placeholders})
                )
            )"""
        )
        parametros.extend(branch_ids)

    consulta = f"""
        SELECT {TABLA}.*, STRING_AGG({TABLA_BRANCHES}.name, ', ') AS branch_names
        FROM {TABLA}
        LEFT JOIN {TABLA_SUCURSALES} ON {TABLA_SUCURSALES}.client_id = {TABLA}.id
        LEFT JOIN {TABLA_BRANCHES}
            ON {TABLA_BRANCHES}.id = {TABLA_SUCURSALES}.branch_id AND {TABLA_BRANCHES}.status = 1
    """
    if condiciones:
        consulta += " WHERE " + " AND ".join(condiciones)
    consulta += f" GROUP BY {TABLA}.id ORDER BY {TABLA}.last_name, {TABLA}.name"

    with obtener_conexion() as conexion:
        return conexion.execute(consulta, parametros).fetchall()


def buscar_por_nombre(texto):
    """Busca clientes activos por coincidencia parcial en nombre o apellido."""
    patron = f"%{texto}%"
    with obtener_conexion() as conexion:
        return conexion.execute(
            f"""
            SELECT * FROM {TABLA}
            WHERE status = 1 AND (name LIKE ? OR last_name LIKE ?)
            ORDER BY last_name, name
            """,
            (patron, patron),
        ).fetchall()


def actualizar_cliente(id_cliente, name=None, last_name=None, dni_cuit=None, phone=None, email=None,
                        branch_ids=None):
    """Actualiza los campos recibidos; los que se pasan en None mantienen su
    valor actual. branch_ids=None mantiene las sucursales actuales; para
    vaciarlas pasar branch_ids=[]."""
    cliente_actual = obtener_por_id(id_cliente)
    if cliente_actual is None:
        raise ValidationError("El cliente no existe.")

    nuevos = {
        "name": name if name is not None else cliente_actual["name"],
        "last_name": last_name if last_name is not None else cliente_actual["last_name"],
        "dni_cuit": dni_cuit if dni_cuit is not None else cliente_actual["dni_cuit"],
        "phone": phone if phone is not None else cliente_actual["phone"],
        "email": email if email is not None else cliente_actual["email"],
    }

    dni_cuit_normalizado, telefono_normalizado = _validar_datos(
        nuevos["name"], nuevos["last_name"], nuevos["dni_cuit"], nuevos["phone"], nuevos["email"],
    )

    with obtener_conexion() as conexion:
        try:
            conexion.execute(
                f"""
                UPDATE {TABLA}
                SET name = ?, last_name = ?, dni_cuit = ?, phone = ?, email = ?
                WHERE id = ?
                """,
                (nuevos["name"], nuevos["last_name"], dni_cuit_normalizado, telefono_normalizado,
                 nuevos["email"], id_cliente),
            )
            _sincronizar_sucursales_cliente(conexion, id_cliente, branch_ids)
            conexion.commit()
        except sqlite3.IntegrityError as error:
            raise _traducir_error_integridad(error) from error


def borrar_cliente(id_cliente):
    """Borrado lógico: marca status = 0 en vez de eliminar la fila."""
    with obtener_conexion() as conexion:
        conexion.execute(f"UPDATE {TABLA} SET status = 0 WHERE id = ?", (id_cliente,))
        conexion.commit()


def reactivar_cliente(id_cliente):
    """Revierte un borrado lógico: vuelve a marcar status = 1."""
    with obtener_conexion() as conexion:
        conexion.execute(f"UPDATE {TABLA} SET status = 1 WHERE id = ?", (id_cliente,))
        conexion.commit()
