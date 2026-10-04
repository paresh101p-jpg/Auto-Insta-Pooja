$videoDir = "new_video"
$outputFile = "reels_urls.txt"

if (-not (Test-Path $videoDir)) {
    Write-Host "Folder '$videoDir' not found!"
    exit
}

$mp4Files = @(Get-ChildItem -Path $videoDir -Filter *.mp4)

if ($mp4Files.Count -eq 0) {
    Write-Host "No .mp4 files found in $videoDir folder!"
    exit
}

Write-Host "Found $($mp4Files.Count) reels. Starting upload to Catbox..."

$uploadedCount = 0

foreach ($file in $mp4Files) {
    $filePath = $file.FullName
    $fileName = $file.Name
    
    Write-Host "[$($uploadedCount + 1)/$($mp4Files.Count)] Uploading $fileName..."
    
    try {
        # Using curl (Invoke-RestMethod could work but curl/Invoke-WebRequest with form data can be tricky in older PS versions)
        # However, writing raw multipart/form-data in PS is hard, let's use the built-in curl.exe which comes with modern Windows
        $url = curl.exe -k -s -F "reqtype=fileupload" -F "fileToUpload=@$filePath" https://catbox.moe/user/api.php
        
        if ($url -match "^https://") {
            Write-Host "Success! URL: $url"
            Add-Content -Path $outputFile -Value $url
            Add-Content -Path "reels_urls_backup.txt" -Value $url
            $uploadedCount++
            
            # Delete local file to free space
            Remove-Item -Path $filePath -Force
            Write-Host "Deleted local file $fileName to free up space."
        } else {
            Write-Host "Failed to upload $fileName. Response: $url"
        }
    } catch {
        Write-Host "Exception during upload: $_"
    }
    
    Start-Sleep -Seconds 1
}

Write-Host "`nUpload complete! Successfully uploaded $uploadedCount reels."
Write-Host "The URLs are saved in $outputFile. You can now push this file to GitHub!"
