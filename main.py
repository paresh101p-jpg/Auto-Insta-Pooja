import os
import random
import time
import subprocess
import requests
from google import genai
from PIL import Image
import urllib.parse
import json
from datetime import datetime

# Secrets from GitHub Actions
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
FB_ACCESS_TOKEN = os.environ.get("FB_ACCESS_TOKEN")

# NAYE PAGE KA ID YAHAN HARDCODE KAREIN
FB_PAGE_ID = "1313997728621727" 

if not all([GEMINI_API_KEY, FB_ACCESS_TOKEN]):
    print("Error: Please set GEMINI_API_KEY and FB_ACCESS_TOKEN in GitHub Secrets.")
    exit(1)

if FB_PAGE_ID == "YAHAN_APNA_NAYA_PAGE_ID_DALNA_HAI":
    print("Error: Please set your FB_PAGE_ID in main.py first.")
    exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)
IMAGES_FOLDER = "images"
GEMINI_MODELS = ["gemini-3.8-flash", "gemini-3.8-flash-001"]
# Yahan naye repo ka naam aayega (e.g., Auto-Insta-Pooja)
GITHUB_REPO_RAW_URL = "https://raw.githubusercontent.com/paresh101p-jpg/Auto-Insta-Pooja/master/"

HISTORY_FILE = "post_history.json"
POSTED_FOLDER = "posted_images"
REELS_FILE = "reels_urls.txt"
TEMP_VIDEO = "temp_video.mp4"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

def git_commit_and_push(commit_message):
    try:
        subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
        subprocess.run(["git", "config", "user.name", "Auto Insta Bot"], check=True)
        subprocess.run(["git", "add", "-A"], check=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "push"], check=True)
        print(f"Git Push Success: {commit_message}")
    except Exception as e:
        print(f"Git push warning: {e}")

def get_next_media():
    # Attempt 1: Check for local images in images/ folder with 7-day rule
    if not os.path.exists(IMAGES_FOLDER):
        os.makedirs(IMAGES_FOLDER)
    
    files = [
        f for f in os.listdir(IMAGES_FOLDER)
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".mp4"))
    ]
    random.shuffle(files)
    
    history = load_history()
    now = datetime.now()
    
    for f in files:
        base_name = os.path.splitext(f)[0]
        if base_name in history:
            last_date_str = history[base_name]
            try:
                last_post_date = datetime.fromisoformat(last_date_str)
                days_passed = (now - last_post_date).days
                if days_passed < 7:
                    print(f"Skipping image {f} (posted {days_passed} days ago, waiting for 7 days).")
                    continue
            except:
                pass
        
        # Valid file found!
        chosen_local_path = os.path.join(IMAGES_FOLDER, f)
        history[base_name] = now.isoformat()
        save_history(history)
        print(f"Using local media: {chosen_local_path} ({len(files)} remaining)")
        
        # Move immediately so it doesn't get picked up next time
        if not os.path.exists(POSTED_FOLDER):
            os.makedirs(POSTED_FOLDER)
        new_path = os.path.join(POSTED_FOLDER, f)
        os.rename(chosen_local_path, new_path)
        git_commit_and_push(f"Moved to posted: {f}")
        
        # Calculate public URL
        clean_path = new_path.replace("\\", "/")
        encoded_path = "/".join([urllib.parse.quote(p) for p in clean_path.split("/")])
        media_url = f"{GITHUB_REPO_RAW_URL}{encoded_path}"
        
        return {
            "type": "local",
            "local_path": new_path,
            "media_url": media_url,
            "is_video": new_path.lower().endswith('.mp4'),
            "original_path": chosen_local_path
        }

    # Attempt 2: If no valid images, use reels_urls.txt
    print("No valid images found in images/. Checking reels_urls.txt...")
    if os.path.exists(REELS_FILE):
        with open(REELS_FILE, "r") as f:
            urls = [line.strip() for line in f.readlines() if line.strip()]
            
        if urls:
            catbox_url = random.choice(urls)
            print(f"Using Catbox URL: {catbox_url} ({len(urls)-1} remaining)")
            
            # Remove the used URL from the list
            with open(REELS_FILE, "w") as f:
                urls.remove(catbox_url)
                f.write("\n".join(urls))
            git_commit_and_push("Used a Catbox URL and removed it from list")
            
            # Download the video temporarily so Gemini can analyze it
            print("Downloading video from Catbox for Gemini caption generation...")
            res = requests.get(catbox_url)
            with open(TEMP_VIDEO, "wb") as f:
                f.write(res.content)
                
            return {
                "type": "catbox",
                "local_path": TEMP_VIDEO,
                "media_url": catbox_url,
                "is_video": True,
                "original_path": None
            }
            
    raise Exception("No media available at all! (images folder is empty/blocked AND reels_urls.txt is empty). Please upload new media.")


def generate_caption(media_path):
    is_video = media_path.lower().endswith('.mp4')
    print(f"Analyzing {'video' if is_video else 'image'} using Gemini Vision...")
    prompt = (
        "You are an expert Fashion and Beauty Instagram Social Media Manager. Look closely at the content provided. "
        "It features a woman. Carefully observe her outfit, the style, the colors, and her overall look. "
        "Write a highly engaging, stylish, and beautiful Instagram caption in a mix of Hindi and English (Hinglish) describing her amazing look and outfit. "
        "Your response MUST be the final Instagram caption, formatted beautifully with emojis. "
        "Include the following elements in this exact order:\n"
        "1. A catchy 2-3 line description or compliment about her outfit, style, and beauty (Hinglish).\n"
        "2. An engaging question for the audience (e.g., 'Kaisa laga ye look?').\n"
        "3. A call to action exactly like this:\n\n"
        "For more amazing fashion & AI looks, follow us! ðŸ‘‡\n"
        "Instagram: @pooja.perfect_ai\n"
        "Facebook: @pooja.perfectai\n\n"
        "Like â¤ï¸ | Comment ðŸ’¬ | Share ðŸš€ | Save ðŸ“Œ\n\n"
        "4. At least 15-20 highly relevant trending fashion and beauty hashtags at the bottom (e.g., #fashion #ootd #indianstyle #saree #beauty #poojaperfectai etc.). "
        "Do not include any extra text outside the caption itself."
    )
    
    content_to_pass = None
    uploaded_file = None
    
    try:
        if is_video:
            print("Uploading video to Gemini...")
            uploaded_file = client.files.upload(file=media_path)
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(3)
                uploaded_file = client.files.get(name=uploaded_file.name)
            content_to_pass = uploaded_file
        else:
            content_to_pass = Image.open(media_path)
            
        for model_name in GEMINI_MODELS:
            for attempt in range(1, 4):
                try:
                    print(f"Attempt {attempt} with model {model_name}...")
                    response = client.models.generate_content(
                        model=model_name,
                        contents=[content_to_pass, prompt]
                    )
                    caption = response.text
                    if caption:
                        print("Caption generated successfully!\n")
                        print(caption)
                        print("\n" + "="*50 + "\n")
                        return caption
                except Exception as e:
                    print(f"Gemini error on attempt {attempt} with {model_name}: {e}")
                    time.sleep(3)
    finally:
        if uploaded_file:
            try:
                client.files.delete(name=uploaded_file.name)
                print("Cleaned up video from Gemini storage.")
            except:
                pass
                
    return "What a stunning look! ðŸ˜âœ¨\n\nFor more amazing fashion & AI looks, follow us! ðŸ‘‡\nInstagram: @pooja.perfect_ai\nFacebook: @pooja.perfectai\n\nLike â¤ï¸ | Comment ðŸ’¬ | Share ðŸš€ | Save ðŸ“Œ\n\n#fashion #indianfashion #ootd #saree #beauty #poojaperfectai"

def get_ig_account_id():
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}?fields=instagram_business_account&access_token={FB_ACCESS_TOKEN}"
    res = requests.get(url).json()
    if 'instagram_business_account' in res:
        return res['instagram_business_account']['id']
    else:
        print(f"âŒ Error getting IG Account ID: {res}")
        return None

def post_fb_feed(caption, image_url):
    print("Posting to Facebook Feed (Photo)...")
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/photos"
    payload = {
        'url': image_url,
        'message': caption,
        'access_token': FB_ACCESS_TOKEN
    }
    res = requests.post(url, data=payload).json()
    if 'id' in res:
        print(f"âœ… FB Feed Success (ID: {res['id']})")
        return True
    else:
        print(f"âŒ FB Feed Failed: {res}")
        return False

def post_fb_video(caption, video_url):
    print("Posting to Facebook Feed (Video)...")
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/videos"
    payload = {
        'file_url': video_url,
        'description': caption,
        'access_token': FB_ACCESS_TOKEN
    }
    res = requests.post(url, data=payload).json()
    if 'id' in res:
        print(f"âœ… FB Video Success (ID: {res['id']})")
        return True
    else:
        print(f"âŒ FB Video Failed: {res}")
        return False

def post_fb_story(image_url):
    print("Posting to Facebook Story (2-step method)...")
    upload_url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/photos"
    upload_payload = {
        'url': image_url,
        'published': 'false',
        'access_token': FB_ACCESS_TOKEN
    }
    upload_res = requests.post(upload_url, data=upload_payload).json()
    photo_id = upload_res.get('id')
    if not photo_id:
        print(f"âŒ FB Story Failed (photo upload step): {upload_res}")
        return False
    print(f"Uploaded unpublished photo for story (photo_id: {photo_id})")
    story_url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/photo_stories"
    story_payload = {
        'photo_id': photo_id,
        'access_token': FB_ACCESS_TOKEN
    }
    story_res = requests.post(story_url, data=story_payload).json()
    if story_res.get('success') or 'post_id' in story_res or 'id' in story_res:
        print(f"âœ… FB Story Success: {story_res}")
        return True
    else:
        print(f"âŒ FB Story Failed (photo_stories step): {story_res}")
        return False

def post_ig_media(ig_account_id, caption, media_url, is_story=False, is_video=False):
    target = "Story" if is_story else ("Reel" if is_video else "Feed")
    print(f"Posting to Instagram {target}...")
    media_endpoint_url = f"https://graph.facebook.com/v20.0/{ig_account_id}/media"
    payload = {'access_token': FB_ACCESS_TOKEN}
    
    if is_video:
        payload['video_url'] = media_url
        if is_story:
            payload['media_type'] = 'STORIES'
        else:
            payload['media_type'] = 'REELS'
            payload['caption'] = caption
    else:
        payload['image_url'] = media_url
        if is_story:
            payload['media_type'] = 'STORIES'
        else:
            payload['caption'] = caption
            
    res = requests.post(media_endpoint_url, data=payload).json()
    if 'id' not in res:
        print(f"âŒ IG Upload Error: {res}")
        return False
        
    container_id = res['id']
    print(f"Container Created: {container_id}. Waiting for processing...")
    
    if is_video:
        status = "IN_PROGRESS"
        while status != "FINISHED":
            time.sleep(10)
            status_res = requests.get(f"https://graph.facebook.com/v20.0/{container_id}?fields=status_code&access_token={FB_ACCESS_TOKEN}").json()
            status = status_res.get('status_code', 'ERROR')
            print(f"Video Status: {status}")
            if status == "ERROR" or status == "EXPIRED":
                print(f"âŒ Video Processing Failed!")
                return False
    else:
        time.sleep(25)
    
    publish_url = f"https://graph.facebook.com/v20.0/{ig_account_id}/media_publish"
    pub_payload = {
        'creation_id': container_id,
        'access_token': FB_ACCESS_TOKEN
    }
    pub_res = requests.post(publish_url, data=pub_payload).json()
    if 'id' in pub_res:
        print(f"âœ… IG {target} Published Successfully! (ID: {pub_res['id']})")
        return True
    else:
        print(f"âŒ IG Publish Error: {pub_res}")
        return False

def handle_failure(media_info):
    print("âŒ Post failed. Attempting to rollback...")
    if media_info["type"] == "local":
        print("Moving media back to images folder...")
        os.rename(media_info["local_path"], media_info["original_path"])
        
        # Remove from history
        base_name = os.path.splitext(os.path.basename(media_info["original_path"]))[0]
        history = load_history()
        if base_name in history:
            del history[base_name]
            save_history(history)
            
        git_commit_and_push(f"Rollback: Moved back to images: {os.path.basename(media_info['original_path'])}")
    elif media_info["type"] == "catbox":
        print("Restoring Catbox URL to top of reels_urls.txt...")
        url = media_info["media_url"]
        urls = []
        if os.path.exists(REELS_FILE):
            with open(REELS_FILE, "r") as f:
                urls = [line.strip() for line in f.readlines() if line.strip()]
        urls.insert(0, url)
        with open(REELS_FILE, "w") as f:
            f.write("\n".join(urls))
        git_commit_and_push("Rollback: Restored failed Catbox URL")

if __name__ == "__main__":
    try:
        # Cleanup previously posted files to avoid large repo size
        if os.path.exists(POSTED_FOLDER):
            files = os.listdir(POSTED_FOLDER)
            if files:
                for f in files:
                    os.remove(os.path.join(POSTED_FOLDER, f))
                git_commit_and_push("Cleaned up old posted media")
        
        media_info = get_next_media()
        print(f"Media URL for Graph API: {media_info['media_url']}")
        
        caption = generate_caption(media_info["local_path"])
        
        ig_account_id = get_ig_account_id()
        if not ig_account_id:
            raise Exception("No Instagram account linked to the page.")
            
        success = False
        
        # Post to Instagram (Reel or Feed)
        if post_ig_media(ig_account_id, caption, media_info["media_url"], is_story=False, is_video=media_info["is_video"]):
            success = True
            
        # Post to Instagram Story
        post_ig_media(ig_account_id, caption, media_info["media_url"], is_story=True, is_video=media_info["is_video"])
        
        # Post to Facebook
        if media_info["is_video"]:
            if post_fb_video(caption, media_info["media_url"]):
                success = True
        else:
            if post_fb_feed(caption, media_info["media_url"]):
                success = True
            post_fb_story(media_info["media_url"])
        
        if success:
            print("âœ… All posts done successfully!")
        else:
            handle_failure(media_info)
            
        # Delete temp video if exists
        if os.path.exists(TEMP_VIDEO):
            os.remove(TEMP_VIDEO)

    except Exception as e:
        print(f"An error occurred: {e}")
        exit(1)
