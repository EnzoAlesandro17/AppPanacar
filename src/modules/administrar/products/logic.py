import sqlite3

from src.constants.validations import validar_campos_obligatorios
from src.db.connection import obtener_conexion
from src.exceptions import ValidationError
from src.modules.administrar.products.db import TABLA


def _validar_stock(stock):
    """stock en None es válido: significa que el producto no maneja stock (ej: E-SIM)."""
    if stock is None:
        return
    if not isinstance(stock, int) or isinstance(stock, bool) or stock < 0:
        raise ValidationError("stock debe ser un número entero mayor o igual a 0, o None si no aplica.")


def _validar_precios(wholesale_price, retail_price):
    for etiqueta, valor in (("wholesale_price", wholesale_price), ("retail_price", retail_price)):
        if valor is None:
            raise ValidationError(f"Falta {etiqueta}")
        if not isinstance(valor, (int, float)) or isinstance(valor, bool) or valor < 0:
            raise ValidationError(f"{etiqueta} debe ser un número mayor o igual a 0.")

    if retail_price < wholesale_price:
        raise ValidationError(
            "retail_price no puede ser menor a wholesale_price."
        )


def _validar_datos(code, name, category, brand, description, stock, wholesale_price, retail_price):
    validar_campos_obligatorios({
        "code": code,
        "name": name,
        "category": category,
        "brand": brand,
        "description": description,
    })
    _validar_stock(stock)
    _validar_precios(wholesale_price, retail_price)


def _traducir_error_integridad(error):
    mensaje = str(error)
    if "code" in mensaje:
        return ValidationError("Ya existe un producto con ese code.")
    return ValidationError("Ya existe un producto con alguno de esos datos únicos.")


def crear_producto(code, name, category, brand, description, stock, wholesale_price, retail_price):
    """Valida y crea un producto nuevo. Devuelve el id generado."""
    _validar_datos(code, name, category, brand, description, stock, wholesale_price, retail_price)

    with obtener_conexion() as conexion:
        try:
            cursor = conexion.execute(
                f"""
                INSERT INTO {TABLA}
                    (code, name, category, brand, description, stock, wholesale_price, retail_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (code, name, category, brand, description, stock, wholesale_price, retail_price),
            )
            conexion.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError as error:
            raise _traducir_error_integridad(error) from error


def obtener_por_id(id_producto):
    with obtener_conexion() as conexion:
        return conexion.execute(f"SELECT * FROM {TABLA} WHERE id = ?", (id_producto,)).fetchone()


def obtener_por_code(code):
    with obtener_conexion() as conexion:
        return conexion.execute(f"SELECT * FROM {TABLA} WHERE code = ?", (code,)).fetchone()


def listar_productos(incluir_borrados=False):
    consulta = f"SELECT * FROM {TABLA}"
    if not incluir_borrados:
        consulta += " WHERE status = 1"
    consulta += " ORDER BY name"

    with obtener_conexion() as conexion:
        return conexion.execute(consulta).fetchall()


def buscar_por_nombre(texto):
    """Busca productos activos por coincidencia parcial en el nombre."""
    patron = f"%{texto}%"
    with obtener_conexion() as conexion:
        return conexion.execute(
            f"""
            SELECT * FROM {TABLA}
            WHERE status = 1 AND name LIKE ?
            ORDER BY name
            """,
            (patron,),
        ).fetchall()


def actualizar_producto(id_producto, code=None, name=None, category=None, brand=None,
                         description=None, stock=None, wholesale_price=None, retail_price=None):
    """Actualiza los campos recibidos; los que se pasan en None mantienen su valor actual."""
    producto_actual = obtener_por_id(id_producto)
    if producto_actual is None:
        raise ValidationError("El producto no existe.")

    nuevos = {
        "code": code if code is not None else producto_actual["code"],
        "name": name if name is not None else producto_actual["name"],
        "category": category if category is not None else producto_actual["category"],
        "brand": brand if brand is not None else producto_actual["brand"],
        "description": description if description is not None else producto_actual["description"],
        "stock": stock if stock is not None else producto_actual["stock"],
        "wholesale_price": wholesale_price if wholesale_price is not None else producto_actual["wholesale_price"],
        "retail_price": retail_price if retail_price is not None else producto_actual["retail_price"],
    }

    _validar_datos(
        nuevos["code"], nuevos["name"], nuevos["category"], nuevos["brand"],
        nuevos["description"], nuevos["stock"], nuevos["wholesale_price"], nuevos["retail_price"],
    )

    with obtener_conexion() as conexion:
        try:
            conexion.execute(
                f"""
                UPDATE {TABLA}
                SET code = ?, name = ?, category = ?, brand = ?, description = ?,
                    stock = ?, wholesale_price = ?, retail_price = ?
                WHERE id = ?
                """,
                (
                    nuevos["code"], nuevos["name"], nuevos["category"], nuevos["brand"],
                    nuevos["description"], nuevos["stock"], nuevos["wholesale_price"],
                    nuevos["retail_price"], id_producto,
                ),
            )
            conexion.commit()
        except sqlite3.IntegrityError as error:
            raise _traducir_error_integridad(error) from error


def aumentar_stock(id_producto, cantidad):
    """Suma cantidad al stock actual (ej: entrada de mercadería por compra)."""
    if not isinstance(cantidad, int) or isinstance(cantidad, bool) or cantidad <= 0:
        raise ValidationError("cantidad debe ser un número entero mayor a 0.")

    producto = obtener_por_id(id_producto)
    if producto is None:
        raise ValidationError("El producto no existe.")
    if producto["stock"] is None:
        raise ValidationError("Este producto no maneja stock (ej: E-SIM).")

    with obtener_conexion() as conexion:
        conexion.execute(
            f"UPDATE {TABLA} SET stock = stock + ? WHERE id = ?", (cantidad, id_producto)
        )
        conexion.commit()


def disminuir_stock(id_producto, cantidad):
    """Resta cantidad al stock actual (ej: salida por venta). No permite que quede negativo."""
    if not isinstance(cantidad, int) or isinstance(cantidad, bool) or cantidad <= 0:
        raise ValidationError("cantidad debe ser un número entero mayor a 0.")

    producto = obtener_por_id(id_producto)
    if producto is None:
        raise ValidationError("El producto no existe.")
    if producto["stock"] is None:
        raise ValidationError("Este producto no maneja stock (ej: E-SIM).")
    if producto["stock"] < cantidad:
        raise ValidationError(
            f"Stock insuficiente: hay {producto['stock']} y se quieren restar {cantidad}."
        )

    with obtener_conexion() as conexion:
        conexion.execute(
            f"UPDATE {TABLA} SET stock = stock - ? WHERE id = ?", (cantidad, id_producto)
        )
        conexion.commit()


def borrar_producto(id_producto):
    """Borrado lógico: marca status = 0 en vez de eliminar la fila."""
    with obtener_conexion() as conexion:
        conexion.execute(f"UPDATE {TABLA} SET status = 0 WHERE id = ?", (id_producto,))
        conexion.commit()


def reactivar_producto(id_producto):
    """Revierte un borrado lógico: vuelve a marcar status = 1."""
    with obtener_conexion() as conexion:
        conexion.execute(f"UPDATE {TABLA} SET status = 1 WHERE id = ?", (id_producto,))
        conexion.commit()
