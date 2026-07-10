from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from src.auth import login_required, requiere_ver_eliminados
from src.breadcrumbs import migas
from src.constants.validations import parsear_fecha_visual
from src.exceptions import RegistroBorradoExistente, ValidationError
from src.modules.administrar.branches.logic import listar_sucursales
from src.modules.administrar.products.logic import (
    CONDITIONS,
    PRODUCT_TYPES,
    SIDES,
    actualizar_producto,
    agregar_compatibilidad,
    borrar_compatibilidad,
    borrar_producto,
    crear_producto,
    listar_compatibilidad,
    listar_productos,
    obtener_por_id,
    obtener_sucursales_ids_producto,
    reactivar_producto,
    visible_para_sucursales,
)
from src.modules.administrar.validaciones.vehicle_brands.logic import listar_marcas
from src.permissions import puede_ver_eliminados

products_bp = Blueprint("products", __name__, url_prefix="/stock")


def _migas(*ultimos):
    piezas = [("Sistema de gestión", "administrar.index")]
    piezas.append(("Stock", "products.listar") if ultimos else "Stock")
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


def _branch_ids_del_form():
    return [int(valor) for valor in request.form.getlist("branch_ids") if valor.strip()]


def _sucursales_seleccionables():
    """IT puede asignar cualquier sucursal; los demás roles solo las propias."""
    if session.get("role") == "IT":
        return listar_sucursales()
    propias = set(session.get("branch_ids") or [])
    return [sucursal for sucursal in listar_sucursales() if sucursal["id"] in propias]


def _requiere_acceso_al_producto(id_producto):
    """None si el producto es visible para las sucursales de la sesión; si no, un redirect listo para devolver."""
    if not visible_para_sucursales(id_producto, session.get("branch_ids")):
        flash("No tenés acceso a ese producto.", "error")
        return redirect(url_for("products.listar"))
    return None


def _datos_del_form():
    return {
        "code": request.form.get("code", "").strip(),
        "name": request.form.get("name", "").strip(),
        "category": request.form.get("category", "").strip(),
        "brand": request.form.get("brand", "").strip(),
        "description": request.form.get("description", "").strip(),
        "stock": _parsear_numero(request.form.get("stock", ""), "stock", int),
        "wholesale_price": _parsear_numero(request.form.get("wholesale_price", ""), "wholesale_price", float),
        "retail_price": _parsear_numero(request.form.get("retail_price", ""), "retail_price", float),
        "product_type": request.form.get("product_type", "").strip(),
        "oem_code": request.form.get("oem_code", "").strip() or None,
        "side": request.form.get("side", "").strip() or None,
        "condition": request.form.get("condition", "").strip() or None,
        "supplier": request.form.get("supplier", "").strip() or None,
        "location": request.form.get("location", "").strip() or None,
        "purchase_date": (
            parsear_fecha_visual(request.form.get("purchase_date", "").strip())
            if request.form.get("purchase_date", "").strip() else None
        ),
        "purchase_price": _parsear_numero(request.form.get("purchase_price", ""), "purchase_price", float),
        "branch_ids": _branch_ids_del_form(),
    }


@products_bp.route("/")
@login_required
def listar():
    productos = listar_productos(branch_ids=session.get("branch_ids"))
    return render_template("products/listar.html", productos=productos, migas=_migas())


@products_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    sucursales = _sucursales_seleccionables()

    if request.method == "POST":
        try:
            datos = _datos_del_form()
            id_producto = crear_producto(**datos)
        except RegistroBorradoExistente as error:
            borrado_existente_id = None
            if visible_para_sucursales(error.id_existente, session.get("branch_ids")):
                flash(
                    "Ya existe un producto borrado con ese code. Podés reactivarlo en vez de crear uno nuevo.",
                    "error",
                )
                borrado_existente_id = error.id_existente
            else:
                flash("Ya existe un producto con ese code.", "error")
            return render_template(
                "products/formulario.html", producto=dict(request.form), accion="nueva",
                product_types=PRODUCT_TYPES, conditions=CONDITIONS, sides=SIDES,
                sucursales=sucursales, sucursales_seleccionadas=_branch_ids_del_form(),
                borrado_existente_id=borrado_existente_id, migas=_migas("Nuevo producto"),
            )
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "products/formulario.html", producto=dict(request.form), accion="nueva",
                product_types=PRODUCT_TYPES, conditions=CONDITIONS, sides=SIDES,
                sucursales=sucursales, sucursales_seleccionadas=_branch_ids_del_form(),
                migas=_migas("Nuevo producto"),
            )
        flash("Producto creado.", "success")
        return redirect(url_for("products.editar", id_producto=id_producto))

    return render_template(
        "products/formulario.html", producto=None, accion="nueva",
        product_types=PRODUCT_TYPES, conditions=CONDITIONS, sides=SIDES,
        sucursales=sucursales, sucursales_seleccionadas=[], migas=_migas("Nuevo producto"),
    )


@products_bp.route("/<int:id_producto>/editar", methods=["GET", "POST"])
@login_required
def editar(id_producto):
    producto = obtener_por_id(id_producto)
    if producto is None:
        flash("El producto no existe.", "error")
        return redirect(url_for("products.listar"))

    redireccion = _requiere_acceso_al_producto(id_producto)
    if redireccion:
        return redireccion

    sucursales = _sucursales_seleccionables()

    if request.method == "POST":
        try:
            datos = _datos_del_form()
            actualizar_producto(id_producto, **datos)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "products/formulario.html", producto=dict(request.form), accion="editar",
                product_types=PRODUCT_TYPES, conditions=CONDITIONS, sides=SIDES,
                compatibilidades=listar_compatibilidad(id_producto), id_producto=id_producto,
                marcas=listar_marcas(), sucursales=sucursales,
                sucursales_seleccionadas=_branch_ids_del_form(),
                migas=_migas("Editar producto"),
            )
        flash("Producto actualizado.", "success")
        return redirect(url_for("products.editar", id_producto=id_producto))

    return render_template(
        "products/formulario.html", producto=dict(producto), accion="editar",
        product_types=PRODUCT_TYPES, conditions=CONDITIONS, sides=SIDES,
        compatibilidades=listar_compatibilidad(id_producto), id_producto=id_producto,
        marcas=listar_marcas(), sucursales=sucursales,
        sucursales_seleccionadas=obtener_sucursales_ids_producto(id_producto),
        migas=_migas("Editar producto"),
    )


@products_bp.route("/<int:id_producto>/borrar", methods=["POST"])
@login_required
def borrar(id_producto):
    if obtener_por_id(id_producto) is None:
        flash("El producto no existe.", "error")
        return redirect(url_for("products.listar"))

    redireccion = _requiere_acceso_al_producto(id_producto)
    if redireccion:
        return redireccion

    borrar_producto(id_producto)
    flash("Producto borrado.", "success")
    return redirect(url_for("products.listar"))


@products_bp.route("/borrados")
@login_required
@requiere_ver_eliminados
def borrados():
    productos = [p for p in listar_productos(incluir_borrados=True) if p["status"] == 0]
    return render_template("products/borrados.html", productos=productos, migas=_migas("Borrados"))


@products_bp.route("/<int:id_producto>/reactivar", methods=["POST"])
@login_required
def reactivar(id_producto):
    destino = "products.borrados" if puede_ver_eliminados(session.get("role")) else "products.listar"

    if obtener_por_id(id_producto) is None:
        flash("El producto no existe.", "error")
        return redirect(url_for(destino))

    redireccion = _requiere_acceso_al_producto(id_producto)
    if redireccion:
        return redireccion

    reactivar_producto(id_producto)
    flash("Producto reactivado.", "success")
    return redirect(url_for(destino))


@products_bp.route("/<int:id_producto>/compatibilidad", methods=["POST"])
@login_required
def agregar_compatibilidad_ruta(id_producto):
    if obtener_por_id(id_producto) is None:
        flash("El producto no existe.", "error")
        return redirect(url_for("products.listar"))

    redireccion = _requiere_acceso_al_producto(id_producto)
    if redireccion:
        return redireccion

    brand_vehicle_id = _parsear_numero(request.form.get("brand_vehicle_id", ""), "brand_vehicle_id", int)
    model = request.form.get("model", "").strip()
    year = _parsear_numero(request.form.get("year", ""), "year", int)

    try:
        agregar_compatibilidad(id_producto, brand_vehicle_id, model, year)
    except ValidationError as error:
        flash(str(error), "error")
    else:
        flash("Compatibilidad agregada.", "success")

    return redirect(url_for("products.editar", id_producto=id_producto))


@products_bp.route("/<int:id_producto>/compatibilidad/<int:id_compatibilidad>/borrar", methods=["POST"])
@login_required
def borrar_compatibilidad_ruta(id_producto, id_compatibilidad):
    borrar_compatibilidad(id_compatibilidad)
    flash("Compatibilidad eliminada.", "success")
    return redirect(url_for("products.editar", id_producto=id_producto))
