"""Steps genéricos y reutilizables de calidad de datos.

Todos operan sobre la última partición disponible (columna ``periodo``) usando
el backend activo, de modo que el mismo Gherkin sirve para DuckDB o BigQuery.
"""
from behave import then

from utils.warehouse import Warehouse


def _run(context, query):
    """Ejecuta una consulta y guarda la evidencia en el contexto para el reporte."""
    context.query = query
    df = context.wh.run_query(query)
    context.query_result_df = df
    context.query_result_str = df.to_string(index=False)
    return df


@then('los campos "{columns}" en la tabla "{table}" no deben contener valores nulos')
def step_no_nulls(context, columns, table):
    wh: Warehouse = context.wh
    null_conditions = " OR ".join(f"{c.strip()} IS NULL" for c in columns.split(','))
    query = f"""
        SELECT COUNT(1) AS null_count
        FROM {wh.quote_table(table)}
        WHERE ({null_conditions})
        {wh.build_partition_filter(table)}
    """
    df = _run(context, query)
    assert not df.empty, "La consulta de validación de nulos no devolvió resultados."
    assert df['null_count'].iloc[0] == 0, f"Se encontraron valores nulos en los campos: {columns}."


@then('el campo "{column}" en la tabla "{table}" no debe tener valores duplicados')
def step_no_duplicates(context, column, table):
    wh: Warehouse = context.wh
    query = f"""
        SELECT {column}, COUNT(1) AS qty
        FROM {wh.quote_table(table)}
        WHERE 1=1 {wh.build_partition_filter(table)}
        GROUP BY {column}
        HAVING COUNT(1) > 1
    """
    df = _run(context, query)
    assert df.empty, f"Se encontraron valores duplicados en el campo '{column}'."


@then('los campos compuestos "{columns}" en la tabla "{table}" no deben tener valores duplicados')
def step_no_composite_duplicates(context, columns, table):
    wh: Warehouse = context.wh
    partition_filter = wh.build_partition_filter(table)
    query = f"""
        WITH duplicados AS (
            SELECT {columns}, COUNT(*) AS cnt
            FROM {wh.quote_table(table)}
            WHERE 1=1 {partition_filter}
            GROUP BY {columns}
            HAVING COUNT(*) > 1
        )
        SELECT COUNT(*) AS grupos_duplicados FROM duplicados
    """
    df = _run(context, query)
    grupos = int(df['grupos_duplicados'].iloc[0]) if not df.empty else 0

    if grupos > 0:
        sample_query = f"""
            SELECT {columns}, COUNT(*) AS cnt
            FROM {wh.quote_table(table)}
            WHERE 1=1 {partition_filter}
            GROUP BY {columns} HAVING COUNT(*) > 1
            ORDER BY cnt DESC LIMIT 25
        """
        context.error_sample_query = sample_query
        sample_df = wh.run_query(sample_query)
        context.error_sample_df = sample_df
        context.error_sample_result = sample_df.to_string(index=False)

    assert grupos == 0, f"Se encontraron {grupos} grupos duplicados para la clave compuesta: {columns}."


# Mapa de formatos de fecha soportados -> expresión regular (anclada).
_DATE_REGEX = {
    "YYYY-MM-DD": r"\d{4}-\d{2}-\d{2}",
    "DD-MM-YYYY": r"\d{2}-\d{2}-\d{4}",
    "YYYYMM": r"\d{6}",
    "YYYYMMDD": r"\d{8}",
    "DD/MM/YYYY": r"\d{2}/\d{2}/\d{4}",
}


@then('el campo "{column}" en la tabla "{table}" debe cumplir con el formato de fecha "{date_format}"')
def step_date_format(context, column, table, date_format):
    wh: Warehouse = context.wh
    regex = _DATE_REGEX.get(date_format)
    assert regex, f"Formato de fecha '{date_format}' no está definido en los steps."

    query = f"""
        SELECT COUNT(1) AS registros_formato_invalido
        FROM {wh.quote_table(table)}
        WHERE {wh.regexp_no_match(column, regex)}
          AND {column} IS NOT NULL
          {wh.build_partition_filter(table)}
    """
    df = _run(context, query)
    assert not df.empty, "La consulta de validación de formato de fecha falló."
    assert df['registros_formato_invalido'].iloc[0] == 0, \
        f"El campo '{column}' no cumple con el formato {date_format}."


@then('el campo "{column}" en la tabla "{table}" debe contener solo caracteres numéricos')
def step_numeric_chars(context, column, table):
    wh: Warehouse = context.wh
    query = f"""
        SELECT COUNT(*) AS registros_no_numericos
        FROM {wh.quote_table(table)}
        WHERE {wh.regexp_no_match(column, r'[0-9]+')}
          AND {column} IS NOT NULL
          {wh.build_partition_filter(table)}
    """
    df = _run(context, query)
    assert not df.empty, "La consulta de validación de caracteres numéricos falló."
    assert df['registros_no_numericos'].iloc[0] == 0, \
        f"El campo '{column}' contiene caracteres no numéricos."


@then('la tabla "{table}" debe estar particionada')
def step_is_partitioned(context, table):
    col, _ = context.wh.get_partition_info(table)
    assert col is not None, f"La tabla '{table}' no está particionada o no se pudo verificar."
