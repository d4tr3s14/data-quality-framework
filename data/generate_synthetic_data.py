"""
Genera una base de datos DuckDB con datos *100% sintéticos* para el demo.

Modela una plataforma ficticia de inversión multifondo ("Veridian") con tres
capas, replicando un pipeline típico de migración on-premise -> nube:

    raw      -> datos crudos aterrizados desde el origen (simula extracto on-prem)
    curated  -> datos estandarizados / saneados
    product  -> datos listos para consumo de negocio

Todos los identificadores, montos y clientes son aleatorios y deterministas
(semilla fija): no proviene ningún dato de ningún cliente real.

Uso:
    python data/generate_synthetic_data.py
"""
from __future__ import annotations

import os
import random
from datetime import date

import duckdb

SEED = 20240115
DB_PATH = os.path.join(os.path.dirname(__file__), "veridian_demo.duckdb")

PERIODS = [202506, 202507]
FUNDS = ["A", "B", "C", "D", "E"]
PRODUCTS = ["CTA_AHORRO", "CTA_INVERSION", "CTA_PREVISIONAL"]
N_CLIENTS = 25

# Valor cuota por fondo y periodo (último día del mes es el que usa el negocio).
QUOTE_DAYS = {202506: [date(2025, 6, 27), date(2025, 6, 28), date(2025, 6, 30)],
              202507: [date(2025, 7, 29), date(2025, 7, 30), date(2025, 7, 31)]}


def _periodo_to_proc_date(periodo: int) -> date:
    year, month = divmod(periodo, 100)
    return date(year, month, 1)


def build_raw_rows(rng: random.Random):
    """Filas crudas: incluyen registros anulados (estado_reg='N') y vigentes."""
    rows = []
    cuenta_seq = 1000
    for periodo in PERIODS:
        proc_date = _periodo_to_proc_date(periodo)
        for cid in range(1, N_CLIENTS + 1):
            client_funds = rng.sample(FUNDS, rng.randint(1, 3))
            for fondo in client_funds:
                for _ in range(rng.randint(1, 2)):
                    cuenta_seq += 1
                    producto = rng.choice(PRODUCTS)
                    # 1 de cada ~8 registros está anulado y debe filtrarse en curated.
                    estado = "N" if rng.random() < 0.12 else "V"
                    saldo_cuotas = round(rng.uniform(50, 5000), 4)
                    apertura = date(
                        rng.randint(2008, 2023), rng.randint(1, 12), rng.randint(1, 28)
                    )
                    rows.append(
                        (
                            periodo, cid, cuenta_seq, producto, fondo,
                            saldo_cuotas, apertura, estado, "CARGA_MENSUAL", proc_date,
                        )
                    )
    return rows


def build_quote_values(rng: random.Random):
    rows = []
    base = {"A": 38000.0, "B": 42000.0, "C": 51000.0, "D": 33000.0, "E": 29000.0}
    for periodo in PERIODS:
        for fondo in FUNDS:
            for d in QUOTE_DAYS[periodo]:
                val = round(base[fondo] * rng.uniform(0.98, 1.05), 6)
                rows.append((periodo, fondo, val, d))
    return rows


def last_quote_by_fund(quote_rows):
    """Valor cuota del último día por (periodo, fondo)."""
    latest = {}
    for periodo, fondo, val, d in quote_rows:
        key = (periodo, fondo)
        if key not in latest or d > latest[key][1]:
            latest[key] = (val, d)
    return {k: v[0] for k, v in latest.items()}


def main() -> None:
    rng = random.Random(SEED)

    raw_rows = build_raw_rows(rng)
    quote_rows = build_quote_values(rng)
    quote_lookup = last_quote_by_fund(quote_rows)

    # curated = solo registros vigentes (saneados)
    curated_rows = [r for r in raw_rows if r[7] == "V"]

    # product (capa de cuentas) = misma granularidad que curated (cuadra el conteo)
    product_account_rows = [
        (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[9]) for r in curated_rows
    ]

    # product.fund_balance_pesos = saldo en pesos por cliente/fondo (regla de negocio)
    agg = {}
    for periodo, cid, _cuenta, _prod, fondo, saldo_cuotas, *_ in curated_rows:
        agg[(periodo, cid, fondo)] = agg.get((periodo, cid, fondo), 0.0) + saldo_cuotas

    fund_balance_rows = []
    totals_by_client = {}
    for (periodo, cid, fondo), cuotas in agg.items():
        val_cuota = quote_lookup[(periodo, fondo)]
        saldo_pesos = round(cuotas * val_cuota, 0)
        fund_balance_rows.append([periodo, cid, fondo, saldo_pesos, 0.0])
        totals_by_client[(periodo, cid)] = totals_by_client.get((periodo, cid), 0.0) + saldo_pesos

    for row in fund_balance_rows:
        periodo, cid, _fondo, saldo_pesos, _ = row
        total = totals_by_client[(periodo, cid)]
        row[4] = round((saldo_pesos / total) * 100, 2) if total else 0.0

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    con = duckdb.connect(DB_PATH)

    con.execute("CREATE SCHEMA raw; CREATE SCHEMA curated; CREATE SCHEMA product;")

    con.execute(
        """
        CREATE TABLE raw.account_balances (
            periodo INTEGER, id_cliente INTEGER, id_cuenta INTEGER,
            tipo_producto VARCHAR, tipo_fondo VARCHAR, saldo_cuotas DOUBLE,
            fec_apertura DATE, estado_reg VARCHAR, proceso VARCHAR,
            fecha_insercion_dt DATE
        )"""
    )
    con.executemany("INSERT INTO raw.account_balances VALUES (?,?,?,?,?,?,?,?,?,?)", raw_rows)

    con.execute(
        """
        CREATE TABLE curated.account_balances_standard (
            periodo INTEGER, id_cliente INTEGER, id_cuenta INTEGER,
            tipo_producto VARCHAR, tipo_fondo VARCHAR, saldo_cuotas DOUBLE,
            fec_apertura DATE, estado_reg VARCHAR, proceso VARCHAR,
            fecha_insercion_dt DATE
        )"""
    )
    con.executemany(
        "INSERT INTO curated.account_balances_standard VALUES (?,?,?,?,?,?,?,?,?,?)", curated_rows
    )

    con.execute(
        """
        CREATE TABLE product.account_balances (
            periodo INTEGER, id_cliente INTEGER, id_cuenta INTEGER,
            tipo_producto VARCHAR, tipo_fondo VARCHAR, saldo_cuotas DOUBLE,
            fec_apertura DATE, fecha_proceso_dt DATE
        )"""
    )
    con.executemany(
        "INSERT INTO product.account_balances VALUES (?,?,?,?,?,?,?,?)", product_account_rows
    )

    con.execute(
        """
        CREATE TABLE curated.quote_values_daily (
            periodo INTEGER, tipo_fondo VARCHAR, val_cuota DOUBLE, fec_valor DATE
        )"""
    )
    con.executemany("INSERT INTO curated.quote_values_daily VALUES (?,?,?,?)", quote_rows)

    con.execute(
        """
        CREATE TABLE product.fund_balance_pesos (
            periodo INTEGER, id_cliente INTEGER, tipo_fondo VARCHAR,
            saldo_pesos DOUBLE, distr_porcentaje DOUBLE
        )"""
    )
    con.executemany(
        "INSERT INTO product.fund_balance_pesos VALUES (?,?,?,?,?)", fund_balance_rows
    )

    con.close()

    print(f"Base de datos sintética generada en: {DB_PATH}")
    print(f"  raw.account_balances              : {len(raw_rows)} filas")
    print(f"  curated.account_balances_standard : {len(curated_rows)} filas")
    print(f"  product.account_balances          : {len(product_account_rows)} filas")
    print(f"  curated.quote_values_daily        : {len(quote_rows)} filas")
    print(f"  product.fund_balance_pesos        : {len(fund_balance_rows)} filas")


if __name__ == "__main__":
    main()
