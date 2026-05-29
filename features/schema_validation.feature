# language: es
Característica: Validación de esquemas de tablas
  Verifica que las tablas publicadas en la capa de producto mantengan el
  contrato de datos esperado (nombres de columna y tipos de dato) tras la
  migración del pipeline.

  @TC-101 @schema
  Escenario: Validar esquema de la tabla product.account_balances
    Dado que estoy conectado al data warehouse
    Cuando valido el esquema de la tabla "product.account_balances"
    Entonces el esquema debe ser el siguiente
      | column_name      | data_type |
      | periodo          | INTEGER   |
      | id_cliente       | INTEGER   |
      | id_cuenta        | INTEGER   |
      | tipo_producto    | VARCHAR   |
      | tipo_fondo       | VARCHAR   |
      | saldo_cuotas     | DOUBLE    |
      | fec_apertura     | DATE      |
      | fecha_proceso_dt | DATE      |

  @TC-102 @schema
  Escenario: Validar esquema de la tabla product.fund_balance_pesos
    Dado que estoy conectado al data warehouse
    Cuando valido el esquema de la tabla "product.fund_balance_pesos"
    Entonces el esquema debe ser el siguiente
      | column_name      | data_type |
      | periodo          | INTEGER   |
      | id_cliente       | INTEGER   |
      | tipo_fondo       | VARCHAR   |
      | saldo_pesos      | DOUBLE    |
      | distr_porcentaje | DOUBLE    |
