# Ejecuta el demo completo de punta a punta (Windows / PowerShell).
# No requiere que allure esté en el PATH — lo detecta automáticamente.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

# 1. Generar datos sintéticos
Write-Host "`n[1/3] Generando datos sinteticos..." -ForegroundColor Cyan
python data/generate_synthetic_data.py

# 2. Ejecutar la suite con el formatter de Allure
Write-Host "`n[2/3] Ejecutando suite de validacion..." -ForegroundColor Cyan
behave -f allure_behave.formatter:AllureFormatter -o allure-results

# 3. Abrir el dashboard de Allure
Write-Host "`n[3/3] Abriendo dashboard de Allure..." -ForegroundColor Cyan

# Busca el ejecutable allure en orden: PATH, npm global, scoop
$allureCmd = $null
foreach ($candidate in @(
    "allure",
    "$env:APPDATA\npm\allure.cmd",
    "$env:USERPROFILE\scoop\shims\allure.cmd"
)) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) {
        $allureCmd = $candidate
        break
    }
    if (Test-Path $candidate) {
        $allureCmd = $candidate
        break
    }
}

if ($allureCmd) {
    & $allureCmd serve allure-results
} else {
    Write-Host "`nAllure CLI no encontrado en el PATH." -ForegroundColor Yellow
    Write-Host "Genera el reporte estatico con:" -ForegroundColor Yellow
    Write-Host "  & `"$env:APPDATA\npm\allure.cmd`" generate allure-results --clean -o allure-report" -ForegroundColor White
    Write-Host "  start allure-report\index.html" -ForegroundColor White
}

Write-Host "`nPDFs de evidencia en: reports\pdf\" -ForegroundColor Green
