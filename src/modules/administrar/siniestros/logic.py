from datetime import datetime

from src.constants.validations import validar_campos_obligatorios, validar_fecha
from src.db.connection import obtener_conexion
from src.exceptions import ValidationError
from src.modules.administrar.branches.db import TABLA as TABLA_BRANCHES
from src.modules.administrar.clients.db import TABLA as TABLA_CLIENTS
from src.modules.administrar.siniestros.db import TABLA, TABLA_COMENTARIOS, TABLA_HISTORIAL
from src.modules.administrar.validaciones.claim_statuses.db import TABLA as TABLA_CLAIM_STATUSES
from src.modules.administrar.validaciones.claim_statuses.logic import obtener_por_id as obtener_estado_por_id
from src.modules.administrar.validaciones.claim_types.db import TABLA as TABLA_CLAIM_TYPES
from src.modules.administrar.validaciones.claim_types.logic import obtener_por_id as obtener_tipo_por_id
from src.modules.administrar.validaciones.insurance_companies.db import TABLA as TABLA_INSURANCE_COMPANIES
from src.modules.administrar.validaciones.insurance_companies.logic import (
    obtener_por_id as obtener_aseguradora_por_id,
)
from src.modules.administrar.vehicles.db import TABLA as TABLA_VEHICLES


def _validar_datos(client_id, vehicle_id, insurance_company_id, claim_type_id, claim_status_id,
                    branch_id, opened_date):
    validar_campos_obligatorios({
        "client_id": client_id,
        "vehicle_id": vehicle_id,
        "claim_status_id": claim_status_id,
        "branch_id": branch_id,
        "opened_date": opened_date,
    })
    validar_fecha(opened_date)

    with obtener_conexion() as conexion:
        cliente = conexion.execute(
            f"SELECT id FROM {TABLA_CLIENTS} WHERE id = ? AND status = 1", (client_id,)
        ).fetchone()
        if cliente is None:
            raise ValidationError("El cliente indicado no existe.")

        vehiculo = conexion.execute(
            f"SELECT id FROM {TABLA_VEHICLES} WHERE id = ? AND status = 1", (vehicle_id,)
        ).fetchone()
        if vehiculo is None:
            raise ValidationError("El vehículo indicado no existe.")

        sucursal = conexion.execute(
            f"SELECT id FROM {TABLA_BRANCHES} WHERE id = ? AND status = 1", (branch_id,)
        ).fetchone()
        if sucursal is None:
            raise ValidationError("La sucursal indicada no existe.")

    estado = obtener_estado_por_id(claim_status_id)
    if estado is None or estado["status"] == 0:
        raise ValidationError("El estado indicado no existe.")

    if insurance_company_id is not None:
        aseguradora = obtener_aseguradora_por_id(insurance_company_id)
        if aseguradora is None or aseguradora["status"] == 0:
            raise ValidationError("La compañía de seguro indicada no existe.")

    if claim_type_id is not None:
        tipo = obtener_tipo_por_id(claim_type_id)
        if tipo is None or tipo["status"] == 0:
            raise ValidationError("El tipo de siniestro indicado no existe.")


def _registrar_cambio_estado(conexion, siniestro_id, previous_status_id, new_status_id,
                              changed_by_user_id, changed_by_username):
    conexion.execute(
        f"""
        INSERT INTO {TABLA_HISTORIAL}
            (siniestro_id, previous_status_id, new_status_id, changed_by, changed_by_username, changed_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (siniestro_id, previous_status_id, new_status_id, changed_by_user_id, changed_by_username,
         datetime.now().isoformat()),
    )


def visible_para_sucursales(id_siniestro, branch_ids_sesion):
    """True si el siniestro debería ser visible para alguien con esas sucursales.

    A diferencia de Clientes/Vehículos/Stock, la sucursal es obligatoria (FK
    simple): no existe el caso de "sin asignar, visible para todos"."""
    if branch_ids_sesion is None:
        return True
    siniestro = obtener_por_id(id_siniestro)
    if siniestro is None:
        return False
    return siniestro["branch_id"] in branch_ids_sesion


def crear_siniestro(client_id, vehicle_id, claim_status_id, branch_id, opened_date,
                     insurance_company_id=None, claim_type_id=None, description=None,
                     changed_by_user_id=None, changed_by_username=None):
    """Valida y crea un siniestro nuevo. Devuelve el id generado.

    Al crearlo se registra el primer paso del historial de estados (sin
    estado anterior)."""
    _validar_datos(
        client_id, vehicle_id, insurance_company_id, claim_type_id, claim_status_id, branch_id, opened_date
    )

    with obtener_conexion() as conexion:
        cursor = conexion.execute(
            f"""
            INSERT INTO {TABLA}
                (client_id, vehicle_id, insurance_company_id, claim_type_id, claim_status_id, branch_id,
                 opened_date, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (client_id, vehicle_id, insurance_company_id, claim_type_id, claim_status_id, branch_id,
             opened_date, description),
        )
        id_siniestro = cursor.lastrowid
        _registrar_cambio_estado(
            conexion, id_siniestro, None, claim_status_id, changed_by_user_id, changed_by_username
        )
        conexion.commit()
        return id_siniestro


def obtener_por_id(id_siniestro):
    with obtener_conexion() as conexion:
        return conexion.execute(f"SELECT * FROM {TABLA} WHERE id = ?", (id_siniestro,)).fetchone()


def listar_siniestros(incluir_borrados=False, branch_ids=None):
    """branch_ids=None no filtra por sucursal. Si se pasa una lista (aunque
    esté vacía), solo devuelve siniestros de esas sucursales: a diferencia de
    Clientes/Vehículos/Stock la sucursal es obligatoria, no hay "sin
    asignar" que quede visible para todos."""
    condiciones = []
    parametros = []

    if not incluir_borrados:
        condiciones.append(f"{TABLA}.status = 1")

    if branch_ids is not None:
        placeholders = ", ".join("?" for _ in branch_ids) if branch_ids else "NULL"
        condiciones.append(f"{TABLA}.branch_id IN ({placeholders})")
        parametros.extend(branch_ids)

    consulta = f"""
        SELECT {TABLA}.*,
               {TABLA_CLIENTS}.name AS client_name, {TABLA_CLIENTS}.last_name AS client_last_name,
               {TABLA_VEHICLES}.model AS vehicle_model, {TABLA_VEHICLES}.license_plate AS vehicle_license_plate,
               {TABLA_INSURANCE_COMPANIES}.name AS insurance_company_name,
               {TABLA_CLAIM_TYPES}.name AS claim_type_name,
               {TABLA_CLAIM_STATUSES}.name AS claim_status_name,
               {TABLA_BRANCHES}.name AS branch_name
        FROM {TABLA}
        JOIN {TABLA_CLIENTS} ON {TABLA_CLIENTS}.id = {TABLA}.client_id
        JOIN {TABLA_VEHICLES} ON {TABLA_VEHICLES}.id = {TABLA}.vehicle_id
        LEFT JOIN {TABLA_INSURANCE_COMPANIES} ON {TABLA_INSURANCE_COMPANIES}.id = {TABLA}.insurance_company_id
        LEFT JOIN {TABLA_CLAIM_TYPES} ON {TABLA_CLAIM_TYPES}.id = {TABLA}.claim_type_id
        JOIN {TABLA_CLAIM_STATUSES} ON {TABLA_CLAIM_STATUSES}.id = {TABLA}.claim_status_id
        JOIN {TABLA_BRANCHES} ON {TABLA_BRANCHES}.id = {TABLA}.branch_id
    """
    if condiciones:
        consulta += " WHERE " + " AND ".join(condiciones)
    consulta += f" ORDER BY {TABLA}.opened_date DESC, {TABLA}.id DESC"

    with obtener_conexion() as conexion:
        return conexion.execute(consulta, parametros).fetchall()


def listar_historial(id_siniestro):
    """Historial de cambios de estado de un siniestro, más antiguo primero."""
    with obtener_conexion() as conexion:
        return conexion.execute(
            f"""
            SELECT {TABLA_HISTORIAL}.*,
                   previo.name AS previous_status_name,
                   nuevo.name AS new_status_name
            FROM {TABLA_HISTORIAL}
            LEFT JOIN {TABLA_CLAIM_STATUSES} AS previo ON previo.id = {TABLA_HISTORIAL}.previous_status_id
            JOIN {TABLA_CLAIM_STATUSES} AS nuevo ON nuevo.id = {TABLA_HISTORIAL}.new_status_id
            WHERE siniestro_id = ?
            ORDER BY {TABLA_HISTORIAL}.id
            """,
            (id_siniestro,),
        ).fetchall()


def agregar_comentario(id_siniestro, comentario, changed_by_user_id=None, changed_by_username=None):
    """Observación libre sobre el siniestro (no cambia ningún dato del siniestro en sí)."""
    comentario = (comentario or "").strip()
    if not comentario:
        raise ValidationError("La observación no puede estar vacía.")
    if obtener_por_id(id_siniestro) is None:
        raise ValidationError("El siniestro no existe.")

    with obtener_conexion() as conexion:
        conexion.execute(
            f"""
            INSERT INTO {TABLA_COMENTARIOS} (siniestro_id, comentario, changed_by, changed_by_username, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (id_siniestro, comentario, changed_by_user_id, changed_by_username, datetime.now().isoformat()),
        )
        conexion.commit()


def listar_comentarios(id_siniestro):
    with obtener_conexion() as conexion:
        return conexion.execute(
            f"SELECT * FROM {TABLA_COMENTARIOS} WHERE siniestro_id = ? ORDER BY id", (id_siniestro,)
        ).fetchall()


def listar_actividad(id_siniestro):
    """Línea de tiempo del siniestro (más antiguo primero): cambios de estado
    (automáticos) + observaciones libres, mezclados en orden cronológico."""
    eventos = []

    for paso in listar_historial(id_siniestro):
        if paso["previous_status_id"] is None:
            texto = f'Siniestro abierto con estado "{paso["new_status_name"]}".'
        else:
            texto = f'Estado cambiado de "{paso["previous_status_name"]}" a "{paso["new_status_name"]}".'
        eventos.append({
            "tipo": "estado", "fecha": paso["changed_at"], "texto": texto,
            "usuario": paso["changed_by_username"],
        })

    for comentario in listar_comentarios(id_siniestro):
        eventos.append({
            "tipo": "comentario", "fecha": comentario["created_at"], "texto": comentario["comentario"],
            "usuario": comentario["changed_by_username"],
        })

    eventos.sort(key=lambda evento: evento["fecha"])
    return eventos


def actualizar_siniestro(id_siniestro, client_id=None, vehicle_id=None, claim_status_id=None,
                          branch_id=None, opened_date=None, description=None,
                          insurance_company_id=None, quitar_aseguradora=False,
                          claim_type_id=None, quitar_tipo=False,
                          changed_by_user_id=None, changed_by_username=None):
    """Actualiza los campos recibidos; los que se pasan en None mantienen su
    valor actual. insurance_company_id=None mantiene la aseguradora actual;
    para desvincularla explícitamente pasar quitar_aseguradora=True (mismo
    criterio para claim_type_id/quitar_tipo).

    Si claim_status_id cambia respecto al actual, registra el paso en el
    historial de estados."""
    siniestro_actual = obtener_por_id(id_siniestro)
    if siniestro_actual is None:
        raise ValidationError("El siniestro no existe.")

    nuevos = {
        "client_id": client_id if client_id is not None else siniestro_actual["client_id"],
        "vehicle_id": vehicle_id if vehicle_id is not None else siniestro_actual["vehicle_id"],
        "insurance_company_id": None if quitar_aseguradora else (
            insurance_company_id if insurance_company_id is not None
            else siniestro_actual["insurance_company_id"]
        ),
        "claim_type_id": None if quitar_tipo else (
            claim_type_id if claim_type_id is not None else siniestro_actual["claim_type_id"]
        ),
        "claim_status_id": claim_status_id if claim_status_id is not None else siniestro_actual["claim_status_id"],
        "branch_id": branch_id if branch_id is not None else siniestro_actual["branch_id"],
        "opened_date": opened_date if opened_date is not None else siniestro_actual["opened_date"],
        "description": description if description is not None else siniestro_actual["description"],
    }

    _validar_datos(
        nuevos["client_id"], nuevos["vehicle_id"], nuevos["insurance_company_id"], nuevos["claim_type_id"],
        nuevos["claim_status_id"], nuevos["branch_id"], nuevos["opened_date"],
    )

    with obtener_conexion() as conexion:
        conexion.execute(
            f"""
            UPDATE {TABLA}
            SET client_id = ?, vehicle_id = ?, insurance_company_id = ?, claim_type_id = ?,
                claim_status_id = ?, branch_id = ?, opened_date = ?, description = ?
            WHERE id = ?
            """,
            (nuevos["client_id"], nuevos["vehicle_id"], nuevos["insurance_company_id"], nuevos["claim_type_id"],
             nuevos["claim_status_id"], nuevos["branch_id"], nuevos["opened_date"],
             nuevos["description"], id_siniestro),
        )
        if nuevos["claim_status_id"] != siniestro_actual["claim_status_id"]:
            _registrar_cambio_estado(
                conexion, id_siniestro, siniestro_actual["claim_status_id"], nuevos["claim_status_id"],
                changed_by_user_id, changed_by_username,
            )
        conexion.commit()


def borrar_siniestro(id_siniestro):
    """Borrado lógico: marca status = 0 en vez de eliminar la fila."""
    with obtener_conexion() as conexion:
        conexion.execute(f"UPDATE {TABLA} SET status = 0 WHERE id = ?", (id_siniestro,))
        conexion.commit()


def reactivar_siniestro(id_siniestro):
    """Revierte un borrado lógico: vuelve a marcar status = 1."""
    with obtener_conexion() as conexion:
        conexion.execute(f"UPDATE {TABLA} SET status = 1 WHERE id = ?", (id_siniestro,))
        conexion.commit()
