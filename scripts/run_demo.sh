#!/usr/bin/env bash
# Ejecuta el demo completo de punta a punta (Linux / macOS).
set -euo pipefail
cd "$(dirname "$0")/.."

python data/generate_synthetic_data.py
behave -f allure_behave.formatter:AllureFormatter -o allure-results

echo
echo "PDFs de evidencia en: reports/pdf/"
echo "Para ver el dashboard de Allure:  allure serve allure-results"
