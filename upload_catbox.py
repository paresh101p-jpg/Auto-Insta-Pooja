import os
import requests
import time

def upload_to_catbox(file_path):
    url = "https://catbox.moe/user/api.php"
    try:
        with open(file_path, "rb") as f:
            files = {"fileToUpload": f}
            data = {"reqtype": "fileupload"}
            response = requests.post(url, data=data, files=files)
            if response.status_code == 200 and response.text.startswith("https"):
                return response.text
            else:
                print(f"Error uploading {file_path}: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        print(f"Exception during upload: {e}")
        return None

def main():
    video_dir = "new_video"
    output_file = "reels_urls.txt"
    
    if not os.path.exists(video_dir):
        print(f"Folder '{video_dir}' not found!")
        return

    mp4_files = [f for f in os.listdir(video_dir) if f.endswith(".mp4")]
    
    if not mp4_files:
        print("No .mp4 files found in new_video folder!")
        return
        
    print(f"Found {len(mp4_files)} reels. Starting upload to Catbox...")
    
    uploaded_count = 0
    with open(output_file, "a") as out_f:
        for index, file_name in enumerate(mp4_files):
            file_path = os.path.join(video_dir, file_name)
            print(f"[{index + 1}/{len(mp4_files)}] Uploading {file_name}...")
            
            url = upload_to_catbox(file_path)
            if url:
                print(f"Success! URL: {url}")
                out_f.write(f"{url}\n")
                out_f.flush() # Ensure it's written immediately
                uploaded_count += 1
                
                # Delete the local file after successful upload to save space
                try:
                    os.remove(file_path)
                    print(f"Deleted local file {file_name} to free up space.")
                except Exception as e:
                    print(f"Could not delete {file_name}: {e}")
            else:
                print(f"Failed to upload {file_name}. Will retry next time.")
                
            time.sleep(1) # Small delay to not spam the API

    print(f"\nUpload complete! Successfully uploaded {uploaded_count} reels.")
    print(f"The URLs are saved in {output_file}. You can now push this file to GitHub!")

if __name__ == "__main__":
    main()
