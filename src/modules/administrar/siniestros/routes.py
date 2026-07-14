from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from src.auth import login_required, requiere_ver_eliminados
from src.breadcrumbs import migas
from src.constants.validations import parsear_fecha_visual
from src.exceptions import RegistroBorradoExistente, ValidationError
from src.modules.administrar.branches.logic import listar_sucursales
from src.modules.administrar.clients.logic import crear_cliente, listar_clientes
from src.modules.administrar.siniestros.logic import (
    actualizar_siniestro,
    borrar_siniestro,
    crear_siniestro,
    listar_historial,
    listar_siniestros,
    obtener_por_id,
    reactivar_siniestro,
    visible_para_sucursales,
)
from src.modules.administrar.validaciones.claim_statuses.logic import listar_estados
from src.modules.administrar.validaciones.insurance_companies.logic import listar_aseguradoras
from src.modules.administrar.validaciones.vehicle_brands.logic import listar_marcas
from src.modules.administrar.vehicles.logic import crear_vehiculo, listar_vehiculos
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
    }


def _contexto_comun(accion):
    return {
        "accion": accion,
        "clientes": listar_clientes(branch_ids=session.get("branch_ids")),
        "vehiculos": listar_vehiculos(branch_ids=session.get("branch_ids")),
        "marcas": listar_marcas(),
        "aseguradoras": listar_aseguradoras(),
        "estados": listar_estados(),
        "sucursales": _sucursales_seleccionables(),
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
                description=datos["description"],
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
                migas=_migas("Nuevo siniestro"), **_contexto_comun("nueva"),
            )
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "siniestros/formulario.html", siniestro=dict(request.form),
                migas=_migas("Nuevo siniestro"), **_contexto_comun("nueva"),
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
                quitar_aseguradora=datos["quitar_aseguradora"], description=datos["description"],
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
                historial=listar_historial(id_siniestro),
                migas=_migas("Editar siniestro"), **_contexto_comun("editar"),
            )
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "siniestros/formulario.html", siniestro={**dict(request.form), "id": id_siniestro},
                historial=listar_historial(id_siniestro),
                migas=_migas("Editar siniestro"), **_contexto_comun("editar"),
            )
        flash("Siniestro actualizado.", "success")
        return redirect(url_for("siniestros.editar", id_siniestro=id_siniestro))

    return render_template(
        "siniestros/formulario.html", siniestro=dict(siniestro),
        historial=listar_historial(id_siniestro),
        migas=_migas("Editar siniestro"), **_contexto_comun("editar"),
    )


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
