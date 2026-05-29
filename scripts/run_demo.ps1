# Ejecuta el demo completo de punta a punta (Windows / PowerShell).
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

# Asegurar que el directorio global de npm esté disponible en esta sesión
$npmBin = "$env:APPDATA\npm"
if (Test-Path $npmBin) {
    $env:PATH = "$npmBin;$env:PATH"
}

# 1. Generar datos sintéticos
Write-Host "`n[1/3] Generando datos sinteticos..." -ForegroundColor Cyan
python data/generate_synthetic_data.py

# 2. Ejecutar la suite con el formatter de Allure
Write-Host "`n[2/3] Ejecutando suite de validacion..." -ForegroundColor Cyan
behave -f allure_behave.formatter:AllureFormatter -o allure-results

# 3. Abrir el dashboard de Allure
Write-Host "`n[3/3] Abriendo dashboard de Allure..." -ForegroundColor Cyan

$allureExe = Get-Command allure -ErrorAction SilentlyContinue
if ($allureExe) {
    allure serve allure-results
} else {
    # Fallback: generar reporte estático y abrir en el navegador
    Write-Host "Generando reporte estatico..." -ForegroundColor Yellow
    & "$npmBin\allure.cmd" generate allure-results --clean -o allure-report
    Start-Process "allure-report\index.html"
    Write-Host "Reporte abierto en el navegador." -ForegroundColor Green
}

Write-Host "`nPDFs de evidencia en: reports\pdf\" -ForegroundColor Green
