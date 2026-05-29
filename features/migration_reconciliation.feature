# language: es
Característica: Reconciliación de migración entre capas
  Verifica la integridad de los datos al moverse por el pipeline de migración
  on-premise -> nube: crudo (origen) -> curado (saneado) -> producto.

  @TC-301 @migracion
  Escenario: Los registros vigentes del crudo cuadran con la capa curada
    Dado que estoy conectado al data warehouse
    Entonces los registros vigentes del crudo "raw.account_balances" deben cuadrar con la capa curada "curated.account_balances_standard"

  @TC-302 @migracion
  Escenario: La capa curada y la capa de producto tienen la misma cantidad de filas
    Dado que estoy conectado al data warehouse
    Entonces la cantidad de filas en la tabla "curated.account_balances_standard" debe ser igual a la de la tabla "product.account_balances"
