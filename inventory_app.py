#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema Avanzado de Gestión de Inventario (Consola + SQLite)
-------------------------------------------------------------
Características:
- POO: clases Producto e Inventario
- Colecciones: diccionario para cache local (id -> Producto)
- CRUD completo sincronizado con SQLite
- Menú interactivo por consola

Uso:
    python inventory_app.py
"""

import sqlite3
from dataclasses import dataclass
from typing import Dict, List, Optional

DB_NAME = "inventario.db"

# =========================
#   MODELO DE DOMINIO
# =========================
@dataclass
class Producto:
    id: Optional[int]
    nombre: str
    cantidad: int
    precio: float

    def get_id(self) -> Optional[int]:
        return self.id

    def set_id(self, nuevo_id: int) -> None:
        self.id = nuevo_id

    def get_nombre(self) -> str:
        return self.nombre

    def set_nombre(self, nuevo_nombre: str) -> None:
        self.nombre = nuevo_nombre

    def get_cantidad(self) -> int:
        return self.cantidad

    def set_cantidad(self, nueva_cantidad: int) -> None:
        if nueva_cantidad < 0:
            raise ValueError("La cantidad no puede ser negativa.")
        self.cantidad = nueva_cantidad

    def get_precio(self) -> float:
        return self.precio

    def set_precio(self, nuevo_precio: float) -> None:
        if nuevo_precio < 0:
            raise ValueError("El precio no puede ser negativo.")
        self.precio = nuevo_precio

    def actualizar_cantidad(self, delta: int) -> None:
        nueva = self.cantidad + delta
        if nueva < 0:
            raise ValueError("La cantidad resultante no puede ser negativa.")
        self.cantidad = nueva

    def to_row(self) -> tuple:
        return (self.nombre, self.cantidad, self.precio)

# =========================
#        INVENTARIO
# =========================
class Inventario:
    def __init__(self, db_path: str = DB_NAME) -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._crear_tabla()
        self.productos: Dict[int, Producto] = {}
        self._cargar_cache()

    def _crear_tabla(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                cantidad INTEGER NOT NULL CHECK (cantidad >= 0),
                precio REAL NOT NULL CHECK (precio >= 0)
            )
            """
        )
        self.conn.commit()

    def _cargar_cache(self) -> None:
        self.productos.clear()
        for row in self.conn.execute("SELECT id, nombre, cantidad, precio FROM productos"):
            prod = Producto(id=row["id"], nombre=row["nombre"],
                            cantidad=row["cantidad"], precio=row["precio"])
            self.productos[prod.id] = prod

    def agregar(self, producto: Producto) -> int:
        cur = self.conn.execute(
            "INSERT INTO productos (nombre, cantidad, precio) VALUES (?, ?, ?)",
            producto.to_row(),
        )
        self.conn.commit()
        new_id = cur.lastrowid
        producto.set_id(new_id)
        self.productos[new_id] = producto
        return new_id

    def eliminar(self, prod_id: int) -> bool:
        cur = self.conn.execute("DELETE FROM productos WHERE id = ?", (prod_id,))
        self.conn.commit()
        eliminado = cur.rowcount > 0
        if eliminado:
            self.productos.pop(prod_id, None)
        return eliminado

    def actualizar(self, prod_id: int, *, nombre: Optional[str] = None,
                   cantidad: Optional[int] = None, precio: Optional[float] = None) -> bool:
        if prod_id not in self.productos:
            return False

        campos = []
        valores = []
        if nombre is not None:
            campos.append("nombre = ?")
            valores.append(nombre)
        if cantidad is not None:
            if cantidad < 0:
                raise ValueError("La cantidad no puede ser negativa.")
            campos.append("cantidad = ?")
            valores.append(cantidad)
        if precio is not None:
            if precio < 0:
                raise ValueError("El precio no puede ser negativo.")
            campos.append("precio = ?")
            valores.append(precio)

        if not campos:
            return False

        valores.append(prod_id)
        sql = f"UPDATE productos SET {', '.join(campos)} WHERE id = ?"
        cur = self.conn.execute(sql, tuple(valores))
        self.conn.commit()

        if cur.rowcount > 0:
            p = self.productos[prod_id]
            if nombre is not None:
                p.set_nombre(nombre)
            if cantidad is not None:
                p.set_cantidad(cantidad)
            if precio is not None:
                p.set_precio(precio)
            return True
        return False

    def buscar_por_nombre(self, texto: str) -> List[Producto]:
        patron = f"%{texto.strip()}%"
        filas = self.conn.execute(
            "SELECT id, nombre, cantidad, precio FROM productos WHERE nombre LIKE ? COLLATE NOCASE",
            (patron,),
        ).fetchall()
        return [Producto(row["id"], row["nombre"], row["cantidad"], row["precio"]) for row in filas]

    def listar_todos(self) -> List[Producto]:
        return list(self.productos.values())

    def cerrar(self) -> None:
        self.conn.close()

# =========================
#        UI CONSOLA
# =========================
def pedir_int(msg: str, *, minimo: Optional[int] = None) -> int:
    while True:
        try:
            valor = int(input(msg))
            if minimo is not None and valor < minimo:
                print(f"Debe ser ≥ {minimo}.")
                continue
            return valor
        except ValueError:
            print("Ingrese un número entero válido.")

def pedir_float(msg: str, *, minimo: Optional[float] = None) -> float:
    while True:
        try:
            valor = float(input(msg))
            if minimo is not None and valor < minimo:
                print(f"Debe ser ≥ {minimo}.")
                continue
            return valor
        except ValueError:
            print("Ingrese un número válido (use punto decimal).")

def menu() -> None:
    inv = Inventario()
    print("✅ Inventario listo. Base de datos:", inv.db_path)

    opciones = {
        "1": "Añadir producto",
        "2": "Eliminar producto por ID",
        "3": "Actualizar producto",
        "4": "Buscar por nombre",
        "5": "Mostrar todos",
        "0": "Salir",
    }

    try:
        while True:
            print("\n--- MENÚ INVENTARIO ---")
            for k, v in opciones.items():
                print(f"[{k}] {v}")
            op = input("Elija opción: ").strip()

            if op == "1":
                nombre = input("Nombre: ").strip()
                cantidad = pedir_int("Cantidad: ", minimo=0)
                precio = pedir_float("Precio: ", minimo=0)
                prod = Producto(id=None, nombre=nombre, cantidad=cantidad, precio=precio)
                new_id = inv.agregar(prod)
                print(f"✔ Producto añadido con ID {new_id}.")

            elif op == "2":
                pid = pedir_int("ID a eliminar: ", minimo=1)
                if inv.eliminar(pid):
                    print("✔ Eliminado.")
                else:
                    print("✖ No existe ese ID.")

            elif op == "3":
                pid = pedir_int("ID a actualizar: ", minimo=1)
                if pid not in inv.productos:
                    print("✖ No existe ese ID.")
                    continue
                print("Deje vacío para no cambiar.")
                nombre = input("Nuevo nombre: ").strip()
                cantidad_txt = input("Nueva cantidad: ").strip()
                precio_txt = input("Nuevo precio: ").strip()

                kwargs = {}
                if nombre:
                    kwargs["nombre"] = nombre
                if cantidad_txt:
                    try:
                        kwargs["cantidad"] = int(cantidad_txt)
                    except ValueError:
                        print("Cantidad inválida. Se ignora.")
                if precio_txt:
                    try:
                        kwargs["precio"] = float(precio_txt)
                    except ValueError:
                        print("Precio inválido. Se ignora.")

                if inv.actualizar(pid, **kwargs):
                    print("✔ Actualizado.")
                else:
                    print("✖ No se realizó ningún cambio.")

            elif op == "4":
                q = input("Texto a buscar: ").strip()
                resultados = inv.buscar_por_nombre(q)
                if not resultados:
                    print("No se encontraron productos.")
                else:
                    print(f"{len(resultados)} resultado(s):")
                    for p in resultados:
                        print(f"- ID={p.id} | {p.nombre} | Cant={p.cantidad} | Precio={p.precio:.2f}")

            elif op == "5":
                items = inv.listar_todos()
                if not items:
                    print("Inventario vacío.")
                else:
                    print("Productos en inventario:")
                    for p in items:
                        print(f"- ID={p.id} | {p.nombre} | Cant={p.cantidad} | Precio={p.precio:.2f}")

            elif op == "0":
                print("Hasta pronto 👋")
                break
            else:
                print("Opción inválida.")
    finally:
        inv.cerrar()

if __name__ == '__main__':
    menu()


#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema Avanzado de Gestión de Inventario (Consola + SQLite)
-------------------------------------------------------------
Características:
- POO: clases Producto e Inventario
- Colecciones: diccionario para cache local (id -> Producto)
- CRUD completo sincronizado con SQLite
- Menú interactivo por consola

Uso:
    python inventory_app.py
"""

import sqlite3
from dataclasses import dataclass
from typing import Dict, List, Optional

DB_NAME = "inventario.db"

# =========================
#   MODELO DE DOMINIO
# =========================
@dataclass
class Producto:
    id: Optional[int]
    nombre: str
    cantidad: int
    precio: float

    def get_id(self) -> Optional[int]:
        return self.id

    def set_id(self, nuevo_id: int) -> None:
        self.id = nuevo_id

    def get_nombre(self) -> str:
        return self.nombre

    def set_nombre(self, nuevo_nombre: str) -> None:
        self.nombre = nuevo_nombre

    def get_cantidad(self) -> int:
        return self.cantidad

    def set_cantidad(self, nueva_cantidad: int) -> None:
        if nueva_cantidad < 0:
            raise ValueError("La cantidad no puede ser negativa.")
        self.cantidad = nueva_cantidad

    def get_precio(self) -> float:
        return self.precio

    def set_precio(self, nuevo_precio: float) -> None:
        if nuevo_precio < 0:
            raise ValueError("El precio no puede ser negativo.")
        self.precio = nuevo_precio

    def actualizar_cantidad(self, delta: int) -> None:
        nueva = self.cantidad + delta
        if nueva < 0:
            raise ValueError("La cantidad resultante no puede ser negativa.")
        self.cantidad = nueva

    def to_row(self) -> tuple:
        return (self.nombre, self.cantidad, self.precio)

# =========================
#        INVENTARIO
# =========================
class Inventario:
    def __init__(self, db_path: str = DB_NAME) -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._crear_tabla()
        self.productos: Dict[int, Producto] = {}
        self._cargar_cache()

    def _crear_tabla(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                cantidad INTEGER NOT NULL CHECK (cantidad >= 0),
                precio REAL NOT NULL CHECK (precio >= 0)
            )
            """
        )
        self.conn.commit()

    def _cargar_cache(self) -> None:
        self.productos.clear()
        for row in self.conn.execute("SELECT id, nombre, cantidad, precio FROM productos"):
            prod = Producto(id=row["id"], nombre=row["nombre"],
                            cantidad=row["cantidad"], precio=row["precio"])
            self.productos[prod.id] = prod

    def agregar(self, producto: Producto) -> int:
        cur = self.conn.execute(
            "INSERT INTO productos (nombre, cantidad, precio) VALUES (?, ?, ?)",
            producto.to_row(),
        )
        self.conn.commit()
        new_id = cur.lastrowid
        producto.set_id(new_id)
        self.productos[new_id] = producto
        return new_id

    def eliminar(self, prod_id: int) -> bool:
        cur = self.conn.execute("DELETE FROM productos WHERE id = ?", (prod_id,))
        self.conn.commit()
        eliminado = cur.rowcount > 0
        if eliminado:
            self.productos.pop(prod_id, None)
        return eliminado

    def actualizar(self, prod_id: int, *, nombre: Optional[str] = None,
                   cantidad: Optional[int] = None, precio: Optional[float] = None) -> bool:
        if prod_id not in self.productos:
            return False

        campos = []
        valores = []
        if nombre is not None:
            campos.append("nombre = ?")
            valores.append(nombre)
        if cantidad is not None:
            if cantidad < 0:
                raise ValueError("La cantidad no puede ser negativa.")
            campos.append("cantidad = ?")
            valores.append(cantidad)
        if precio is not None:
            if precio < 0:
                raise ValueError("El precio no puede ser negativo.")
            campos.append("precio = ?")
            valores.append(precio)

        if not campos:
            return False

        valores.append(prod_id)
        sql = f"UPDATE productos SET {', '.join(campos)} WHERE id = ?"
        cur = self.conn.execute(sql, tuple(valores))
        self.conn.commit()

        if cur.rowcount > 0:
            p = self.productos[prod_id]
            if nombre is not None:
                p.set_nombre(nombre)
            if cantidad is not None:
                p.set_cantidad(cantidad)
            if precio is not None:
                p.set_precio(precio)
            return True
        return False

    def buscar_por_nombre(self, texto: str) -> List[Producto]:
        patron = f"%{texto.strip()}%"
        filas = self.conn.execute(
            "SELECT id, nombre, cantidad, precio FROM productos WHERE nombre LIKE ? COLLATE NOCASE",
            (patron,),
        ).fetchall()
        return [Producto(row["id"], row["nombre"], row["cantidad"], row["precio"]) for row in filas]

    def listar_todos(self) -> List[Producto]:
        return list(self.productos.values())

    def cerrar(self) -> None:
        self.conn.close()

# =========================
#        UI CONSOLA
# =========================
def pedir_int(msg: str, *, minimo: Optional[int] = None) -> int:
    while True:
        try:
            valor = int(input(msg))
            if minimo is not None and valor < minimo:
                print(f"Debe ser ≥ {minimo}.")
                continue
            return valor
        except ValueError:
            print("Ingrese un número entero válido.")

def pedir_float(msg: str, *, minimo: Optional[float] = None) -> float:
    while True:
        try:
            valor = float(input(msg))
            if minimo is not None and valor < minimo:
                print(f"Debe ser ≥ {minimo}.")
                continue
            return valor
        except ValueError:
            print("Ingrese un número válido (use punto decimal).")

def menu() -> None:
    inv = Inventario()
    print("✅ Inventario listo. Base de datos:", inv.db_path)

    opciones = {
        "1": "Añadir producto",
        "2": "Eliminar producto por ID",
        "3": "Actualizar producto",
        "4": "Buscar por nombre",
        "5": "Mostrar todos",
        "0": "Salir",
    }

    try:
        while True:
            print("\n--- MENÚ INVENTARIO ---")
            for k, v in opciones.items():
                print(f"[{k}] {v}")
            op = input("Elija opción: ").strip()

            if op == "1":
                nombre = input("Nombre: ").strip()
                cantidad = pedir_int("Cantidad: ", minimo=0)
                precio = pedir_float("Precio: ", minimo=0)
                prod = Producto(id=None, nombre=nombre, cantidad=cantidad, precio=precio)
                new_id = inv.agregar(prod)
                print(f"✔ Producto añadido con ID {new_id}.")

            elif op == "2":
                pid = pedir_int("ID a eliminar: ", minimo=1)
                if inv.eliminar(pid):
                    print("✔ Eliminado.")
                else:
                    print("✖ No existe ese ID.")

            elif op == "3":
                pid = pedir_int("ID a actualizar: ", minimo=1)
                if pid not in inv.productos:
                    print("✖ No existe ese ID.")
                    continue
                print("Deje vacío para no cambiar.")
                nombre = input("Nuevo nombre: ").strip()
                cantidad_txt = input("Nueva cantidad: ").strip()
                precio_txt = input("Nuevo precio: ").strip()

                kwargs = {}
                if nombre:
                    kwargs["nombre"] = nombre
                if cantidad_txt:
                    try:
                        kwargs["cantidad"] = int(cantidad_txt)
                    except ValueError:
                        print("Cantidad inválida. Se ignora.")
                if precio_txt:
                    try:
                        kwargs["precio"] = float(precio_txt)
                    except ValueError:
                        print("Precio inválido. Se ignora.")

                if inv.actualizar(pid, **kwargs):
                    print("✔ Actualizado.")
                else:
                    print("✖ No se realizó ningún cambio.")

            elif op == "4":
                q = input("Texto a buscar: ").strip()
                resultados = inv.buscar_por_nombre(q)
                if not resultados:
                    print("No se encontraron productos.")
                else:
                    print(f"{len(resultados)} resultado(s):")
                    for p in resultados:
                        print(f"- ID={p.id} | {p.nombre} | Cant={p.cantidad} | Precio={p.precio:.2f}")

            elif op == "5":
                items = inv.listar_todos()
                if not items:
                    print("Inventario vacío.")
                else:
                    print("Productos en inventario:")
                    for p in items:
                        print(f"- ID={p.id} | {p.nombre} | Cant={p.cantidad} | Precio={p.precio:.2f}")

            elif op == "0":
                print("Hasta pronto 👋")
                break
            else:
                print("Opción inválida.")
    finally:
        inv.cerrar()

if __name__ == '__main__':
    menu()

