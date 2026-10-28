# Downloads official tools with SHA-512 verification. Does not install Blender.
param([string]$Destination = "$env:LOCALAPPDATA\NiangaoTools")
$ErrorActionPreference = 'Stop'
$version = '4.6.3'
$base = "https://github.com/godotengine/godot/releases/download/$version-stable"
New-Item -ItemType Directory -Force $Destination | Out-Null
$sums = Join-Path $Destination 'SHA512-SUMS.txt'
Invoke-WebRequest "$base/SHA512-SUMS.txt" -OutFile $sums
function Get-Verified([string]$name) {
 $file = Join-Path $Destination $name
 if (-not (Test-Path $file)) { Invoke-WebRequest "$base/$name" -OutFile $file }
 $line = Get-Content $sums | Where-Object { ($_ -split '\s+')[-1].TrimStart('*') -eq $name }
 if (-not $line) { throw "Missing official checksum: $name" }
 $expected = ($line -split '\s+')[0]
 if ((Get-FileHash $file -Algorithm SHA512).Hash -ne $expected) { throw "Checksum mismatch: $file" }
 return $file
}
$editor = Get-Verified "Godot_v$version-stable_win64.exe.zip"
Expand-Archive -Force $editor (Join-Path $Destination 'editor')
$template = Get-Verified "Godot_v$version-stable_export_templates.tpz"
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [IO.Compression.ZipFile]::OpenRead($template)
$target = Join-Path $env:APPDATA "Godot/export_templates/$version.stable"
New-Item -ItemType Directory -Force $target | Out-Null
try {
 foreach ($name in @('windows_release_x86_64.exe','windows_debug_x86_64.exe')) {
  $entry = $zip.GetEntry("templates/$name")
  if (-not $entry) { throw "Template missing: $name" }
  [IO.Compression.ZipFileExtensions]::ExtractToFile($entry,(Join-Path $target $name),$true)
 }
} finally { $zip.Dispose() }
$env:GODOT_BIN = (Get-ChildItem (Join-Path $Destination 'editor') -Filter '*console.exe' | Select-Object -First 1).FullName
Write-Host "GODOT_BIN=$env:GODOT_BIN"
Write-Host 'Current PowerShell session is ready. Run tools/run-tests.ps1 and tools/export-windows.ps1.'
