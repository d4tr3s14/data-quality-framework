"""Steps de reconciliación de migración (on-premise -> nube).

Verifican que los datos se mantienen íntegros al moverse entre capas del
pipeline: crudo (origen) -> curado (saneado) -> producto (consumo).
"""
from behave import then

from utils.warehouse import Warehouse


def _count(context, table, extra_filter=""):
    wh: Warehouse = context.wh
    query = f"""
        SELECT COUNT(1) AS total
        FROM {wh.quote_table(table)}
        WHERE 1=1 {extra_filter} {wh.build_partition_filter(table)}
    """
    df = wh.run_query(query)
    return query, int(df['total'].iloc[0])


@then('la cantidad de filas en la tabla "{table_a}" debe ser igual a la de la tabla "{table_b}"')
def step_row_count_equal(context, table_a, table_b):
    q_a, count_a = _count(context, table_a)
    q_b, count_b = _count(context, table_b)

    context.query = f"{q_a}\n-- vs --\n{q_b}"
    context.query_result_str = f"{table_a}: {count_a} filas\n{table_b}: {count_b} filas"
    context.query_result_df = context.wh.run_query(
        f"SELECT {count_a} AS count_a, {count_b} AS count_b"
    )

    assert count_a == count_b, (
        f"La cantidad de filas no coincide. '{table_a}' tiene {count_a} filas, "
        f"'{table_b}' tiene {count_b}."
    )


@then('los registros vigentes del crudo "{raw_table}" deben cuadrar con la capa curada "{curated_table}"')
def step_raw_vigentes_match_curated(context, raw_table, curated_table):
    """El origen trae registros anulados; tras el saneamiento solo quedan los vigentes."""
    q_raw, count_raw = _count(context, raw_table, extra_filter="AND estado_reg = 'V'")
    q_cur, count_cur = _count(context, curated_table)

    context.query = f"{q_raw}\n-- vs --\n{q_cur}"
    context.query_result_str = (
        f"Crudo (solo vigentes): {count_raw} filas\nCurado: {count_cur} filas"
    )
    context.query_result_df = context.wh.run_query(
        f"SELECT {count_raw} AS crudo_vigentes, {count_cur} AS curado"
    )

    assert count_raw == count_cur, (
        f"Inconsistencia en la migración: el crudo tiene {count_raw} registros vigentes, "
        f"pero la capa curada tiene {count_cur}."
    )
