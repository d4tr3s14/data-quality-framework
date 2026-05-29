"""Steps de reglas de negocio: cálculo y reconciliación de saldos.

Demuestra una validación funcional no trivial: recalcular el saldo en pesos
desde los datos de origen (saldo en cuotas x valor cuota del último día del
periodo) y comparar contra el dato publicado en la capa de producto.
"""
import allure
import numpy as np
import pandas as pd
from behave import when, then

from utils.warehouse import Warehouse


@when('obtengo los saldos en cuotas del cliente "{id_cliente}" del periodo {periodo:d} desde la tabla "{table}"')
def step_get_balances(context, id_cliente, periodo, table):
    wh: Warehouse = context.wh
    query = f"""
        SELECT id_cliente, tipo_fondo, SUM(saldo_cuotas) AS saldo_cuotas
        FROM {wh.quote_table(table)}
        WHERE id_cliente = {id_cliente} AND periodo = {periodo}
        GROUP BY id_cliente, tipo_fondo
        ORDER BY tipo_fondo
    """
    context.query = query
    df = wh.run_query(query)
    context.query_result_df = df
    context.query_result_str = df.to_string(index=False)
    assert not df.empty, f"No se encontraron saldos para el cliente {id_cliente} en {periodo}."
    context.saldos_cuotas_df = df


@when('obtengo los valores cuota del periodo {periodo:d} desde la tabla "{table}"')
def step_get_quotes(context, periodo, table):
    wh: Warehouse = context.wh
    query = f"""
        WITH ultimo_dia AS (
            SELECT MAX(fec_valor) AS max_fecha
            FROM {wh.quote_table(table)} WHERE periodo = {periodo}
        )
        SELECT tipo_fondo, val_cuota
        FROM {wh.quote_table(table)}
        WHERE periodo = {periodo} AND fec_valor = (SELECT max_fecha FROM ultimo_dia)
        ORDER BY tipo_fondo
    """
    context.query = query
    df = wh.run_query(query)
    context.query_result_df = df
    context.query_result_str = df.to_string(index=False)
    assert not df.empty, f"No se encontraron valores cuota para el periodo {periodo}."
    context.valores_cuota_df = df


@then('el saldo en pesos calculado coincide con la tabla de producto "{table}" para el cliente "{id_cliente}" del periodo {periodo:d}')
def step_validate_calculated_balance(context, table, id_cliente, periodo):
    wh: Warehouse = context.wh
    assert hasattr(context, 'saldos_cuotas_df'), "Faltan los saldos en cuotas (paso previo)."
    assert hasattr(context, 'valores_cuota_df'), "Faltan los valores cuota (paso previo)."

    # 1. Recalcular el saldo en pesos esperado desde el origen.
    df_calc = pd.merge(context.saldos_cuotas_df, context.valores_cuota_df, on="tipo_fondo", how="left")
    df_calc['saldo_pesos_calculado'] = (df_calc['saldo_cuotas'] * df_calc['val_cuota']).round(0)
    df_calc = df_calc[['tipo_fondo', 'saldo_pesos_calculado']].sort_values('tipo_fondo').reset_index(drop=True)
    context.attach_df_list.append(("Saldo en pesos calculado desde el origen", df_calc))

    # 2. Leer el dato publicado en la capa de producto.
    query = f"""
        SELECT tipo_fondo, saldo_pesos AS saldo_pesos_real
        FROM {wh.quote_table(table)}
        WHERE id_cliente = {id_cliente} AND periodo = {periodo}
        ORDER BY tipo_fondo
    """
    context.query = query
    df_real = wh.run_query(query)
    context.query_result_df = df_real
    context.query_result_str = df_real.to_string(index=False)
    assert not df_real.empty, f"La capa de producto no tiene datos para el cliente {id_cliente}."

    # 3. Comparar calculado vs real.
    comparacion = pd.merge(df_calc, df_real, on="tipo_fondo", how="outer").fillna(0)
    context.attach_df_list.append(("Comparación calculado vs producto", comparacion))
    allure.attach(comparacion.to_string(index=False), name="Reconciliación de saldos",
                  attachment_type=allure.attachment_type.TEXT)

    coinciden = np.isclose(
        comparacion['saldo_pesos_calculado'], comparacion['saldo_pesos_real'], atol=1.0
    )
    assert coinciden.all(), (
        "Inconsistencia entre el saldo calculado y el publicado en producto. "
        "Ver tabla 'Comparación calculado vs producto' en el reporte."
    )
