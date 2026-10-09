# Regenerates only the derived sprites and the offline layout preview.
# Source artwork is read-only. Run from any working directory.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$artRoot = Join-Path $repoRoot 'gfx/interface/SPD_GUI'
$outputRoot = Join-Path $artRoot 'generated'
[void][IO.Directory]::CreateDirectory($outputRoot)
# Render a 470x117 copy of the 503x125 category banner for full-width inline text.
# The original artwork remains untouched.
$categorySource = [Drawing.Bitmap]::FromFile((Join-Path $repoRoot 'gfx/interface/decisions/decision_GER_SPD.png'))
$categoryBanner = New-Object Drawing.Bitmap(470, 117)
$categoryCanvas = [Drawing.Graphics]::FromImage($categoryBanner)
try {
    $categoryCanvas.Clear([Drawing.Color]::Transparent)
    $categoryCanvas.InterpolationMode = [Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $categoryCanvas.DrawImage($categorySource, [Drawing.Rectangle]::new(0, 0, 470, 117), [Drawing.Rectangle]::new(0, 0, $categorySource.Width, $categorySource.Height), [Drawing.GraphicsUnit]::Pixel)
    $categoryBanner.Save((Join-Path $repoRoot 'gfx/interface/decisions/decision_GER_SPD_inline.png'), [Drawing.Imaging.ImageFormat]::Png)
}
finally { $categoryCanvas.Dispose(); $categoryBanner.Dispose(); $categorySource.Dispose() }
# Slice the original word shapes from their alpha channel, one ink band per row.
foreach ($faction in @('left', 'center', 'right')) {
    $sourceName = if ($faction -eq 'center') { 'center2.png' } else { $faction + '.png' }
    $source = [Drawing.Bitmap]::FromFile((Join-Path $artRoot $sourceName))
    $atlas = New-Object Drawing.Bitmap(2750, 12)
    $canvas = [Drawing.Graphics]::FromImage($atlas)
    try {
        $bands = @()
        $start = -1
        $minX = $source.Width
        $maxX = -1
        for ($y = 0; $y -lt $source.Height; $y++) {
            $count = 0
            for ($x = 0; $x -lt $source.Width; $x++) {
                if ($source.GetPixel($x, $y).A -gt 128) {
                    $count++
                    $minX = [Math]::Min($minX, $x)
                    $maxX = [Math]::Max($maxX, $x)
                }
            }
            if ($count -gt 20 -and $start -lt 0) { $start = $y }
            if ($count -le 20 -and $start -ge 0) {
                $bands += [PSCustomObject]@{ Top = $start; Height = $y - $start }
                $start = -1
            }
        }
        if ($start -ge 0) { $bands += [PSCustomObject]@{ Top = $start; Height = $source.Height - $start } }
        if ($bands.Count -ne 25) { throw ($sourceName + ': expected 25 ink bands, found ' + $bands.Count) }
        $canvas.Clear([Drawing.Color]::Transparent)
        $canvas.InterpolationMode = [Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $canvas.PixelOffsetMode = [Drawing.Drawing2D.PixelOffsetMode]::HighQuality
        $inkWidth = $maxX - $minX + 1
        for ($row = 0; $row -lt 25; $row++) {
            $height = [Math]::Max(1, [int][Math]::Round($bands[$row].Height * 110.0 / $inkWidth))
            $dest = [Drawing.Rectangle]::new($row * 110, [int][Math]::Floor((12 - $height) / 2), 110, $height)
            $crop = [Drawing.Rectangle]::new($minX, $bands[$row].Top, $inkWidth, $bands[$row].Height)
            $canvas.DrawImage($source, $dest, $crop, [Drawing.GraphicsUnit]::Pixel)
        }
        $atlas.Save((Join-Path $outputRoot ('rows_' + $faction + '.png')), [Drawing.Imaging.ImageFormat]::Png)
        Write-Output ($sourceName + ': sliced 25 original alpha-masked rows.')
    }
    finally { $canvas.Dispose(); $atlas.Dispose(); $source.Dispose() }
}

# Temporary exact copies only when unfinished headline artwork is absent.
# Replacing these files with final artwork is sufficient; this never overwrites them.
foreach ($name in @('title_center.png', 'title_right.png')) {
    $target = Join-Path $artRoot $name
    if (-not [IO.File]::Exists($target)) { [IO.File]::Copy((Join-Path $artRoot 'title.png'), $target) }
}

# Geometric portrait placeholder. Replace this file when faction portraits are ready.
$portrait = New-Object Drawing.Bitmap(60, 80)
$canvas = [Drawing.Graphics]::FromImage($portrait)
$ink = New-Object Drawing.SolidBrush([Drawing.Color]::FromArgb(255, 70, 61, 48))
$border = New-Object Drawing.Pen([Drawing.Color]::FromArgb(255, 106, 91, 67))
try {
    $canvas.Clear([Drawing.Color]::FromArgb(255, 192, 175, 141))
    $canvas.SmoothingMode = [Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $canvas.FillEllipse($ink, 19, 12, 22, 27)
    $canvas.FillEllipse($ink, 8, 41, 44, 44)
    $canvas.FillRectangle($ink, 24, 34, 12, 16)
    $canvas.DrawRectangle($border, 1, 1, 57, 77)
    $portrait.Save((Join-Path $outputRoot 'leader_placeholder.png'), [Drawing.Imaging.ImageFormat]::Png)
}
finally { $border.Dispose(); $ink.Dispose(); $canvas.Dispose(); $portrait.Dispose() }

# Render the actual GUI coordinates, frame numbers, textures and initial support values.
# This is an offline layout check, not an in-game screenshot.
$preview = New-Object Drawing.Bitmap(500, 730)
$canvas = [Drawing.Graphics]::FromImage($preview)
$loaded = @{}
try {
    $canvas.Clear([Drawing.Color]::FromArgb(255, 38, 39, 39))
    $guiText = [IO.File]::ReadAllText((Join-Path $repoRoot 'interface/GER_SPD_newspaper.gui'))
    $gfxText = [IO.File]::ReadAllText((Join-Path $repoRoot 'interface/GER_SPD_newspaper.gfx'))
    $effectsText = [IO.File]::ReadAllText((Join-Path $repoRoot 'common/scripted_effects/GER_SPD_newspaper_effects.txt'))
    $left = [int][regex]::Match($effectsText, 'GER_SPD_left_support = (\d+)').Groups[1].Value
    $center = [int][regex]::Match($effectsText, 'GER_SPD_center_support = (\d+)').Groups[1].Value
    foreach ($sprite in [regex]::Matches($gfxText, 'spriteType\s*=\s*\{([^}]+)\}')) {
        $name = [regex]::Match($sprite.Value, 'name\s*=\s*"([^"]+)"').Groups[1].Value
        $file = [regex]::Match($sprite.Value, 'texturefile\s*=\s*"([^"]+)"').Groups[1].Value
        $loaded[$name] = [Drawing.Bitmap]::FromFile((Join-Path $repoRoot $file))
    }
    $pattern = '(?:iconType|buttonType)\s*=\s*\{\s*name\s*=\s*"([^"]+)"\s*position\s*=\s*\{\s*x\s*=\s*(\d+)\s*y\s*=\s*(\d+)\s*\}\s*spriteType\s*=\s*"([^"]+)"([^}]*)\}'
    foreach ($icon in [regex]::Matches($guiText, $pattern)) {
        $name = $icon.Groups[1].Value
        if ($name -like 'GER_SPD_headline*') {
            $activeHeadline = if ($left -gt 60) { 'GER_SPD_headline_left' } elseif ($center -gt 60) { 'GER_SPD_headline_center' } elseif ((100 - $left - $center) -gt 60) { 'GER_SPD_headline_right' } else { 'GER_SPD_headline' }
            if ($name -ne $activeHeadline) { continue }
        }
        $x = [int]$icon.Groups[2].Value
        $y = [int]$icon.Groups[3].Value
        $texture = $loaded[$icon.Groups[4].Value]
        if ($name -match '^GER_SPD_row_(\d+)_(left|center|right)$') {
            $number = [int]$Matches[1]
            $faction = $Matches[2]
            $active = if ($number -le $left) { 'left' } elseif ($number -le $left + $center) { 'center' } else { 'right' }
            if ($faction -ne $active) { continue }
            $frame = [int][regex]::Match($icon.Groups[5].Value, 'frame\s*=\s*(\d+)').Groups[1].Value
            $dest = New-Object Drawing.Rectangle($x, $y, 110, 12)
            $src = [Drawing.Rectangle]::new(($frame - 1) * 110, 0, 110, 12)
            $canvas.DrawImage($texture, $dest, $src, [Drawing.GraphicsUnit]::Pixel)
        }
        else {
            $dest = [Drawing.Rectangle]::new($x, $y, $texture.Width, $texture.Height)
            $src = [Drawing.Rectangle]::new(0, 0, $texture.Width, $texture.Height)
            $canvas.DrawImage($texture, $dest, $src, [Drawing.GraphicsUnit]::Pixel)
        }
    }
    $preview.Save((Join-Path $PSScriptRoot 'preview.png'), [Drawing.Imaging.ImageFormat]::Png)
}
finally {
    foreach ($texture in $loaded.Values) { $texture.Dispose() }
    $canvas.Dispose()
    $preview.Dispose()
}
Write-Output 'Built 3 row atlases, portrait placeholder and preview.png.'
