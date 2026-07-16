from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from src.auth import login_required, requiere_ver_eliminados
from src.breadcrumbs import migas
from src.constants.validations import parsear_fecha_visual
from src.exceptions import RegistroBorradoExistente, ValidationError
from src.modules.administrar.branches.logic import listar_sucursales
from src.modules.administrar.clients.logic import crear_cliente, listar_clientes
from src.modules.administrar.clients.logic import obtener_por_id as obtener_cliente_por_id
from src.modules.administrar.siniestros.logic import (
    actualizar_siniestro,
    agregar_comentario,
    borrar_siniestro,
    crear_siniestro,
    listar_actividad,
    listar_siniestros,
    obtener_por_id,
    reactivar_siniestro,
    visible_para_sucursales,
)
from src.modules.administrar.validaciones.claim_statuses.logic import listar_estados
from src.modules.administrar.validaciones.claim_types.logic import listar_tipos
from src.modules.administrar.validaciones.insurance_companies.logic import listar_aseguradoras
from src.modules.administrar.validaciones.vehicle_brands.logic import listar_marcas
from src.modules.administrar.vehicles.logic import crear_vehiculo, listar_vehiculos
from src.modules.administrar.vehicles.logic import obtener_por_id as obtener_vehiculo_por_id
from src.permissions import puede_ver_eliminados

siniestros_bp = Blueprint("siniestros", __name__, url_prefix="/siniestros")


def _migas(*ultimos):
    piezas = [("Sistema de gestión", "administrar.index")]
    piezas.append(("Siniestros", "siniestros.listar") if ultimos else "Siniestros")
    piezas.extend(ultimos)
    return migas(*piezas)


def _parsear_numero(valor, campo, tipo):
    valor = valor.strip()
    if not valor:
        return None
    try:
        return tipo(valor)
    except ValueError:
        raise ValidationError(f"{campo} debe ser un número.")


def _sucursales_seleccionables():
    """IT puede asignar cualquier sucursal; los demás roles solo las propias."""
    if session.get("role") == "IT":
        return listar_sucursales()
    propias = set(session.get("branch_ids") or [])
    return [sucursal for sucursal in listar_sucursales() if sucursal["id"] in propias]


def _requiere_acceso_al_siniestro(id_siniestro):
    """None si el siniestro es visible para las sucursales de la sesión; si no, un redirect listo para devolver."""
    if not visible_para_sucursales(id_siniestro, session.get("branch_ids")):
        flash("No tenés acceso a ese siniestro.", "error")
        return redirect(url_for("siniestros.listar"))
    return None


def _resolver_cliente(form):
    """Devuelve el client_id a usar: si modo_cliente es 'nuevo', da de alta el
    cliente ahí mismo (mismas validaciones que Clientes); si no, toma el
    client_id elegido en el selector."""
    if form.get("modo_cliente") == "nuevo":
        return crear_cliente(
            name=form.get("cliente_name", "").strip(),
            last_name=form.get("cliente_last_name", "").strip(),
            dni_cuit=form.get("cliente_dni_cuit", "").strip(),
            phone=form.get("cliente_phone", "").strip() or None,
            email=form.get("cliente_email", "").strip() or None,
        )
    client_id = _parsear_numero(form.get("client_id", ""), "client_id", int)
    if client_id is None:
        raise ValidationError("Falta elegir un cliente.")
    return client_id


def _resolver_vehiculo(form):
    """Devuelve el vehicle_id a usar: si modo_vehiculo es 'nuevo', da de alta
    el vehículo ahí mismo (mismas validaciones que Vehículos); si no, toma el
    vehicle_id elegido en el selector."""
    if form.get("modo_vehiculo") == "nuevo":
        return crear_vehiculo(
            brand_id=_parsear_numero(form.get("vehiculo_brand_id", ""), "brand_id", int),
            model=form.get("vehiculo_model", "").strip(),
            year=_parsear_numero(form.get("vehiculo_year", ""), "year", int),
            license_plate=form.get("vehiculo_license_plate", "").strip(),
            color=form.get("vehiculo_color", "").strip() or None,
            chassis_number=form.get("vehiculo_chassis_number", "").strip() or None,
            engine_number=form.get("vehiculo_engine_number", "").strip() or None,
        )
    vehicle_id = _parsear_numero(form.get("vehicle_id", ""), "vehicle_id", int)
    if vehicle_id is None:
        raise ValidationError("Falta elegir un vehículo.")
    return vehicle_id


def _datos_comunes_del_form():
    valor_aseguradora = request.form.get("insurance_company_id", "").strip()
    valor_tipo = request.form.get("claim_type_id", "").strip()
    return {
        "claim_status_id": _parsear_numero(request.form.get("claim_status_id", ""), "claim_status_id", int),
        "branch_id": _parsear_numero(request.form.get("branch_id", ""), "branch_id", int),
        "opened_date": (
            parsear_fecha_visual(request.form.get("opened_date", "").strip())
            if request.form.get("opened_date", "").strip() else None
        ),
        "description": request.form.get("description", "").strip() or None,
        "insurance_company_id": int(valor_aseguradora) if valor_aseguradora else None,
        "quitar_aseguradora": not valor_aseguradora,
        "claim_type_id": int(valor_tipo) if valor_tipo else None,
        "quitar_tipo": not valor_tipo,
    }


def _texto_cliente(cliente):
    return f"{cliente['last_name']}, {cliente['name']} ({cliente['dni_cuit']})"


def _texto_vehiculo(vehiculo):
    return f"{vehiculo['brand_name']} {vehiculo['model']} ({vehiculo['license_plate']})"


def _cliente_actual(siniestro, clientes):
    """(client_id, texto) para precargar el combobox: el cliente elegido, o el
    nombre tipeado si se estaba cargando uno nuevo cuando falló la validación."""
    if not siniestro:
        return "", ""
    client_id = siniestro.get("client_id")
    if client_id:
        for cliente in clientes:
            if str(cliente["id"]) == str(client_id):
                return str(cliente["id"]), _texto_cliente(cliente)
    if siniestro.get("modo_cliente") == "nuevo" and siniestro.get("cliente_name"):
        return "", f"{siniestro.get('cliente_last_name', '')}, {siniestro.get('cliente_name', '')}"
    return "", ""


def _vehiculo_actual(siniestro, vehiculos):
    if not siniestro:
        return "", ""
    vehicle_id = siniestro.get("vehicle_id")
    if vehicle_id:
        for vehiculo in vehiculos:
            if str(vehiculo["id"]) == str(vehicle_id):
                return str(vehiculo["id"]), _texto_vehiculo(vehiculo)
    if siniestro.get("modo_vehiculo") == "nuevo" and siniestro.get("vehiculo_model"):
        return "", siniestro.get("vehiculo_model", "")
    return "", ""


def _contexto_comun(accion, siniestro=None):
    clientes = listar_clientes(branch_ids=session.get("branch_ids"))
    vehiculos = listar_vehiculos(branch_ids=session.get("branch_ids"))
    cliente_id_actual, cliente_texto_actual = _cliente_actual(siniestro, clientes)
    vehiculo_id_actual, vehiculo_texto_actual = _vehiculo_actual(siniestro, vehiculos)
    return {
        "accion": accion,
        "clientes": clientes,
        "vehiculos": vehiculos,
        "marcas": listar_marcas(),
        "aseguradoras": listar_aseguradoras(),
        "tipos": listar_tipos(),
        "estados": listar_estados(),
        "sucursales": _sucursales_seleccionables(),
        "cliente_id_actual": cliente_id_actual,
        "cliente_texto_actual": cliente_texto_actual,
        "vehiculo_id_actual": vehiculo_id_actual,
        "vehiculo_texto_actual": vehiculo_texto_actual,
        "modo_cliente_actual": (siniestro.get("modo_cliente") if siniestro else None) or "existente",
        "modo_vehiculo_actual": (siniestro.get("modo_vehiculo") if siniestro else None) or "existente",
    }


@siniestros_bp.route("/")
@login_required
def listar():
    siniestros = listar_siniestros(branch_ids=session.get("branch_ids"))
    return render_template("siniestros/listar.html", siniestros=siniestros, migas=_migas())


@siniestros_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    if request.method == "POST":
        try:
            client_id = _resolver_cliente(request.form)
            vehicle_id = _resolver_vehiculo(request.form)
            datos = _datos_comunes_del_form()
            id_siniestro = crear_siniestro(
                client_id=client_id, vehicle_id=vehicle_id,
                claim_status_id=datos["claim_status_id"], branch_id=datos["branch_id"],
                opened_date=datos["opened_date"], insurance_company_id=datos["insurance_company_id"],
                claim_type_id=datos["claim_type_id"], description=datos["description"],
                changed_by_user_id=session.get("user_id"), changed_by_username=session.get("username"),
            )
        except RegistroBorradoExistente:
            flash(
                "Ya existe un cliente o vehículo borrado con esos datos. Reactivalo desde "
                "Clientes/Vehículos antes de cargar el siniestro.",
                "error",
            )
            return render_template(
                "siniestros/formulario.html", siniestro=dict(request.form),
                migas=_migas("Nuevo siniestro"), **_contexto_comun("nueva", siniestro=dict(request.form)),
            )
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "siniestros/formulario.html", siniestro=dict(request.form),
                migas=_migas("Nuevo siniestro"), **_contexto_comun("nueva", siniestro=dict(request.form)),
            )
        flash("Siniestro creado.", "success")
        return redirect(url_for("siniestros.editar", id_siniestro=id_siniestro))

    return render_template(
        "siniestros/formulario.html", siniestro=None,
        migas=_migas("Nuevo siniestro"), **_contexto_comun("nueva"),
    )


@siniestros_bp.route("/<int:id_siniestro>/editar", methods=["GET", "POST"])
@login_required
def editar(id_siniestro):
    siniestro = obtener_por_id(id_siniestro)
    if siniestro is None:
        flash("El siniestro no existe.", "error")
        return redirect(url_for("siniestros.listar"))

    redireccion = _requiere_acceso_al_siniestro(id_siniestro)
    if redireccion:
        return redireccion

    if request.method == "POST":
        try:
            client_id = _resolver_cliente(request.form)
            vehicle_id = _resolver_vehiculo(request.form)
            datos = _datos_comunes_del_form()
            actualizar_siniestro(
                id_siniestro, client_id=client_id, vehicle_id=vehicle_id,
                claim_status_id=datos["claim_status_id"], branch_id=datos["branch_id"],
                opened_date=datos["opened_date"], insurance_company_id=datos["insurance_company_id"],
                quitar_aseguradora=datos["quitar_aseguradora"],
                claim_type_id=datos["claim_type_id"], quitar_tipo=datos["quitar_tipo"],
                description=datos["description"],
                changed_by_user_id=session.get("user_id"), changed_by_username=session.get("username"),
            )
        except RegistroBorradoExistente:
            flash(
                "Ya existe un cliente o vehículo borrado con esos datos. Reactivalo desde "
                "Clientes/Vehículos antes de continuar.",
                "error",
            )
            return render_template(
                "siniestros/formulario.html", siniestro={**dict(request.form), "id": id_siniestro},
                migas=_migas("Editar siniestro"),
                **_contexto_comun("editar", siniestro={**dict(request.form), "id": id_siniestro}),
            )
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "siniestros/formulario.html", siniestro={**dict(request.form), "id": id_siniestro},
                migas=_migas("Editar siniestro"),
                **_contexto_comun("editar", siniestro={**dict(request.form), "id": id_siniestro}),
            )
        flash("Siniestro actualizado.", "success")
        return redirect(url_for("siniestros.editar", id_siniestro=id_siniestro))

    return render_template(
        "siniestros/formulario.html", siniestro=dict(siniestro),
        migas=_migas("Editar siniestro"), **_contexto_comun("editar", siniestro=dict(siniestro)),
    )


def _contexto_actividad():
    return {
        "estados": listar_estados(),
        "aseguradoras": listar_aseguradoras(),
        "tipos": listar_tipos(),
        "sucursales": _sucursales_seleccionables(),
    }


@siniestros_bp.route("/<int:id_siniestro>/actividad")
@login_required
def actividad(id_siniestro):
    siniestro = obtener_por_id(id_siniestro)
    if siniestro is None:
        flash("El siniestro no existe.", "error")
        return redirect(url_for("siniestros.listar"))

    redireccion = _requiere_acceso_al_siniestro(id_siniestro)
    if redireccion:
        return redireccion

    return render_template(
        "siniestros/actividad.html",
        siniestro=dict(siniestro),
        cliente=obtener_cliente_por_id(siniestro["client_id"]),
        vehiculo=obtener_vehiculo_por_id(siniestro["vehicle_id"]),
        actividad=listar_actividad(id_siniestro),
        migas=_migas("Actividad"),
        **_contexto_actividad(),
    )


@siniestros_bp.route("/<int:id_siniestro>/actividad/comentario", methods=["POST"])
@login_required
def agregar_comentario_view(id_siniestro):
    if obtener_por_id(id_siniestro) is None:
        flash("El siniestro no existe.", "error")
        return redirect(url_for("siniestros.listar"))

    redireccion = _requiere_acceso_al_siniestro(id_siniestro)
    if redireccion:
        return redireccion

    try:
        agregar_comentario(
            id_siniestro, request.form.get("comentario", ""),
            changed_by_user_id=session.get("user_id"), changed_by_username=session.get("username"),
        )
        flash("Observación agregada.", "success")
    except ValidationError as error:
        flash(str(error), "error")
    return redirect(url_for("siniestros.actividad", id_siniestro=id_siniestro))


@siniestros_bp.route("/<int:id_siniestro>/actividad/actualizar", methods=["POST"])
@login_required
def actualizar_rapido(id_siniestro):
    if obtener_por_id(id_siniestro) is None:
        flash("El siniestro no existe.", "error")
        return redirect(url_for("siniestros.listar"))

    redireccion = _requiere_acceso_al_siniestro(id_siniestro)
    if redireccion:
        return redireccion

    valor_aseguradora = request.form.get("insurance_company_id", "").strip()
    valor_tipo = request.form.get("claim_type_id", "").strip()
    try:
        actualizar_siniestro(
            id_siniestro,
            claim_status_id=_parsear_numero(request.form.get("claim_status_id", ""), "claim_status_id", int),
            branch_id=_parsear_numero(request.form.get("branch_id", ""), "branch_id", int),
            insurance_company_id=int(valor_aseguradora) if valor_aseguradora else None,
            quitar_aseguradora=not valor_aseguradora,
            claim_type_id=int(valor_tipo) if valor_tipo else None,
            quitar_tipo=not valor_tipo,
            changed_by_user_id=session.get("user_id"), changed_by_username=session.get("username"),
        )
        flash("Siniestro actualizado.", "success")
    except ValidationError as error:
        flash(str(error), "error")
    return redirect(url_for("siniestros.actividad", id_siniestro=id_siniestro))


@siniestros_bp.route("/<int:id_siniestro>/borrar", methods=["POST"])
@login_required
def borrar(id_siniestro):
    if obtener_por_id(id_siniestro) is None:
        flash("El siniestro no existe.", "error")
        return redirect(url_for("siniestros.listar"))

    redireccion = _requiere_acceso_al_siniestro(id_siniestro)
    if redireccion:
        return redireccion

    borrar_siniestro(id_siniestro)
    flash("Siniestro borrado.", "success")
    return redirect(url_for("siniestros.listar"))


@siniestros_bp.route("/borrados")
@login_required
@requiere_ver_eliminados
def borrados():
    siniestros = [s for s in listar_siniestros(incluir_borrados=True) if s["status"] == 0]
    return render_template("siniestros/borrados.html", siniestros=siniestros, migas=_migas("Borrados"))


@siniestros_bp.route("/<int:id_siniestro>/reactivar", methods=["POST"])
@login_required
def reactivar(id_siniestro):
    destino = "siniestros.borrados" if puede_ver_eliminados(session.get("role")) else "siniestros.listar"

    if obtener_por_id(id_siniestro) is None:
        flash("El siniestro no existe.", "error")
        return redirect(url_for(destino))

    redireccion = _requiere_acceso_al_siniestro(id_siniestro)
    if redireccion:
        return redireccion

    reactivar_siniestro(id_siniestro)
    flash("Siniestro reactivado.", "success")
    return redirect(url_for(destino))
