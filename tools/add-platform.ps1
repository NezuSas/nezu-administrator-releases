[CmdletBinding()]
param(
    [string]$Name,
    [string]$IconPath
)

$repository = Split-Path -Parent $PSScriptRoot
Set-Location $repository

if (git status --porcelain) {
    throw "El repositorio tiene cambios pendientes. Confírmalos o guárdalos antes de añadir una plataforma."
}
if (-not $Name) { $Name = Read-Host "Nombre de la plataforma" }
if (-not $IconPath) { $IconPath = Read-Host "Ruta completa de la imagen (PNG, JPG, WEBP o SVG)" }

python .\tools\add_platform.py --name $Name --icon $IconPath
if ($LASTEXITCODE -ne 0) { throw "No se modificó el catálogo." }

git add assets/catalog.json assets/platforms
git commit -m "feat(assets): add platform $Name"
git push origin main
if ($LASTEXITCODE -ne 0) { throw "La plataforma se preparó localmente, pero no se pudo subir a GitHub." }

Write-Host "Listo. GitHub Actions firmará el catálogo automáticamente." -ForegroundColor Green
