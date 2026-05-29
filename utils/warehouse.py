"""
Capa de acceso a datos *backend-agnóstica*.

El framework no habla SQL de un motor específico desde los `steps`: en su lugar
pide al backend activo que construya los fragmentos dependientes del dialecto
(esquema, info de partición, expresiones regex). Así el MISMO archivo Gherkin y
los MISMOS steps corren contra:

    - DuckDB   -> backend por defecto del demo (datos sintéticos locales, sin nube)
    - BigQuery -> backend de producción (migración on-premise -> GCP)

El backend se selecciona con la variable de entorno ``DB_BACKEND``.

NOTA DE PORTAFOLIO: el demo usa DuckDB para que cualquiera pueda clonar y
ejecutar las pruebas sin credenciales ni infraestructura. El conector de
BigQuery se incluye para mostrar la integración real con GCP, pero no se
ejercita en la suite de demostración.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Optional, Tuple

import pandas as pd


class Warehouse(ABC):
    """Interfaz común que deben cumplir todos los backends de datos."""

    @abstractmethod
    def run_query(self, sql: str) -> pd.DataFrame:
        """Ejecuta una consulta y devuelve un DataFrame de pandas."""

    @abstractmethod
    def get_schema(self, table: str) -> pd.DataFrame:
        """Devuelve un DataFrame con columnas ``column_name`` y ``data_type``."""

    @abstractmethod
    def get_partition_info(self, table: str) -> Tuple[Optional[str], Optional[object]]:
        """Devuelve ``(columna_particion, ultimo_valor)`` o ``(None, None)``."""

    @abstractmethod
    def quote_table(self, table: str) -> str:
        """Formatea el identificador de tabla para el dialecto del backend."""

    @abstractmethod
    def regexp_no_match(self, column: str, pattern: str) -> str:
        """Expresión SQL booleana, TRUE cuando ``column`` NO cumple ``pattern``."""

    def build_partition_filter(self, table: str) -> str:
        """Cláusula ``AND ...`` para filtrar por la última partición (o vacío)."""
        col, latest = self.get_partition_info(table)
        if col is None or latest is None:
            return ""
        value = latest if isinstance(latest, (int, float)) else f"'{latest}'"
        return f"AND {col} = {value}"

    def close(self) -> None:  # pragma: no cover - opcional por backend
        pass


class DuckDBWarehouse(Warehouse):
    """Backend local basado en DuckDB. Motor del demo del portafolio.

    Convenciones:
      - Los identificadores se manejan en minúsculas (DuckDB pliega a minúscula
        los identificadores sin comillas), evitando problemas de mayúsculas.
      - Un ``table`` puede venir como ``esquema.tabla`` o ``proyecto.esquema.tabla``;
        en el segundo caso se ignora el prefijo de proyecto.
      - Si una tabla tiene una columna ``periodo`` se trata como columna de
        partición (equivalente a una tabla particionada por fecha en BigQuery).
    """

    PARTITION_COLUMN = "periodo"

    def __init__(self, database_path: str):
        import duckdb  # import perezoso: solo se exige si se usa este backend

        self._con = duckdb.connect(database_path, read_only=True)

    @staticmethod
    def _split_table(table: str) -> Tuple[str, str]:
        parts = table.replace("`", "").split(".")
        schema, name = parts[-2], parts[-1]
        return schema.lower(), name.lower()

    def run_query(self, sql: str) -> pd.DataFrame:
        return self._con.execute(sql).df()

    def get_schema(self, table: str) -> pd.DataFrame:
        schema, name = self._split_table(table)
        return self._con.execute(
            """
            SELECT lower(column_name) AS column_name,
                   upper(data_type)   AS data_type
            FROM information_schema.columns
            WHERE lower(table_schema) = ? AND lower(table_name) = ?
            """,
            [schema, name],
        ).df()

    def get_partition_info(self, table: str):
        schema, name = self._split_table(table)
        cols = self._con.execute(
            """
            SELECT lower(column_name) AS c
            FROM information_schema.columns
            WHERE lower(table_schema) = ? AND lower(table_name) = ?
            """,
            [schema, name],
        ).df()["c"].tolist()

        if self.PARTITION_COLUMN not in cols:
            return None, None

        latest = self._con.execute(
            f"SELECT MAX({self.PARTITION_COLUMN}) AS v FROM {self.quote_table(table)}"
        ).fetchone()[0]
        return self.PARTITION_COLUMN, latest

    def quote_table(self, table: str) -> str:
        schema, name = self._split_table(table)
        return f"{schema}.{name}"

    def regexp_no_match(self, column: str, pattern: str) -> str:
        return f"NOT regexp_full_match(CAST({column} AS VARCHAR), '{pattern}')"

    def close(self) -> None:
        self._con.close()


def get_warehouse() -> Warehouse:
    """Fábrica: instancia el backend según ``DB_BACKEND`` (default: duckdb)."""
    backend = os.getenv("DB_BACKEND", "duckdb").lower()

    if backend == "duckdb":
        db_path = os.getenv(
            "DUCKDB_PATH",
            os.path.join("data", "veridian_demo.duckdb"),
        )
        if not os.path.exists(db_path):
            raise FileNotFoundError(
                f"No se encontró la base de datos DuckDB en '{db_path}'. "
                "Genera los datos sintéticos primero:  python data/generate_synthetic_data.py"
            )
        return DuckDBWarehouse(db_path)

    if backend == "bigquery":
        from utils.bigquery_client import BigQueryWarehouse

        return BigQueryWarehouse(project_id=os.environ["GCP_PROJECT_ID"])

    raise ValueError(f"DB_BACKEND no soportado: '{backend}' (usa 'duckdb' o 'bigquery').")
