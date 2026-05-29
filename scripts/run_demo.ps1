# Ejecuta el demo completo de punta a punta (Windows / PowerShell).
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

# Localizar allure.cmd (instalado via npm). Probar PATH y ubicaciones conocidas.
$allureCmd = $null
$candidates = @(
    "$env:APPDATA\npm\allure.cmd",
    "$env:ProgramData\chocolatey\bin\allure.cmd",
    "$env:USERPROFILE\scoop\shims\allure.cmd"
)
foreach ($c in $candidates) {
    if (Test-Path $c) { $allureCmd = $c; break }
}

if ($allureCmd) {
    # Invocar vía cmd.exe: evita problemas del perfil de PowerShell con el
    # operador & sobre archivos .cmd, y maneja rutas con espacios.
    & cmd.exe /d /s /c """$allureCmd"" serve allure-results"
} else {
    Write-Host "`nAllure CLI no se encontro. Instalalo con:" -ForegroundColor Yellow
    Write-Host "  npm install -g allure-commandline" -ForegroundColor White
    Write-Host "Luego vuelve a ejecutar este script." -ForegroundColor White
}

Write-Host "`nPDFs de evidencia en: reports\pdf\" -ForegroundColor Green
