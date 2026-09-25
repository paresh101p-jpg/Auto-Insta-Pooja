import os
import time
import subprocess
import requests
from google import genai
from PIL import Image

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

def get_next_image():
    if not os.path.exists(IMAGES_FOLDER):
        os.makedirs(IMAGES_FOLDER)
    files = sorted([
        f for f in os.listdir(IMAGES_FOLDER)
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
    ])
    if not files:
        raise Exception("No images left in 'images/' folder! Please upload more images.")
    chosen = os.path.join(IMAGES_FOLDER, files[0])
    print(f"Using image: {chosen} ({len(files)} remaining)")
    return chosen

def generate_caption(image_path):
    print("Reading Hindi text from the image using Gemini Vision...")
    prompt = (
        "You are an expert Instagram Social Media Manager for a devotional/spiritual account. Look at the image provided. "
        "First, extract the exact Hindi text written on the image. "
        "Then, write a long, engaging Instagram caption in a mix of Hindi and English (Hinglish) based on that text. "
        "Your response MUST be the final Instagram caption, formatted beautifully with emojis. "
        "Include the following elements in this exact order:\n"
        "1. The exact Hindi text from the image at the very top.\n"
        "2. A 3-4 line beautiful, deep devotional thought inspired by the text in Hinglish.\n"
        "3. A call to action exactly like this:\n\n"
        "Aise hi daily darshan aur thoughts ke liye follow karein! 👇\n"
        "👉 @pooja.perfect_ai\n\n"
        "Like ❤️ | Comment 💬 | Share 🚀 | Save 📌\n\n"
        "4. At least 15-20 highly relevant spiritual hashtags at the bottom (e.g., #bhakti #darshan #pooja #krishna #mahadev etc.). "
        "Do not include any extra text outside the caption itself."
    )
    img = Image.open(image_path)
    
    for model_name in GEMINI_MODELS:
        for attempt in range(1, 4):
            try:
                print(f"Attempt {attempt} with model {model_name}...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=[img, prompt]
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
                
    return "Beautiful Devotional Thought. 🙏✨\n\nFollow us for daily positive thoughts.\n\n#bhakti #devotion #pooja #spirituality #peace"

def get_ig_account_id():
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}?fields=instagram_business_account&access_token={FB_ACCESS_TOKEN}"
    res = requests.get(url).json()
    if 'instagram_business_account' in res:
        return res['instagram_business_account']['id']
    else:
        print(f"❌ Error getting IG Account ID: {res}")
        return None

def post_fb_feed(caption, image_url):
    print("Posting to Facebook Feed...")
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/photos"
    payload = {
        'url': image_url,
        'message': caption,
        'access_token': FB_ACCESS_TOKEN
    }
    res = requests.post(url, data=payload).json()
    if 'id' in res:
        print(f"✅ FB Feed Success (ID: {res['id']})")
        return True
    else:
        print(f"❌ FB Feed Failed: {res}")
        return False

def post_fb_story(image_url):
    print("Posting to Facebook Story...")
    # Method 1: photo_stories
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/photo_stories"
    payload = {'url': image_url, 'access_token': FB_ACCESS_TOKEN}
    res = requests.post(url, data=payload).json()
    if 'id' in res:
        print(f"✅ FB Story Success (ID: {res['id']})")
        return True
    print(f"photo_stories failed: {res.get('error', {}).get('message', '')}")
    
    # Method 2: Try as a regular photo with no_story=False
    print("Trying alternate FB Story method...")
    url2 = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/photos"
    payload2 = {
        'url': image_url,
        'published': 'false',
        'no_story': 'false',
        'access_token': FB_ACCESS_TOKEN
    }
    res2 = requests.post(url2, data=payload2).json()
    if 'id' in res2:
        print(f"✅ FB Story (Method 2) Success (ID: {res2['id']})")
        return True
    else:
        print(f"❌ FB Story Failed (both methods): {res2}")
        return False

def post_ig_media(ig_account_id, caption, image_url, is_story=False):
    target = "Story" if is_story else "Feed"
    print(f"Posting to Instagram {target}...")
    
    # 1. Upload media container
    media_url = f"https://graph.facebook.com/v20.0/{ig_account_id}/media"
    payload = {
        'image_url': image_url,
        'access_token': FB_ACCESS_TOKEN
    }
    if is_story:
        payload['media_type'] = 'STORIES'
    else:
        payload['caption'] = caption
        
    res = requests.post(media_url, data=payload).json()
    if 'id' not in res:
        print(f"❌ IG Upload Error: {res}")
        return False
        
    container_id = res['id']
    print(f"Container Created: {container_id}. Waiting for processing...")
    
    # Wait for processing
    time.sleep(25)
    
    # 2. Publish container
    publish_url = f"https://graph.facebook.com/v20.0/{ig_account_id}/media_publish"
    pub_payload = {
        'creation_id': container_id,
        'access_token': FB_ACCESS_TOKEN
    }
    pub_res = requests.post(publish_url, data=pub_payload).json()
    if 'id' in pub_res:
        print(f"✅ IG {target} Published Successfully! (ID: {pub_res['id']})")
        return True
    else:
        print(f"❌ IG Publish Error: {pub_res}")
        return False

def delete_posted_image(image_path):
    print(f"Deleting image from GitHub: {image_path}")
    try:
        subprocess.run(["git", "config", "--global", "user.name", "Auto Insta Bot"], check=True)
        subprocess.run(["git", "config", "--global", "user.email", "actions@github.com"], check=True)
        subprocess.run(["git", "rm", image_path], check=True)
        subprocess.run(["git", "commit", "-m", f"Auto-deleted {os.path.basename(image_path)} after posting"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("✅ Image successfully deleted from repository.")
    except Exception as e:
        print(f"❌ Error deleting image from git: {e}")

if __name__ == "__main__":
    try:
        image_path = get_next_image()
        image_filename = os.path.basename(image_path)
        
        # Raw GitHub URL - ensure this repository is PUBLIC or use a different hosting method
        image_url = f"{GITHUB_REPO_RAW_URL}{IMAGES_FOLDER}/{image_filename}"
        print(f"Image URL for Graph API: {image_url}")
        
        caption = generate_caption(image_path)
        
        ig_account_id = get_ig_account_id()
        if not ig_account_id:
            raise Exception("No Instagram account linked to the page.")
            
        success = False
        
        # Post to Instagram Feed
        if post_ig_media(ig_account_id, caption, image_url, is_story=False):
            success = True
            
        # Post to Instagram Story
        post_ig_media(ig_account_id, caption, image_url, is_story=True)
        
        # Post to Facebook Feed
        if post_fb_feed(caption, image_url):
            success = True
            
        # Post to Facebook Story
        post_fb_story(image_url)
        
        if success:
            print("⏳ All posts done. Waiting 5 minutes before deleting image from GitHub...")
            time.sleep(300) # Give IG time to fetch it completely
            delete_posted_image(image_path)
        else:
            print("❌ Post failed. Not deleting the image.")

    except Exception as e:
        print(f"An error occurred: {e}")
        exit(1)
