from flask import Blueprint, flash, redirect, render_template, request, url_for

from src.auth import login_required
from src.exceptions import ValidationError
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
    reactivar_producto,
)
from src.modules.administrar.validaciones.vehicle_brands.logic import listar_marcas

products_bp = Blueprint("products", __name__, url_prefix="/products")


def _parsear_numero(valor, campo, tipo):
    valor = valor.strip()
    if not valor:
        return None
    try:
        return tipo(valor)
    except ValueError:
        raise ValidationError(f"{campo} debe ser un número.")


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
        "purchase_date": request.form.get("purchase_date", "").strip() or None,
        "purchase_price": _parsear_numero(request.form.get("purchase_price", ""), "purchase_price", float),
    }


@products_bp.route("/")
@login_required
def listar():
    productos = listar_productos()
    return render_template("products/listar.html", productos=productos)


@products_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    if request.method == "POST":
        try:
            datos = _datos_del_form()
            id_producto = crear_producto(**datos)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "products/formulario.html", producto=dict(request.form), accion="nueva",
                product_types=PRODUCT_TYPES, conditions=CONDITIONS, sides=SIDES,
            )
        flash("Producto creado.", "success")
        return redirect(url_for("products.editar", id_producto=id_producto))

    return render_template(
        "products/formulario.html", producto=None, accion="nueva",
        product_types=PRODUCT_TYPES, conditions=CONDITIONS, sides=SIDES,
    )


@products_bp.route("/<int:id_producto>/editar", methods=["GET", "POST"])
@login_required
def editar(id_producto):
    producto = obtener_por_id(id_producto)
    if producto is None:
        flash("El producto no existe.", "error")
        return redirect(url_for("products.listar"))

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
                marcas=listar_marcas(),
            )
        flash("Producto actualizado.", "success")
        return redirect(url_for("products.editar", id_producto=id_producto))

    return render_template(
        "products/formulario.html", producto=dict(producto), accion="editar",
        product_types=PRODUCT_TYPES, conditions=CONDITIONS, sides=SIDES,
        compatibilidades=listar_compatibilidad(id_producto), id_producto=id_producto,
        marcas=listar_marcas(),
    )


@products_bp.route("/<int:id_producto>/borrar", methods=["POST"])
@login_required
def borrar(id_producto):
    if obtener_por_id(id_producto) is None:
        flash("El producto no existe.", "error")
        return redirect(url_for("products.listar"))

    borrar_producto(id_producto)
    flash("Producto borrado.", "success")
    return redirect(url_for("products.listar"))


@products_bp.route("/borrados")
@login_required
def borrados():
    productos = [p for p in listar_productos(incluir_borrados=True) if p["status"] == 0]
    return render_template("products/borrados.html", productos=productos)


@products_bp.route("/<int:id_producto>/reactivar", methods=["POST"])
@login_required
def reactivar(id_producto):
    if obtener_por_id(id_producto) is None:
        flash("El producto no existe.", "error")
        return redirect(url_for("products.borrados"))

    reactivar_producto(id_producto)
    flash("Producto reactivado.", "success")
    return redirect(url_for("products.borrados"))


@products_bp.route("/<int:id_producto>/compatibilidad", methods=["POST"])
@login_required
def agregar_compatibilidad_ruta(id_producto):
    if obtener_por_id(id_producto) is None:
        flash("El producto no existe.", "error")
        return redirect(url_for("products.listar"))

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
