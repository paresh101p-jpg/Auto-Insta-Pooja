$ffmpeg = "E:\Paresh\Auto Post\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"
$inputDir = "E:\Paresh\Auto Post\Auto-Insta-Pooja\images"
$outputDir = "E:\Paresh\Auto Post\Auto-Insta-Pooja\images_4x5"

if (-not (Test-Path $outputDir)) { New-Item -ItemType Directory -Force -Path $outputDir | Out-Null }

$images = Get-ChildItem -Path $inputDir -Include *.jpg, *.png -Recurse

$total = $images.Count
$count = 0
foreach ($img in $images) {
    if ($img.PSIsContainer) { continue }
    $outPath = Join-Path $outputDir $img.Name
    if (-not (Test-Path $outPath)) {
        & $ffmpeg -y -v error -i $img.FullName -vf "crop=ih*4/5:ih" -q:v 2 $outPath
    }
    $count++
    if ($count % 50 -eq 0) { Write-Host "Processed $count of $total" }
}
Write-Host "Done! $total images cropped to 4:5 in $outputDir"
