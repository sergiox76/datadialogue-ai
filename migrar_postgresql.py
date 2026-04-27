"""
============================================================
DataDialogue AI — Fase 2
migrar_postgresql.py: Migra banco.db (SQLite) → PostgreSQL
============================================================
Pre-requisitos:
  1. PostgreSQL instalado y corriendo
  2. Crear la BD:  createdb -U postgres banco
  3. Configurar variables en .env (ver .env.example)

Ejecutar: python migrar_postgresql.py
"""

import sqlite3
import os
import sys
from dotenv import load_dotenv

# Intentar importar psycopg2
try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("❌ psycopg2 no instalado. Ejecuta: pip install psycopg2-binary")
    sys.exit(1)

load_dotenv()

# ── Configuración ──────────────────────────────────────────
SQLITE_PATH = os.getenv("SQLITE_PATH", "banco.db")
PG_CONFIG = {
    "host":     os.getenv("PG_HOST",     "localhost"),
    "port":     int(os.getenv("PG_PORT", "5432")),
    "user":     os.getenv("PG_USER",     "postgres"),
    "password": os.getenv("PG_PASSWORD", ""),
    "dbname":   os.getenv("PG_DATABASE", "banco"),
}

# ── Esquema PostgreSQL ─────────────────────────────────────
SCHEMA_SQL = """
DROP TABLE IF EXISTS movimientos  CASCADE;
DROP TABLE IF EXISTS cuentas      CASCADE;
DROP TABLE IF EXISTS clientes     CASCADE;
DROP TABLE IF EXISTS ciudad       CASCADE;

CREATE TABLE ciudad (
    id_ciudad     SERIAL       PRIMARY KEY,
    nombre_ciudad VARCHAR(100) NOT NULL,
    departamento  VARCHAR(100) NOT NULL
);

CREATE TABLE clientes (
    id_cliente       SERIAL       PRIMARY KEY,
    nombre           VARCHAR(100) NOT NULL,
    apellido         VARCHAR(100) NOT NULL,
    documento        VARCHAR(20)  NOT NULL UNIQUE,
    fecha_nacimiento DATE         NOT NULL,
    id_ciudad        INTEGER      NOT NULL REFERENCES ciudad(id_ciudad),
    telefono         VARCHAR(20),
    correo           VARCHAR(150)
);

CREATE TABLE cuentas (
    id_cuenta      SERIAL         PRIMARY KEY,
    id_cliente     INTEGER        NOT NULL REFERENCES clientes(id_cliente),
    tipo_cuenta    VARCHAR(20)    NOT NULL,
    saldo          NUMERIC(15,2)  NOT NULL,
    fecha_apertura DATE           NOT NULL,
    estado         VARCHAR(20)    NOT NULL
);

CREATE TABLE movimientos (
    id_movimiento    SERIAL        PRIMARY KEY,
    id_cuenta        INTEGER       NOT NULL REFERENCES cuentas(id_cuenta),
    fecha_movimiento DATE          NOT NULL,
    tipo_movimiento  VARCHAR(20)   NOT NULL,
    valor            NUMERIC(15,2) NOT NULL,
    descripcion      VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_clientes_ciudad    ON clientes(id_ciudad);
CREATE INDEX IF NOT EXISTS idx_cuentas_cliente    ON cuentas(id_cliente);
CREATE INDEX IF NOT EXISTS idx_movimientos_cuenta ON movimientos(id_cuenta);
"""

TABLAS = ["ciudad", "clientes", "cuentas", "movimientos"]


def leer_sqlite():
    """Lee todas las tablas de SQLite y las devuelve como diccionarios."""
    if not os.path.exists(SQLITE_PATH):
        print(f"❌ No se encontró {SQLITE_PATH}. Ejecuta primero: python setup_db.py")
        sys.exit(1)

    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    datos = {}
    for tabla in TABLAS:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {tabla} ORDER BY 1;")
        filas = [dict(row) for row in cur.fetchall()]
        datos[tabla] = filas
        print(f"  📥 {tabla}: {len(filas)} registros leídos de SQLite")
    conn.close()
    return datos


def crear_esquema_pg(pg_cur):
    """Crea las tablas en PostgreSQL."""
    pg_cur.execute(SCHEMA_SQL)
    print("  ✅ Esquema creado en PostgreSQL")


def insertar_datos_pg(pg_cur, datos):
    """Inserta los datos en PostgreSQL con SERIAL gestionado manualmente."""
    for tabla, filas in datos.items():
        if not filas:
            continue

        columnas = list(filas[0].keys())
        placeholders = ", ".join(["%s"] * len(columnas))
        cols_str = ", ".join(columnas)
        sql = f"INSERT INTO {tabla} ({cols_str}) VALUES ({placeholders})"

        valores = [tuple(fila[c] for c in columnas) for fila in filas]
        psycopg2.extras.execute_batch(pg_cur, sql, valores)

        # Sincronizar secuencia SERIAL con el máximo id insertado
        id_col = f"id_{tabla[:-1] if tabla.endswith('s') else tabla}"  # heurística
        col_pk = columnas[0]  # La PK siempre es la primera columna
        pg_cur.execute(
            f"SELECT setval(pg_get_serial_sequence('{tabla}', '{col_pk}'), "
            f"MAX({col_pk})) FROM {tabla};"
        )
        print(f"  ✅ {tabla}: {len(filas)} registros insertados")


def validar_migracion(pg_cur):
    """Compara conteos entre SQLite y PostgreSQL."""
    print("\n── Validación ──────────────────────────────────")
    for tabla in TABLAS:
        pg_cur.execute(f"SELECT COUNT(*) FROM {tabla};")
        conteo = pg_cur.fetchone()[0]
        print(f"  {tabla:15s}: {conteo} registros en PostgreSQL")
    print("────────────────────────────────────────────────")


def migrar():
    print("\n🚀 Iniciando migración SQLite → PostgreSQL")
    print(f"   Origen : {SQLITE_PATH}")
    print(f"   Destino: {PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['dbname']}\n")

    # Leer datos de SQLite
    print("1. Leyendo datos de SQLite...")
    datos = leer_sqlite()

    # Conectar a PostgreSQL
    print("\n2. Conectando a PostgreSQL...")
    try:
        pg_conn = psycopg2.connect(**PG_CONFIG)
        pg_conn.autocommit = False
        pg_cur = pg_conn.cursor()
        print("   ✅ Conexión establecida")
    except psycopg2.OperationalError as e:
        print(f"   ❌ Error de conexión: {e}")
        print("   Verifica que PostgreSQL esté corriendo y que las credenciales en .env sean correctas.")
        sys.exit(1)

    # Crear esquema
    print("\n3. Creando esquema en PostgreSQL...")
    crear_esquema_pg(pg_cur)

    # Insertar datos
    print("\n4. Insertando datos...")
    insertar_datos_pg(pg_cur, datos)

    # Commit y validar
    pg_conn.commit()
    print("\n5. Validando migración...")
    validar_migracion(pg_cur)

    pg_cur.close()
    pg_conn.close()
    print("\n✅ Migración completada exitosamente.")


if __name__ == "__main__":
    migrar()
