param([string]$OutputDirectory = "$PSScriptRoot/../exports/windows")
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
$exe = Join-Path $OutputDirectory 'Niangao-P0.exe'
if (-not (Test-Path $exe)) { throw 'Export Niangao-P0.exe before packaging' }
$stage = Join-Path ([IO.Path]::GetTempPath()) ("niangao-package-" + [guid]::NewGuid().ToString('N'))
try {
 $bundle = Join-Path $stage 'Niangao-P0'
 New-Item -ItemType Directory -Force $bundle | Out-Null
 Copy-Item $exe $bundle
 Copy-Item (Join-Path $root 'docs') (Join-Path $bundle 'docs') -Recurse
 New-Item -ItemType Directory -Force (Join-Path $bundle 'tools'),(Join-Path $bundle 'exports/windows') | Out-Null
 Copy-Item (Join-Path $PSScriptRoot 'acceptance-windows.ps1') (Join-Path $bundle 'tools')
 $hash = (Get-FileHash $exe -Algorithm SHA256).Hash.ToLowerInvariant()
 "$hash  Niangao-P0.exe" | Set-Content (Join-Path $OutputDirectory 'SHA256SUMS.txt') -Encoding ascii
 Copy-Item (Join-Path $OutputDirectory 'SHA256SUMS.txt') $bundle
 @'
Niangao P0 / PLACEHOLDER

Run Niangao-P0.exe on Windows 10/11 x64. Godot and Blender are not needed.
Requires OpenGL 3.3 drivers. Drag cat; right-click/F3 for debug; T for topmost;
H to hide; Esc to save and exit. Use the system tray to restore a hidden pet.

The model is a geometric PLACEHOLDER, not the final Niangao reconstruction.
Native Windows mouse pass-through, mixed DPI and hotplug remain unverified.
Wine pass-through failed; see docs/validation.md for the actual test scope.

Native desktop acceptance (temporarily moves the mouse):
powershell -File tools/acceptance-windows.ps1 -Exe ./Niangao-P0.exe -ResetPosition

Engine and dependency licenses: docs/GODOT-LICENSE.txt, docs/GODOT-COPYRIGHT.txt.
'@ | Set-Content (Join-Path $bundle 'README-WINDOWS.txt') -Encoding utf8
 Compress-Archive -Path $bundle -DestinationPath (Join-Path $OutputDirectory 'Niangao-P0-windows.zip') -Force
} finally {
 if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
}
