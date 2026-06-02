# 📘 Guía detallada (para todos los niveles)

Esta guía explica **paso a paso** cómo ejecutar, entender y editar el proyecto
**data-quality-framework**, desde tu computador hasta lo que ocurre en GitHub
cuando se ejecuta el CI. Pensada para que **alguien junior** pueda hacerlo sin
complicaciones.

> Orden sugerido: **1)** ¿Qué es? → **2)** Glosario → **3)** Frameworks →
> **4)** Requisitos → **5)** Clonar → **6)** Ejecución local → **7)** Reportes →
> **8)** Cómo editar → **9)** Qué hace el CI.

---

## 1. ¿Qué es este proyecto?

Es un framework para **validar la calidad de los datos** y las **migraciones de
datos** (cuando los datos pasan de un sistema on-premise a la nube, como
BigQuery). Comprueba automáticamente cosas como: que las columnas y tipos sean
los esperados, que no haya nulos ni duplicados, que no se pierdan filas al migrar
y que los cálculos de negocio (ej. saldos) cuadren.

Funciona con **BDD (Behave)**: las validaciones se describen en lenguaje natural
(Gherkin) y se ejecutan contra una base de datos. El demo trae una base
**DuckDB** local con **datos sintéticos**, así que **corre sin credenciales ni
nube**. Genera **informes PDF** (para Product Owners) y dashboards **Allure**.

```
.feature (Gherkin) ─► steps ─► Warehouse (DuckDB local / BigQuery) ─► PDF + Allure
```

---

## 2. Glosario (términos clave)

| Término | Qué significa, en simple |
|---------|--------------------------|
| **Data quality** | Calidad de los datos: que sean completos, válidos, únicos y consistentes. |
| **Migración de datos** | Mover datos de un sistema a otro (ej. Oracle → BigQuery) sin perderlos ni alterarlos. |
| **BDD / Gherkin** | Escribir las validaciones en lenguaje natural (`Dado / Cuando / Entonces`). |
| **Behave** | La herramienta BDD de Python que ejecuta los `.feature`. |
| **Step (paso)** | La función Python que implementa una línea del Gherkin. |
| **SUT / Warehouse** | El "almacén de datos" bajo prueba. Aquí, DuckDB (demo) o BigQuery (producción). |
| **DuckDB** | Una base de datos analítica que vive en **un solo archivo local** (no necesita servidor). |
| **Backend** | La base de datos contra la que se corre (`duckdb` o `bigquery`); se cambia con `DB_BACKEND`. |
| **Schema** | El contrato de la tabla: qué columnas y de qué tipo. |
| **Reconciliación** | Comparar dos lados (ej. origen vs. destino) para ver que coinciden (filas, totales). |
| **Capas raw → curated → product** | Etapas por las que pasan los datos al transformarse. |
| **Allure** | Reporte interactivo de las validaciones, para ingenieros. |
| **Evidencia PDF** | Un PDF por escenario que muestra qué se validó, la consulta y el resultado (para negocio). |
| **CI** | Automatización que corre las validaciones en GitHub en cada cambio. |
| **gh-pages** | Rama donde se publica el reporte Allure como sitio web. |

---

## 3. Frameworks y lenguajes (para qué sirve cada uno)

| Herramienta | Lenguaje | ¿Para qué sirve **en este proyecto**? |
|-------------|----------|----------------------------------------|
| **Python** | — | Lenguaje base del framework. |
| **Behave** | Python | El motor **BDD**: ejecuta los escenarios `.feature` y sus steps. |
| **allure-behave** | Python | Genera los resultados para el dashboard **Allure** desde Behave. |
| **DuckDB** | SQL | La **base de datos local** del demo (un archivo, sin servidor). |
| **pandas** | Python | Manipula los resultados de las consultas como tablas. |
| **reportlab** | Python | Genera los **informes PDF** de evidencia. |
| **python-dotenv** | Python | Lee la configuración desde un archivo `.env`. |
| **BigQuery / Oracle clients** | Python | Conectores de **producción** (opcionales; el demo no los necesita). |
| **GitHub Actions** | YAML | El **CI**: corre las validaciones y publica el reporte. |

---

## 4. Requisitos previos

1. **Python 3.10+** → https://www.python.org/downloads/ (`python --version`).
2. **Git** → https://git-scm.com/
3. *(Opcional, para el dashboard)* **Allure CLI** → `npm install -g allure-commandline`.

> No necesitas nube ni credenciales: el demo usa **DuckDB local + datos sintéticos**.

---

## 5. Clonar el proyecto

```bash
git clone https://github.com/d4tr3s14/data-quality-framework.git
cd data-quality-framework
```

---

## 6. Ejecución LOCAL paso a paso

### Paso 1 — Entorno virtual e instalación
```bash
python -m venv .venv
```
Actívalo:
- **Windows (PowerShell):** `.\.venv\Scripts\Activate.ps1`
- **Linux / macOS:** `source .venv/bin/activate`

Instala dependencias:
```bash
pip install -r requirements.txt
```

### Paso 2 — Todo en un comando (recomendado)
Genera los datos, corre la suite y abre el dashboard:
- **Windows (PowerShell):** `.\scripts\run_demo.ps1`
- **Linux / macOS:** `./scripts/run_demo.sh`

> Si PowerShell bloquea el script:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`

### Paso 2 (alternativa) — Manual, paso a paso
```bash
# 1) Generar la base de datos sintética (crea data/veridian_demo.duckdb)
python data/generate_synthetic_data.py

# 2) Correr las validaciones BDD con salida Allure
behave -f allure_behave.formatter:AllureFormatter -o allure-results

# 3) Ver el dashboard
allure serve allure-results
```

Al terminar verás algo como `4 features passed, 14 scenarios passed`. Los
**PDF** de evidencia quedan en `reports/pdf/`.

### Configuración (opcional)
Copia `.env.example` a `.env` para ajustar valores. El más importante:
```
DB_BACKEND=duckdb     # 'duckdb' (demo) o 'bigquery' (producción)
```

---

## 7. Reportes

| Público | Reporte | Dónde |
|---------|---------|-------|
| **Ingeniero / QA** | **Allure** | `allure serve allure-results` |
| **Product Owner** | **PDF por escenario** | carpeta `reports/pdf/` |

---

## 8. Cómo EDITAR el proyecto (recetas para junior)

### a) Agregar una validación nueva (escenario)
Edita un `.feature` en `features/` (están en español). Por ejemplo, en
`data_quality.feature`:
```gherkin
  Escenario: La columna email no debe tener nulos
    Dado la tabla "clientes"
    Entonces la columna "email" no debe tener valores nulos
```
Si el paso ya existe en `features/steps/`, listo. Si es nuevo, impleméntalo en el
archivo de steps adecuado (`steps_quality.py`, `steps_business.py`, etc.).

### b) Entender dónde está la lógica
- `features/*.feature` → **qué** se valida (lenguaje natural).
- `features/steps/*.py` → **cómo** se valida (Python + SQL).
- `utils/warehouse.py` → la capa que habla con la base de datos (DuckDB/BigQuery).
- `utils/pdf_generator.py` → cómo se arman los PDF.

### c) Cambiar de backend (avanzado / producción)
En `.env`: `DB_BACKEND=bigquery` y completa las credenciales de GCP. Los mismos
`.feature` corren sin cambios.

---

## 9. ¿Qué hace el CI en GitHub? (paso a paso)

El CI vive en `.github/workflows/ci.yml` y corre en cada `push`/`pull request`:

1. **Set up Python + install** — instala Python y `requirements.txt`.
2. **Generate synthetic dataset** — `python data/generate_synthetic_data.py`.
3. **Run BDD validation suite** — `behave` con salida Allure (`allure-results`).
4. **Upload artifacts** — guarda los **resultados Allure** y los **PDF de
   evidencia** (`reports/pdf`) como artefactos descargables.
5. **Job `publish-report` (solo en push)** — genera el reporte **Allure** y lo
   **publica en GitHub Pages** (rama `gh-pages`).

### ¿Dónde veo el resultado?
- GitHub → pestaña **Actions** → el run (✅ / ❌).
- Reporte Allure en vivo: **https://d4tr3s14.github.io/data-quality-framework/**
  (requiere GitHub Pages activado en *Settings → Pages → rama `gh-pages`*).

---

## 10. Problemas comunes

| Problema | Solución |
|----------|----------|
| `behave: command not found` | Activa el `.venv` y `pip install -r requirements.txt`. |
| No existe `veridian_demo.duckdb` | Corre `python data/generate_synthetic_data.py`. |
| PowerShell bloquea el script | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`. |
| `allure: command not found` | Instala el CLI: `npm install -g allure-commandline`. |
| Quiero usar BigQuery y falla | Revisa `.env` (proyecto GCP + credenciales). El demo no lo necesita. |
| El badge de Allure da 404 | Falta activar GitHub Pages (rama `gh-pages`). |

---

## 11. Mapa de archivos

```
features/                escenarios BDD (Gherkin, español) — el "qué"
  environment.py         hooks de Behave (genera PDF/Allure por escenario)
  steps/                 step definitions (Python + SQL) — el "cómo"
utils/
  warehouse.py           capa que habla con la base de datos (DuckDB/BigQuery)
  pdf_generator.py       genera los informes PDF
  bigquery_client.py / oracle_client.py   conectores de producción (opcionales)
data/
  generate_synthetic_data.py   crea la base DuckDB con datos ficticios
  veridian_demo.duckdb         la base de datos del demo (generada)
behave.ini               configuración de Behave
.env.example             plantilla de configuración (cópiala a .env)
scripts/run_demo.*       ejecuta todo el demo de una
.github/workflows/ci.yml el pipeline de CI
```

---

¿Dudas? Empieza por la **sección 6** (`run_demo`), que hace todo de una sola vez.
