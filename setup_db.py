"""
============================================================
DataDialogue AI — Fase 1
setup_db.py: Crea y puebla la base de datos banco.db (SQLite)
============================================================
Ejecutar: python setup_db.py
"""

import sqlite3
import os

DB_PATH = "banco.db"

def crear_base_de_datos():
    # Eliminar BD previa si existe
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Base de datos anterior '{DB_PATH}' eliminada.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # ── TABLAS ─────────────────────────────────────────────
    cursor.executescript("""
    CREATE TABLE ciudad (
        id_ciudad   INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_ciudad TEXT NOT NULL,
        departamento  TEXT NOT NULL
    );

    CREATE TABLE clientes (
        id_cliente       INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre           TEXT    NOT NULL,
        apellido         TEXT    NOT NULL,
        documento        TEXT    NOT NULL UNIQUE,
        fecha_nacimiento TEXT    NOT NULL,
        id_ciudad        INTEGER NOT NULL,
        telefono         TEXT,
        correo           TEXT,
        FOREIGN KEY (id_ciudad) REFERENCES ciudad(id_ciudad)
    );

    CREATE TABLE cuentas (
        id_cuenta      INTEGER PRIMARY KEY AUTOINCREMENT,
        id_cliente     INTEGER NOT NULL,
        tipo_cuenta    TEXT    NOT NULL,
        saldo          REAL    NOT NULL,
        fecha_apertura TEXT    NOT NULL,
        estado         TEXT    NOT NULL,
        FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
    );

    CREATE TABLE movimientos (
        id_movimiento    INTEGER PRIMARY KEY AUTOINCREMENT,
        id_cuenta        INTEGER NOT NULL,
        fecha_movimiento TEXT    NOT NULL,
        tipo_movimiento  TEXT    NOT NULL,
        valor            REAL    NOT NULL,
        descripcion      TEXT,
        FOREIGN KEY (id_cuenta) REFERENCES cuentas(id_cuenta)
    );
    """)

    # ── DATOS ──────────────────────────────────────────────
    cursor.executemany(
        "INSERT INTO ciudad (nombre_ciudad, departamento) VALUES (?, ?)",
        [
            ("Bogotá",     "Cundinamarca"),
            ("Medellín",   "Antioquia"),
            ("Cali",       "Valle del Cauca"),
            ("Manizales",  "Caldas"),
        ]
    )

    cursor.executemany(
        """INSERT INTO clientes
           (nombre, apellido, documento, fecha_nacimiento, id_ciudad, telefono, correo)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        [
            ("Ana",   "Gómez",    "1001", "1990-05-10", 1, "3001111111", "ana@correo.com"),
            ("Luis",  "Martínez", "1002", "1988-07-21", 2, "3002222222", "luis@correo.com"),
            ("Carla", "Ramírez",  "1003", "1995-03-14", 3, "3003333333", "carla@correo.com"),
            ("Jorge", "López",    "1004", "1982-11-30", 4, "3004444444", "jorge@correo.com"),
            ("María", "Torres",   "1005", "1998-09-08", 1, "3005555555", "maria@correo.com"),
        ]
    )

    cursor.executemany(
        """INSERT INTO cuentas
           (id_cliente, tipo_cuenta, saldo, fecha_apertura, estado)
           VALUES (?, ?, ?, ?, ?)""",
        [
            (1, "Ahorros",   1500000.00, "2020-01-15", "Activa"),
            (2, "Corriente", 3200000.00, "2019-06-20", "Activa"),
            (3, "Ahorros",    850000.00, "2021-03-10", "Activa"),
            (4, "Ahorros",  12000000.00, "2018-11-05", "Activa"),
            (5, "Corriente",  500000.00, "2022-07-01", "Inactiva"),
            (1, "Corriente", 2000000.00, "2023-01-20", "Activa"),
        ]
    )

    cursor.executemany(
        """INSERT INTO movimientos
           (id_cuenta, fecha_movimiento, tipo_movimiento, valor, descripcion)
           VALUES (?, ?, ?, ?, ?)""",
        [
            (1, "2026-04-01", "Consignación",  500000.00,   "Nómina"),
            (1, "2026-04-03", "Retiro",        -200000.00,  "Retiro cajero"),
            (2, "2026-04-02", "Consignación",  1200000.00,  "Pago cliente"),
            (2, "2026-04-05", "Transferencia", -300000.00,  "Pago proveedor"),
            (3, "2026-04-01", "Consignación",   400000.00,  "Depósito"),
            (4, "2026-04-04", "Retiro",        -500000.00,  "Gasto personal"),
            (4, "2026-04-06", "Consignación",  2000000.00,  "Venta inmueble"),
            (5, "2026-04-02", "Retiro",        -100000.00,  "Compra online"),
            (6, "2026-04-07", "Consignación",   800000.00,  "Abono"),
            (6, "2026-04-08", "Transferencia", -150000.00,  "Pago servicios"),
        ]
    )

    conn.commit()
    conn.close()
    print(f"✅ Base de datos '{DB_PATH}' creada y poblada correctamente.")
    print("   Tablas: ciudad (4), clientes (5), cuentas (6), movimientos (10)")


if __name__ == "__main__":
    crear_base_de_datos()
