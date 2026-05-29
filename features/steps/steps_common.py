"""Steps comunes: conexión al warehouse y validación de esquema."""
import allure
import pandas as pd
from behave import given, when, then

from utils.warehouse import get_warehouse


@given('que estoy conectado al data warehouse')
def step_connect(context):
    context.wh = get_warehouse()
    assert context.wh is not None, "No se pudo inicializar el backend del data warehouse."


@when('valido el esquema de la tabla "{table}"')
def step_schema_start(context, table):
    context.table_under_test = table


@then('el esquema debe ser el siguiente')
def step_validate_schema(context):
    """Compara el esquema real (column_name, data_type) contra el esperado en el feature."""
    expected_columns = ['column_name', 'data_type']
    for col in expected_columns:
        assert col in context.table.headings, f"La tabla del feature debe contener la columna '{col}'."

    expected_df = pd.DataFrame(context.table.rows, columns=expected_columns)
    expected_df['column_name'] = expected_df['column_name'].str.lower()
    expected_df['data_type'] = expected_df['data_type'].str.upper()

    actual_df = context.wh.get_schema(context.table_under_test)

    context.query = f"-- Esquema de {context.table_under_test} (information_schema.columns)"
    context.query_result_df = actual_df
    context.query_result_str = actual_df.to_string(index=False)

    assert not actual_df.empty, (
        f"No se obtuvo esquema para '{context.table_under_test}'. "
        "Verifique que la tabla exista y los permisos de lectura."
    )

    pd.testing.assert_frame_equal(
        expected_df.sort_values(by='column_name').reset_index(drop=True),
        actual_df.sort_values(by='column_name').reset_index(drop=True),
        check_like=True,
    )
    allure.attach(actual_df.to_string(index=False), name="Esquema real",
                  attachment_type=allure.attachment_type.TEXT)
