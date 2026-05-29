# Ejecuta el demo completo de punta a punta (Windows / PowerShell).
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

python data/generate_synthetic_data.py
behave -f allure_behave.formatter:AllureFormatter -o allure-results

Write-Host ""
Write-Host "PDFs de evidencia en: reports/pdf/"
Write-Host "Para ver el dashboard de Allure:  allure serve allure-results"
