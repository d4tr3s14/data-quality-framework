"""
Conector de producción para Google BigQuery.

Implementa la misma interfaz ``Warehouse`` que el backend DuckDB del demo, de
modo que los MISMOS features y steps corren contra BigQuery en un entorno real
(migración on-premise -> GCP) cambiando solo ``DB_BACKEND=bigquery``.

Credenciales: se toman de una service account vía
``GOOGLE_APPLICATION_CREDENTIALS`` (ruta al JSON) o de las credenciales por
defecto del entorno (ADC). Nunca se incluyen claves en el repositorio.

NOTA DE PORTAFOLIO: este conector se incluye para evidenciar la integración
real con GCP. El demo reproducible corre sobre DuckDB y no lo ejercita.
"""
from __future__ import annotations

import os
from typing import Optional, Tuple

import pandas as pd

from utils.warehouse import Warehouse


class BigQueryWarehouse(Warehouse):
    def __init__(self, project_id: str):
        from google.cloud import bigquery

        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if cred_path:
            from google.oauth2 import service_account

            credentials = service_account.Credentials.from_service_account_file(cred_path)
            self._client = bigquery.Client(credentials=credentials, project=project_id)
        else:
            # Application Default Credentials (ej. workload identity en CI/CD).
            self._client = bigquery.Client(project=project_id)
        self.project_id = project_id

    def run_query(self, sql: str) -> pd.DataFrame:
        return self._client.query(sql).to_dataframe()

    def get_schema(self, table: str) -> pd.DataFrame:
        dataset, name = self._split(table)
        sql = f"""
            SELECT LOWER(column_name) AS column_name, UPPER(data_type) AS data_type
            FROM `{self.project_id}.{dataset}.INFORMATION_SCHEMA.COLUMNS`
            WHERE table_name = '{name}'
        """
        return self._client.query(sql).to_dataframe()

    def get_partition_info(self, table: str) -> Tuple[Optional[str], Optional[object]]:
        table_ref = f"{self.project_id}.{self._qualified(table)}"
        meta = self._client.get_table(table_ref)
        field = None
        if meta.time_partitioning and meta.time_partitioning.field:
            field = meta.time_partitioning.field
        elif meta.range_partitioning and meta.range_partitioning.field:
            field = meta.range_partitioning.field
        if not field:
            return None, None
        latest = self.run_query(
            f"SELECT MAX({field}) AS v FROM {self.quote_table(table)}"
        )['v'].iloc[0]
        return field, latest

    def quote_table(self, table: str) -> str:
        return f"`{self.project_id}.{self._qualified(table)}`"

    def regexp_no_match(self, column: str, pattern: str) -> str:
        return f"NOT REGEXP_CONTAINS(CAST({column} AS STRING), r'^{pattern}$')"

    @staticmethod
    def _split(table: str) -> Tuple[str, str]:
        parts = table.replace("`", "").split(".")
        return parts[-2], parts[-1]

    @staticmethod
    def _qualified(table: str) -> str:
        dataset, name = BigQueryWarehouse._split(table)
        return f"{dataset}.{name}"
