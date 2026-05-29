"""
Conector de producción para Oracle (origen on-premise).

En un escenario de migración real, Oracle suele ser el sistema de origen contra
el que se reconcilian los datos ya migrados a la nube. Este módulo encapsula la
conexión y la ejecución de consultas devolviendo DataFrames de pandas.

Credenciales: se toman de variables de entorno; nunca se hardcodean ni se
versionan archivos con secretos.
    ORACLE_HOST, ORACLE_PORT, ORACLE_SERVICE_NAME, ORACLE_USER, ORACLE_PASSWORD

NOTA DE PORTAFOLIO: incluido para evidenciar la capacidad de reconciliación
origen on-premise vs destino nube. El demo reproducible usa DuckDB para simular
ambas capas, por lo que este conector no se ejercita en CI.
"""
from __future__ import annotations

import logging
import os

import pandas as pd


def get_oracle_connection():
    """Abre una conexión a Oracle usando credenciales del entorno."""
    import oracledb

    try:
        dsn = oracledb.makedsn(
            os.environ["ORACLE_HOST"],
            int(os.environ["ORACLE_PORT"]),
            service_name=os.environ["ORACLE_SERVICE_NAME"],
        )
        connection = oracledb.connect(
            user=os.environ["ORACLE_USER"],
            password=os.environ["ORACLE_PASSWORD"],
            dsn=dsn,
        )
        logging.info("Conexión a Oracle establecida.")
        return connection
    except Exception as exc:
        logging.error(f"Error al conectar a Oracle: {exc}")
        return None


def run_query(connection, query: str) -> pd.DataFrame:
    """Ejecuta una consulta en Oracle y devuelve un DataFrame."""
    try:
        logging.info("Ejecutando consulta en Oracle...")
        df = pd.read_sql(query, con=connection)
        logging.info(f"Consulta exitosa: {len(df)} filas.")
        return df
    except Exception as exc:
        logging.error(f"Error al ejecutar la consulta en Oracle: {exc}")
        logging.error(f"Query: {query}")
        return pd.DataFrame()
