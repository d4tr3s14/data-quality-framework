# language: es
Característica: Reglas de negocio - cálculo de saldos
  Valida que el saldo en pesos publicado en la capa de producto se corresponde
  con el recálculo desde el origen: saldo en cuotas x valor cuota del último
  día del periodo, por cada fondo (A-E).

  @TC-401 @negocio
  Esquema del escenario: Reconciliar saldo calculado vs producto para el cliente <id_cliente>
    Dado que estoy conectado al data warehouse
    Cuando obtengo los saldos en cuotas del cliente "<id_cliente>" del periodo 202507 desde la tabla "curated.account_balances_standard"
    Y obtengo los valores cuota del periodo 202507 desde la tabla "curated.quote_values_daily"
    Entonces el saldo en pesos calculado coincide con la tabla de producto "product.fund_balance_pesos" para el cliente "<id_cliente>" del periodo 202507

    Ejemplos: Clientes a validar
      | id_cliente |
      | 1          |
      | 7          |
      | 13         |
      | 20         |
      | 25         |
