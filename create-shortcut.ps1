$target = "d:\REGIME PROJECT\regime-reaper\start-reaper.bat"
$shortcutPath = "$env:USERPROFILE\Desktop\REGIME REAPER.lnk"
$iconPath = "d:\REGIME PROJECT\regime-reaper\reaper.ico"

# Download skull icon from Windows shell32 (built-in, no download needed)
$WScriptShell = New-Object -ComObject WScript.Shell
$shortcut = $WScriptShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $target
$shortcut.WorkingDirectory = "d:\REGIME PROJECT\regime-reaper"
$shortcut.Description = "REGIME REAPER — Asset Acquisition Intelligence"
$shortcut.WindowStyle = 1

# Use skull-like icon from shell32 if custom icon missing
if (Test-Path $iconPath) {
    $shortcut.IconLocation = "$iconPath,0"
} else {
    # shell32.dll icon 294 is a tombstone/grave marker on most Windows versions
    $shortcut.IconLocation = "shell32.dll,294"
}

$shortcut.Save()
Write-Host "✅ Desktop shortcut created: $shortcutPath"
