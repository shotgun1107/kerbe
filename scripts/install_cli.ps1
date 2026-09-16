param(
    [string]$Python = 'python'
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$venvRoot = Join-Path $projectRoot '.venv'
$venvPython = Join-Path $venvRoot 'Scripts\python.exe'

if (-not (Test-Path -LiteralPath $venvPython)) {
    & $Python -m venv $venvRoot
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the project virtual environment.' }
}

# Remove the former distribution before installing the renamed package:
# both distributions share the codex_usage import namespace.
$installedPackages = & $venvPython -m pip list --format=json
if ($LASTEXITCODE -ne 0) { throw 'Could not inspect the current installation.' }
if (($installedPackages | ConvertFrom-Json).name -contains 'codex-usage-tracker') {
    & $venvPython -m pip uninstall -y codex-usage-tracker
    if ($LASTEXITCODE -ne 0) { throw 'Could not migrate the previous installation.' }
}
& $venvPython -m pip install $projectRoot
if ($LASTEXITCODE -ne 0) { throw 'Could not install Kerbe.' }

$installBin = Join-Path $env:LOCALAPPDATA 'Programs\Kerbe\bin'
$null = New-Item -ItemType Directory -Path $installBin -Force
# The pip-generated native launcher embeds the virtual environment interpreter path.
# Expose only this command, not the venv's python/pip/activation scripts.
Copy-Item -LiteralPath (Join-Path $venvRoot 'Scripts\kerbe.exe') -Destination (Join-Path $installBin 'kerbe.exe') -Force

$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
$pathEntries = @($userPath -split ';' | Where-Object { $_ })
$alreadyPresent = @($pathEntries | Where-Object {
    [Environment]::ExpandEnvironmentVariables($_).TrimEnd('\') -ieq $installBin.TrimEnd('\')
}).Count -gt 0
if (-not $alreadyPresent) {
    $newUserPath = (@($pathEntries) + $installBin) -join ';'
    [Environment]::SetEnvironmentVariable('Path', $newUserPath, 'User')
}

if (-not (($env:Path -split ';') -contains $installBin)) {
    $env:Path = "$installBin;$env:Path"
}
& (Join-Path $installBin 'kerbe.exe') --version
if ($LASTEXITCODE -ne 0) { throw 'Installed command verification failed.' }
Write-Host 'Installed: kerbe'
Write-Host 'Open a new terminal, then run: kerbe --help'
Write-Host 'Keep this project and its .venv in place. Re-run this installer after moving or updating it.'
