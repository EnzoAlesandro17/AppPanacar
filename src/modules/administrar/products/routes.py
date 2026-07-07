from flask import Blueprint, flash, redirect, render_template, request, url_for

from src.auth import login_required
from src.exceptions import ValidationError
from src.modules.administrar.products.logic import (
    actualizar_producto,
    borrar_producto,
    crear_producto,
    listar_productos,
    obtener_por_id,
    reactivar_producto,
)

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
            crear_producto(**datos)
        except ValidationError as error:
            flash(str(error))
            return render_template("products/formulario.html", producto=dict(request.form), accion="nueva")
        flash("Producto creado.")
        return redirect(url_for("products.listar"))

    return render_template("products/formulario.html", producto=None, accion="nueva")


@products_bp.route("/<int:id_producto>/editar", methods=["GET", "POST"])
@login_required
def editar(id_producto):
    producto = obtener_por_id(id_producto)
    if producto is None:
        flash("El producto no existe.")
        return redirect(url_for("products.listar"))

    if request.method == "POST":
        try:
            datos = _datos_del_form()
            actualizar_producto(id_producto, **datos)
        except ValidationError as error:
            flash(str(error))
            return render_template(
                "products/formulario.html", producto=dict(request.form), accion="editar"
            )
        flash("Producto actualizado.")
        return redirect(url_for("products.listar"))

    return render_template("products/formulario.html", producto=dict(producto), accion="editar")


@products_bp.route("/<int:id_producto>/borrar", methods=["POST"])
@login_required
def borrar(id_producto):
    if obtener_por_id(id_producto) is None:
        flash("El producto no existe.")
        return redirect(url_for("products.listar"))

    borrar_producto(id_producto)
    flash("Producto borrado.")
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
        flash("El producto no existe.")
        return redirect(url_for("products.borrados"))

    reactivar_producto(id_producto)
    flash("Producto reactivado.")
    return redirect(url_for("products.borrados"))
