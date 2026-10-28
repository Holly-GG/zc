# Run in Windows PowerShell on an interactive desktop. Moves mouse temporarily.
# Independent underlying WinForms app receives genuine OS clicks, not SendMessage clicks.
param([string]$Exe = "$PSScriptRoot/../exports/windows/Niangao-P0.exe", [switch]$ResetPosition)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class NiangaoWin32 {
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll")] public static extern void mouse_event(uint flags,uint dx,uint dy,uint data,UIntPtr extra);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern IntPtr FindWindow(string cls,string title);
 [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr hwnd,uint msg,IntPtr w,IntPtr l);
 [DllImport("user32.dll")] public static extern bool SetProcessDpiAwarenessContext(IntPtr context);
}
'@
[NiangaoWin32]::SetProcessDpiAwarenessContext([IntPtr](-4)) | Out-Null
$Exe = (Resolve-Path $Exe).Path
$userDir = Join-Path $env:APPDATA 'Godot/app_userdata/Niangao P0'
$configPath = Join-Path $userDir 'config.json'
$tracePath = Join-Path $userDir 'diagnostics.jsonl'
$original = $null
$hadConfig = Test-Path $configPath
if ($ResetPosition -and $hadConfig) { $original = [IO.File]::ReadAllBytes($configPath); Remove-Item $configPath }
$cursor = [Windows.Forms.Cursor]::Position
$script:underlayClicks = 0
$form = New-Object Windows.Forms.Form
$form.Text = 'Niangao independent underlay acceptance'
$form.FormBorderStyle = 'None'
$form.StartPosition = 'Manual'
$form.Bounds = [Windows.Forms.Screen]::PrimaryScreen.WorkingArea
$form.BackColor = [Drawing.Color]::SteelBlue
$form.Add_MouseDown({ if ($_.Button -eq [Windows.Forms.MouseButtons]::Left) { $script:underlayClicks++ } })
$pet = $null
$results = New-Object 'System.Collections.Generic.List[string]'
function Pump([int]$ms) {
 $watch = [Diagnostics.Stopwatch]::StartNew()
 while ($watch.ElapsedMilliseconds -lt $ms) { [Windows.Forms.Application]::DoEvents(); Start-Sleep -Milliseconds 10 }
}
function State {
 for ($retry=0; $retry -lt 20; $retry++) {
  try {
   $line = Get-Content $tracePath -Tail 1 -ErrorAction Stop
   return $line | ConvertFrom-Json
  } catch { Pump 100 }
 }
 throw 'No current diagnostics record'
}
function Wait-Ready {
 for ($retry=0; $retry -lt 100; $retry++) {
  if ($pet.HasExited) { throw 'Pet exited before ready' }
  if (Test-Path $tracePath) { $s = State; if ($s.polygon_points -gt 3) { return $s } }
  Pump 100
 }
 throw 'Alpha hit polygon did not become ready'
}
function Click([int]$x,[int]$y) {
 [NiangaoWin32]::SetCursorPos($x,$y) | Out-Null
 Pump 120
 [NiangaoWin32]::mouse_event(2,0,0,0,[UIntPtr]::Zero)
 Pump 60
 [NiangaoWin32]::mouse_event(4,0,0,0,[UIntPtr]::Zero)
 Pump 500
}
function Check([bool]$value,[string]$message) {
 if (-not $value) { throw "FAIL $message" }
 $results.Add("PASS $message"); Write-Host "PASS $message"
}
function Close-Pet {
 $handle = [NiangaoWin32]::FindWindow($null,'Niangao P0 PLACEHOLDER')
 if ($handle -eq [IntPtr]::Zero) { throw 'Main window not found' }
 [NiangaoWin32]::PostMessage($handle,0x10,[IntPtr]::Zero,[IntPtr]::Zero) | Out-Null
 for ($retry=0; $retry -lt 100 -and -not $pet.HasExited; $retry++) { Pump 100 }
 Check $pet.HasExited 'normal close completes'
 Check ($pet.ExitCode -eq 0) 'normal exit code 0'
}
try {
 if (Get-Process -Name 'Niangao-P0' -ErrorAction SilentlyContinue) { throw 'Close existing Niangao instances before acceptance' }
 $form.Show(); Pump 200
 $pet = Start-Process -FilePath $Exe -ArgumentList @('--','--diagnostics') -PassThru
 $s = Wait-Ready
 if ($ResetPosition -or -not $hadConfig) {
  $area = [Windows.Forms.Screen]::PrimaryScreen.WorkingArea
  Check ([Math]::Abs($s.position[0]+$s.size[0]-($area.Right-16)) -le 3) 'first launch right margin'
  Check ([Math]::Abs($s.position[1]+$s.size[1]-($area.Bottom-16)) -le 3) 'first launch bottom margin / taskbar avoidance'
 }
 $x=[int]$s.position[0]; $y=[int]$s.position[1]; $kx=$s.size[0]/360.0; $ky=$s.size[1]/420.0
 $before=$script:underlayClicks
 Click ($x+10*$kx) ($y+10*$ky)
 Check ($script:underlayClicks -eq $before+1) 'transparent corner click reaches lower app'
 $before=$script:underlayClicks; $petBefore=[int](State).events.PET_CLICKED
 Click ($x+180*$kx) ($y+200*$ky)
 Check ($script:underlayClicks -eq $before) 'opaque body click does not leak to lower app'
 Check ([int](State).events.PET_CLICKED -eq $petBefore+1) 'opaque body click reaches pet EventBus'
 $before=$script:underlayClicks
 Click ($x+85*$kx) ($y+85*$ky)
 Check ($script:underlayClicks -eq $before+1) 'transparent concavity inside character bounds passes through'
 [NiangaoWin32]::SetCursorPos(($x+180*$kx),($y+200*$ky)) | Out-Null
 [NiangaoWin32]::mouse_event(2,0,0,0,[UIntPtr]::Zero); Pump 200
 [NiangaoWin32]::SetCursorPos(($x+110*$kx),($y+150*$ky)) | Out-Null
 Pump 400
 [NiangaoWin32]::mouse_event(4,0,0,0,[UIntPtr]::Zero); Pump 1100
 $moved=State
 Check (($moved.position -join ',') -ne ($s.position -join ',')) 'drag changes window position'
 Close-Pet
 $saved=Get-Content $configPath -Raw | ConvertFrom-Json
 Check (($saved.window.position -join ',') -eq ($moved.position -join ',')) 'position saved in user config'
 $pet=Start-Process -FilePath $Exe -ArgumentList @('--','--diagnostics') -PassThru
 Pump 1000
 $restored=Wait-Ready
 Check (($restored.position -join ',') -eq ($moved.position -join ',')) 'position restored after restart'
 Close-Pet
 $results.Add('Native Windows automated acceptance completed. Manual DPI/hotplug/visual checks still required.')
} finally {
 if ($pet -and -not $pet.HasExited) {
  $h=[NiangaoWin32]::FindWindow($null,'Niangao P0 PLACEHOLDER')
  if ($h -ne [IntPtr]::Zero) { [NiangaoWin32]::PostMessage($h,0x10,[IntPtr]::Zero,[IntPtr]::Zero) | Out-Null; Pump 1000 }
  if (-not $pet.HasExited) { $pet.Kill(); $pet.WaitForExit() }
 }
 $form.Close(); $form.Dispose()
 [NiangaoWin32]::SetCursorPos($cursor.X,$cursor.Y) | Out-Null
 if ($ResetPosition) {
  if ($hadConfig -and $null -ne $original) { [IO.File]::WriteAllBytes($configPath,$original) }
  elseif (Test-Path $configPath) { Remove-Item $configPath }
 }
 $report=Join-Path $PSScriptRoot '../exports/windows/native-acceptance.txt'
 $results | Set-Content -Encoding UTF8 $report
 Write-Host "Partial/passed results: $report (a thrown error means FAIL)"
}
