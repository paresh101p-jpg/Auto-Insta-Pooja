$videoDir = "E:\Paresh\Auto Post\Auto-Insta-Pooja\new_video"
$outputFile = "E:\Paresh\Auto Post\Auto-Insta-Pooja\reels_urls.txt"
$backupFile = "E:\Paresh\Auto Post\Auto-Insta-Pooja\reels_urls_backup.txt"
$progressFile = "E:\Paresh\Auto Post\Auto-Insta-Pooja\uploaded_reels_log.txt"

if (-not (Test-Path $videoDir)) {
    Write-Host "Folder '$videoDir' not found!"
    exit
}

$uploadedSet = @{}
if (Test-Path $progressFile) {
    Get-Content $progressFile | ForEach-Object { $uploadedSet[$_.Trim()] = $true }
}

$mp4Files = @(Get-ChildItem -Path $videoDir -Filter *.mp4)

if ($mp4Files.Count -eq 0) {
    Write-Host "No .mp4 files found in $videoDir folder!"
    exit
}

Write-Host "Found $($mp4Files.Count) total reels in $videoDir."

$pendingFiles = @($mp4Files | Where-Object { -not $uploadedSet.ContainsKey($_.Name) })
Write-Host "Pending reels to upload: $($pendingFiles.Count)"

$uploadedCount = 0

foreach ($file in $pendingFiles) {
    $filePath = $file.FullName
    $fileName = $file.Name
    
    Write-Host "[$($uploadedCount + 1)/$($pendingFiles.Count)] Uploading $fileName..."
    
    $success = $false
    for ($retry = 1; $retry -le 3; $retry++) {
        try {
            $url = curl.exe -k -s -F "reqtype=fileupload" -F "fileToUpload=@$filePath" https://catbox.moe/user/api.php
            
            if ($url -match "^https://") {
                Write-Host "Success! URL: $url"
                Add-Content -Path $outputFile -Value $url
                Add-Content -Path $backupFile -Value $url
                Add-Content -Path $progressFile -Value $fileName
                $uploadedCount++
                $success = $true
                break
            } else {
                Write-Host "Attempt $retry failed for $fileName. Response: $url"
                Start-Sleep -Seconds 2
            }
        } catch {
            Write-Host "Exception on attempt $retry for ${fileName}: $_"
            Start-Sleep -Seconds 2
        }
    }
    
    if (-not $success) {
        Write-Host "Skipping $fileName after 3 failed attempts."
    }
    
    Start-Sleep -Milliseconds 800
}

Write-Host "`nUpload complete! Successfully uploaded $uploadedCount reels."
Write-Host "The URLs are saved in $outputFile."
