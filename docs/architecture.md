# Architecture

## Design goals

1. **One spec, many backends.** The Gherkin scenarios and step definitions are
   backend-agnostic. A demo runs locally on DuckDB; the same specs run against
   BigQuery in production.
2. **Evidence first.** Every step's query and result are captured and rendered
   into a PDF that a non-technical stakeholder can read.
3. **Reproducible.** Synthetic data is generated deterministically (fixed seed),
   so the suite is stable and requires no external infrastructure.

## Layered data model (synthetic "Veridian" platform)

The synthetic dataset reproduces a typical migration pipeline:

```
raw.account_balances           -> landed source extract (includes annulled rows)
        │  (sanitize: keep estado_reg = 'V')
        ▼
curated.account_balances_standard
        │  (publish)
        ▼
product.account_balances        -> business-facing accounts
product.fund_balance_pesos      -> balances in currency, per client & fund
curated.quote_values_daily      -> daily unit (cuota) values
```

## The `Warehouse` abstraction

`utils/warehouse.py` defines the contract every backend implements:

| Method | Responsibility | Dialect-specific |
|---|---|---|
| `run_query(sql)` | Execute SQL → DataFrame | — |
| `get_schema(table)` | Column names + types | `information_schema` vs BigQuery `INFORMATION_SCHEMA` |
| `get_partition_info(table)` | Partition column + latest value | column convention vs BigQuery partition metadata |
| `quote_table(table)` | Identifier quoting | plain vs backticks |
| `regexp_no_match(col, p)` | "value does not match" predicate | `regexp_full_match` vs `REGEXP_CONTAINS` |
| `build_partition_filter(table)` | `AND <col> = <latest>` clause | inherited default |

Steps build SQL using these helpers instead of hardcoding a dialect, which is
what makes the same scenarios portable across DuckDB and BigQuery.

## Evidence pipeline (Behave hooks)

`features/environment.py`:

- `before_scenario` — initializes the evidence buffer.
- `after_step` — captures the executed query, the result DataFrame, attached
  DataFrames (e.g. business calculations), and error tracebacks; mirrors them
  into Allure attachments.
- `after_scenario` — renders the PDF (`utils/pdf_generator.py`) and, if enabled,
  publishes the result to a test-management tool (`utils/test_management.py`).

## Extending the framework

- **New validation** → add a `@then` step in the relevant `steps_*.py` using the
  `Warehouse` helpers, then reference it from a `.feature`.
- **New backend** → implement the `Warehouse` interface and register it in
  `get_warehouse()`.
- **New domain** → adjust `data/generate_synthetic_data.py` and the schema
  expectations in the `.feature` files.
