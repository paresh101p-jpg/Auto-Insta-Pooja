$ffmpeg = "E:\Paresh\Auto Post\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"
$inputDir = "E:\Paresh\Auto Post\Auto-Insta-Pooja\images"
$musicDir = "E:\Paresh\Auto Post\Auto-Insta-Pooja\music"
$outputDir = "E:\Paresh\Auto Post\Auto-Insta-Pooja\new_video"

if (-not (Test-Path $outputDir)) { New-Item -ItemType Directory -Force -Path $outputDir | Out-Null }

$images = @(Get-ChildItem -Path $inputDir -Include *.jpg, *.png -Recurse | Where-Object { -not $_.PSIsContainer })
$musics = @(Get-ChildItem -Path $musicDir -Include *.mp3, *.m4a, *.mp4, *.wav -Recurse | Where-Object { -not $_.PSIsContainer })

if ($musics.Count -eq 0) {
    Write-Host "No music files found!"
    exit
}

$effects = @(
    # Zoom In
    "[0:v]scale=1080:1350,zoompan=z='zoom+0.002':d=150:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1350:fps=30,eq=brightness=0.02:saturation=1.1[fg]",
    # Zoom Out
    "[0:v]scale=1080:1350,zoompan=z='1.2-in/1000':d=150:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1350:fps=30,eq=brightness=0.02:saturation=1.1[fg]",
    # Pan Right
    "[0:v]scale=1080:1350,zoompan=z=1.1:d=150:x='iw/2-(iw/zoom/2)+in':y='ih/2-(ih/zoom/2)':s=1080x1350:fps=30,eq=brightness=0.02:saturation=1.1[fg]",
    # Pan Left
    "[0:v]scale=1080:1350,zoompan=z=1.1:d=150:x='iw/2-(iw/zoom/2)-in':y='ih/2-(ih/zoom/2)':s=1080x1350:fps=30,eq=brightness=0.02:saturation=1.1[fg]"
)

$total = $images.Count
$count = 0

foreach ($img in $images) {
    $music = $musics | Get-Random
    $effect = $effects | Get-Random
    
    $outName = [System.IO.Path]::GetFileNameWithoutExtension($img.Name) + ".mp4"
    $outPath = Join-Path $outputDir $outName

    if (-not (Test-Path $outPath)) {
        # bg filter
        $bgFilter = "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=40:40[bg]"
        $fullFilter = "$bgFilter;$effect;[bg][fg]overlay=(W-w)/2:(H-h)/2[v]"

        & $ffmpeg -y -v error -loop 1 -t 5.5 -i $img.FullName -t 5 -i $music.FullName -filter_complex $fullFilter -map "[v]" -map 1:a? -c:v libx264 -c:a aac -pix_fmt yuv420p -shortest $outPath
    }

    $count++
    if ($count % 10 -eq 0) { Write-Host "Processed $count of $total reels" }
}

Write-Host "Done! All reels generated in $outputDir"
