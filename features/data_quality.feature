# language: es
Característica: Calidad de datos en la capa de producto
  Validaciones genéricas y reutilizables de calidad de datos (nulos,
  duplicados, formatos y dominio) sobre la última partición disponible.

  @TC-201 @calidad
  Escenario: Campos clave sin valores nulos
    Dado que estoy conectado al data warehouse
    Entonces los campos "periodo,id_cliente,id_cuenta,saldo_cuotas" en la tabla "product.account_balances" no deben contener valores nulos

  @TC-202 @calidad
  Escenario: Identificador de cuenta sin duplicados
    Dado que estoy conectado al data warehouse
    Entonces el campo "id_cuenta" en la tabla "product.account_balances" no debe tener valores duplicados

  @TC-203 @calidad
  Escenario: Clave compuesta cliente-fondo sin duplicados
    Dado que estoy conectado al data warehouse
    Entonces los campos compuestos "periodo,id_cliente,tipo_fondo" en la tabla "product.fund_balance_pesos" no deben tener valores duplicados

  @TC-204 @calidad
  Escenario: Fecha de apertura con formato válido
    Dado que estoy conectado al data warehouse
    Entonces el campo "fec_apertura" en la tabla "product.account_balances" debe cumplir con el formato de fecha "YYYY-MM-DD"

  @TC-205 @calidad
  Escenario: Identificador de cliente solo numérico
    Dado que estoy conectado al data warehouse
    Entonces el campo "id_cliente" en la tabla "product.account_balances" debe contener solo caracteres numéricos
