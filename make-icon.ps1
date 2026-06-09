# Creates a gold skull icon as reaper.ico using .NET drawing
Add-Type -AssemblyName System.Drawing

$size = 256
$bmp = New-Object System.Drawing.Bitmap($size, $size)
$g = [System.Drawing.Graphics]::FromImage($bmp)

# Background — obsidian black
$g.FillRectangle([System.Drawing.Brushes]::Black, 0, 0, $size, $size)

# Draw skull emoji via large font
$font = New-Object System.Drawing.Font("Segoe UI Emoji", 160, [System.Drawing.FontStyle]::Regular)
$brush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(212, 175, 55))  # Graveyard Gold
$sf = New-Object System.Drawing.StringFormat
$sf.Alignment = [System.Drawing.StringAlignment]::Center
$sf.LineAlignment = [System.Drawing.StringAlignment]::Center
$rect = New-Object System.Drawing.RectangleF(0, 0, $size, $size)
$g.DrawString("☠", $font, $brush, $rect, $sf)

$g.Dispose()

# Save as PNG first, then convert to ICO
$pngPath = "d:\REGIME PROJECT\regime-reaper\reaper-temp.png"
$icoPath = "d:\REGIME PROJECT\regime-reaper\reaper.ico"
$bmp.Save($pngPath, [System.Drawing.Imaging.ImageFormat]::Png)

# Convert PNG to ICO using .NET
$stream = New-Object System.IO.MemoryStream
$bmp.Save($stream, [System.Drawing.Imaging.ImageFormat]::Png)
$stream.Seek(0, [System.IO.SeekOrigin]::Begin)

$writer = [System.IO.File]::OpenWrite($icoPath)

# ICO header
$writer.Write([byte[]](0,0,1,0,1,0), 0, 6)
# Directory entry: 256x256, 32-bit
$writer.Write([byte[]](0,0,0,0,1,0,32,0), 0, 8)
# Size of PNG data
$pngBytes = $stream.ToArray()
$sizeBytes = [System.BitConverter]::GetBytes([int]$pngBytes.Length)
$writer.Write($sizeBytes, 0, 4)
# Offset to PNG data (6 header + 16 dir entry = 22)
$offsetBytes = [System.BitConverter]::GetBytes([int]22)
$writer.Write($offsetBytes, 0, 4)
# Write PNG data
$writer.Write($pngBytes, 0, $pngBytes.Length)
$writer.Close()
$stream.Close()
$bmp.Dispose()

Remove-Item $pngPath -ErrorAction SilentlyContinue
Write-Host "Icon created: $icoPath"
