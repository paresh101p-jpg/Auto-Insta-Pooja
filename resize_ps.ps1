Add-Type -AssemblyName System.Drawing

$inputDir = ".\images"
$images = Get-ChildItem -Path $inputDir -Include *.png, *.jpg -Recurse | Where-Object { -not $_.PSIsContainer }
$count = 0

foreach ($img in $images) {
    if ($img.Length -gt 150KB) {
        $bmp = New-Object System.Drawing.Bitmap $img.FullName
        $newPath = [System.IO.Path]::ChangeExtension($img.FullName, ".jpg")
        
        $ratio = [math]::Min(1080.0 / $bmp.Width, 1080.0 / $bmp.Height)
        $newWidth = [int]($bmp.Width * $ratio)
        if ($newWidth -gt 1080) { $newWidth = 1080 }
        $newHeight = [int]($bmp.Height * $ratio)
        if ($newHeight -gt 1080) { $newHeight = 1080 }

        if ($bmp.Width -gt 1080 -or $bmp.Height -gt 1080) {
            $newBmp = New-Object System.Drawing.Bitmap $newWidth, $newHeight
            $graphics = [System.Drawing.Graphics]::FromImage($newBmp)
            $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
            $graphics.DrawImage($bmp, 0, 0, $newWidth, $newHeight)
            $bmp.Dispose()
            $newBmp.Save($newPath, [System.Drawing.Imaging.ImageFormat]::Jpeg)
            $newBmp.Dispose()
            $graphics.Dispose()
        } else {
            $bmp.Save($newPath, [System.Drawing.Imaging.ImageFormat]::Jpeg)
            $bmp.Dispose()
        }
        
        if ($img.FullName -ne $newPath) {
            Remove-Item $img.FullName -Force
        }
        $count++
        Write-Host "Compressed: $($img.Name)"
    }
}
Write-Host "Total Compressed: $count"
