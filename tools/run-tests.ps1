param([string]$Godot = $env:GODOT_BIN)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not $Godot) { $Godot = 'godot' }
& $Godot --headless --editor --import --quit
if ($LASTEXITCODE -ne 0) { throw 'Godot import failed' }
& $Godot --headless --path . res://tests/test_runner.tscn
if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
