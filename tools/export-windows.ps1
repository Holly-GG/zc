param([string]$Godot = $env:GODOT_BIN)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not $Godot) { $Godot = 'godot' }
New-Item -ItemType Directory -Force exports/windows | Out-Null
& $Godot --headless --editor --import --quit
if ($LASTEXITCODE -ne 0) { throw 'Import failed' }
& $Godot --headless --path . --export-release 'Windows Desktop' exports/windows/Niangao-P0.exe
if ($LASTEXITCODE -ne 0) { throw 'Windows export failed' }
Get-FileHash exports/windows/Niangao-P0.exe -Algorithm SHA256
