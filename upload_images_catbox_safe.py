import os
import requests
import time
import subprocess

IMAGE_DIR = "images"
URLS_FILE = "images_urls.txt"

if not os.path.exists(IMAGE_DIR):
    print("Images folder not found.")
    exit(0)

# Check which images are already in images_urls.txt to avoid re-uploading
existing_urls = []
if os.path.exists(URLS_FILE):
    with open(URLS_FILE, 'r') as f:
        existing_urls = f.read().splitlines()

images = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
if not images:
    print("No images found to upload.")
    exit(0)

print(f"Found {len(images)} images in folder. Starting upload to Catbox (without deleting local files)...")

urls_added = 0
for i, img_name in enumerate(images):
    img_path = os.path.join(IMAGE_DIR, img_name)
    print(f"[{i+1}/{len(images)}] Uploading {img_name}...")
    try:
        with open(img_path, 'rb') as f:
            resp = requests.post('https://catbox.moe/user/api.php', data={'reqtype': 'fileupload'}, files={'fileToUpload': f})
        if resp.status_code == 200:
            url = resp.text.strip()
            print(f"Success: {url}")
            # Write to file immediately
            with open(URLS_FILE, 'a') as uf:
                uf.write(url + '\n')
            urls_added += 1
            # NOT DELETING THE LOCAL FILE!
        else:
            print(f"Failed to upload {img_name}. Status: {resp.status_code}")
    except Exception as e:
        print(f"Error uploading {img_name}: {e}")
    time.sleep(1)

print(f"Finished. Successfully uploaded {urls_added} images to Catbox.")
