-- ============================================================
-- DataDialogue AI — Fase 2
-- postgresql_schema.sql: Esquema completo para PostgreSQL
-- ============================================================
-- Ejecutar con: psql -U postgres -d banco -f postgresql_schema.sql
--   o desde DBeaver / pgAdmin pegando este script

-- Crear base de datos (ejecutar conectado a postgres, no a banco)
-- CREATE DATABASE banco;
-- \c banco

-- ── Limpiar si existen ─────────────────────────────────────
DROP TABLE IF EXISTS movimientos  CASCADE;
DROP TABLE IF EXISTS cuentas      CASCADE;
DROP TABLE IF EXISTS clientes     CASCADE;
DROP TABLE IF EXISTS ciudad       CASCADE;

-- ── Tabla: ciudad ──────────────────────────────────────────
CREATE TABLE ciudad (
    id_ciudad     SERIAL       PRIMARY KEY,
    nombre_ciudad VARCHAR(100) NOT NULL,
    departamento  VARCHAR(100) NOT NULL
);

-- ── Tabla: clientes ────────────────────────────────────────
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

-- ── Tabla: cuentas ─────────────────────────────────────────
CREATE TABLE cuentas (
    id_cuenta      SERIAL         PRIMARY KEY,
    id_cliente     INTEGER        NOT NULL REFERENCES clientes(id_cliente),
    tipo_cuenta    VARCHAR(20)    NOT NULL CHECK (tipo_cuenta IN ('Ahorros', 'Corriente')),
    saldo          NUMERIC(15, 2) NOT NULL,
    fecha_apertura DATE           NOT NULL,
    estado         VARCHAR(20)    NOT NULL CHECK (estado IN ('Activa', 'Inactiva'))
);

-- ── Tabla: movimientos ─────────────────────────────────────
CREATE TABLE movimientos (
    id_movimiento    SERIAL         PRIMARY KEY,
    id_cuenta        INTEGER        NOT NULL REFERENCES cuentas(id_cuenta),
    fecha_movimiento DATE           NOT NULL,
    tipo_movimiento  VARCHAR(20)    NOT NULL
                         CHECK (tipo_movimiento IN ('Consignación', 'Retiro', 'Transferencia')),
    valor            NUMERIC(15, 2) NOT NULL,
    descripcion      VARCHAR(255)
);

-- ── Índices de rendimiento ─────────────────────────────────
CREATE INDEX idx_clientes_ciudad    ON clientes(id_ciudad);
CREATE INDEX idx_cuentas_cliente    ON cuentas(id_cliente);
CREATE INDEX idx_movimientos_cuenta ON movimientos(id_cuenta);
CREATE INDEX idx_movimientos_fecha  ON movimientos(fecha_movimiento);

-- ── Datos de ejemplo ───────────────────────────────────────
INSERT INTO ciudad (nombre_ciudad, departamento) VALUES
    ('Bogotá',    'Cundinamarca'),
    ('Medellín',  'Antioquia'),
    ('Cali',      'Valle del Cauca'),
    ('Manizales', 'Caldas');

INSERT INTO clientes (nombre, apellido, documento, fecha_nacimiento, id_ciudad, telefono, correo) VALUES
    ('Ana',   'Gómez',    '1001', '1990-05-10', 1, '3001111111', 'ana@correo.com'),
    ('Luis',  'Martínez', '1002', '1988-07-21', 2, '3002222222', 'luis@correo.com'),
    ('Carla', 'Ramírez',  '1003', '1995-03-14', 3, '3003333333', 'carla@correo.com'),
    ('Jorge', 'López',    '1004', '1982-11-30', 4, '3004444444', 'jorge@correo.com'),
    ('María', 'Torres',   '1005', '1998-09-08', 1, '3005555555', 'maria@correo.com');

INSERT INTO cuentas (id_cliente, tipo_cuenta, saldo, fecha_apertura, estado) VALUES
    (1, 'Ahorros',    1500000.00, '2020-01-15', 'Activa'),
    (2, 'Corriente',  3200000.00, '2019-06-20', 'Activa'),
    (3, 'Ahorros',     850000.00, '2021-03-10', 'Activa'),
    (4, 'Ahorros',   12000000.00, '2018-11-05', 'Activa'),
    (5, 'Corriente',   500000.00, '2022-07-01', 'Inactiva'),
    (1, 'Corriente',  2000000.00, '2023-01-20', 'Activa');

INSERT INTO movimientos (id_cuenta, fecha_movimiento, tipo_movimiento, valor, descripcion) VALUES
    (1, '2026-04-01', 'Consignación',   500000.00, 'Nómina'),
    (1, '2026-04-03', 'Retiro',        -200000.00, 'Retiro cajero'),
    (2, '2026-04-02', 'Consignación',  1200000.00, 'Pago cliente'),
    (2, '2026-04-05', 'Transferencia', -300000.00, 'Pago proveedor'),
    (3, '2026-04-01', 'Consignación',   400000.00, 'Depósito'),
    (4, '2026-04-04', 'Retiro',        -500000.00, 'Gasto personal'),
    (4, '2026-04-06', 'Consignación',  2000000.00, 'Venta inmueble'),
    (5, '2026-04-02', 'Retiro',        -100000.00, 'Compra online'),
    (6, '2026-04-07', 'Consignación',   800000.00, 'Abono'),
    (6, '2026-04-08', 'Transferencia', -150000.00, 'Pago servicios');

-- ── Validación ─────────────────────────────────────────────
SELECT 'ciudad'       AS tabla, COUNT(*) AS registros FROM ciudad
UNION ALL
SELECT 'clientes',     COUNT(*) FROM clientes
UNION ALL
SELECT 'cuentas',      COUNT(*) FROM cuentas
UNION ALL
SELECT 'movimientos',  COUNT(*) FROM movimientos;
