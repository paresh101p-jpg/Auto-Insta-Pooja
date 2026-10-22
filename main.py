import os
import sys
import random
import time
import subprocess
import requests
from google import genai
from PIL import Image, ImageFilter
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
GEMINI_MODELS = ["gemini-3.8-flash", "gemini-3.8-pro", "gemini-3.7-flash"]
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
        subprocess.run(["git", "config", "user.email", "actions@github.com"], check=False)
        subprocess.run(["git", "config", "user.name", "Auto Insta Bot"], check=False)
        subprocess.run(["git", "add", "-A"], check=False)
        subprocess.run(["git", "commit", "-m", commit_message], check=False)
        for _ in range(3):
            subprocess.run(["git", "pull", "--rebase", "origin", "master"], check=False)
            res = subprocess.run(["git", "push"], check=False)
            if res.returncode == 0:
                print(f"Git Push Success: {commit_message}")
                return
            time.sleep(2)
    except Exception as e:
        print(f"Git push warning: {e}")

def mark_url_as_used(url, is_video):
    filename = "reels_urls.txt" if is_video else "images_urls.txt"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            urls = [line.strip() for line in f.readlines() if line.strip()]
        if url in urls:
            urls.remove(url)
            with open(filename, "w") as f:
                f.write("\n".join(urls))
            with open("used_urls.txt", "a") as uf:
                uf.write(url + "\n")
            git_commit_and_push(f"Used and removed URL from {filename}")

def reload_urls_from_backup_if_needed(filename, is_video):
    """If the active URL file is empty or missing, reload and shuffle all URLs from the master backup for an infinite cycle."""
    backup_file = "reels_urls_backup.txt" if is_video else "images_urls_backup.txt"
    urls = []
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8", errors="ignore") as f:
            urls = [line.strip() for line in f.readlines() if line.strip()]
            
    # If active file already has URLs, return immediately without any changes
    if urls:
        return urls
        
    # Active file is empty: Check if master backup exists
    if os.path.exists(backup_file):
        print(f"⚠️ {filename} is empty (all posts completed)! Auto-Recycling from {backup_file}...")
        with open(backup_file, "r", encoding="utf-8", errors="ignore") as f:
            backup_urls = [line.strip() for line in f.readlines() if line.strip()]
            
        if backup_urls:
            unique_urls = list(dict.fromkeys(backup_urls))
            import random
            random.shuffle(unique_urls)
            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(unique_urls) + "\n")
            print(f"✅ Auto-Recycle Success: Reloaded and shuffled {len(unique_urls)} URLs from {backup_file} into {filename}!")
            
            # Archive used_urls.txt to cycle archive to prevent unbounded file growth
            if os.path.exists("used_urls.txt"):
                try:
                    with open("used_urls_cycle_archive.txt", "a", encoding="utf-8") as af:
                        with open("used_urls.txt", "r", encoding="utf-8", errors="ignore") as uf:
                            af.write(uf.read())
                    with open("used_urls.txt", "w", encoding="utf-8") as uf:
                        uf.write("")
                    print("✅ Archived and reset used_urls.txt for new cycle.")
                except Exception as ex:
                    print(f"Notice: used_urls archive: {ex}")
                    
            git_commit_and_push(f"Auto-Recycle: Reloaded {len(unique_urls)} URLs from {backup_file} into {filename}")
            return unique_urls
            
    return []

def get_next_media():
    import random
    import requests
    
    last_type_file = "last_post_type.txt"
    last_type = "REEL"
    if os.path.exists(last_type_file):
        with open(last_type_file, "r") as f:
            last_type = f.read().strip()
            
    next_type = "REEL" if last_type == "IMAGE" else "IMAGE"
    print(f"Last post was {last_type}. Now attempting to post {next_type}...")
    

    def get_from_file(filename, is_video):
        urls = reload_urls_from_backup_if_needed(filename, is_video)
        if urls:
            attempts = 0
            while urls and attempts < 5:
                chosen_url = random.choice(urls)
                
                temp_ext = ".mp4" if is_video else ".jpg"
                temp_file = "download_temp_media" + temp_ext
                min_size = 200 * 1024 if is_video else 25 * 1024
                print(f"Downloading from {chosen_url} (min required size: {min_size // 1024} KB)...")
                
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                
                import time
                import subprocess
                success_download = False
                is_404 = False
                
                # 1. Primary Engine: Native curl (HTTP/2 & TLS 1.3 stack, 100% resilient on GitHub Actions Azure runners)
                try:
                    cmd = [
                        "curl", "-s", "-L", "-f",
                        "--connect-timeout", "4",
                        "--max-time", "12",
                        "--retry", "1",
                        "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                        "-o", temp_file,
                        chosen_url
                    ]
                    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
                    if res.returncode == 0 and os.path.exists(temp_file):
                        actual_size = os.path.getsize(temp_file)
                        if actual_size >= min_size:
                            print(f"[OK] Successfully downloaded media via native curl ({actual_size / 1024:.1f} KB)")
                            success_download = True
                except Exception as ce:
                    print(f"Notice: curl engine fallback triggered ({ce})")

                # 2. Fallback 1: urllib.request (uses distinct socket implementation)
                if not success_download:
                    try:
                        import urllib.request
                        import urllib.error
                        req = urllib.request.Request(
                            chosen_url,
                            headers={
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                                "Accept": "*/*"
                            }
                        )
                        with urllib.request.urlopen(req, timeout=5) as resp:
                            if resp.status == 200:
                                with open(temp_file, "wb") as f:
                                    while True:
                                        chunk = resp.read(65536)
                                        if not chunk:
                                            break
                                        f.write(chunk)
                                actual_size = os.path.getsize(temp_file) if os.path.exists(temp_file) else 0
                                if actual_size >= min_size:
                                    print(f"[OK] Successfully downloaded media via urllib ({actual_size / 1024:.1f} KB)")
                                    success_download = True
                    except urllib.error.HTTPError as he:
                        if he.code == 404:
                            is_404 = True
                            print(f"URL returned 404: {chosen_url}")
                    except Exception as ue:
                        print(f"Notice: urllib fallback failed ({ue})")

                # 3. Fallback 2: requests with Connection: close and streaming
                if not success_download and not is_404:
                    try:
                        import requests
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                            'Accept': '*/*',
                            'Connection': 'close'
                        }
                        with requests.get(chosen_url, headers=headers, stream=True, timeout=5) as r:
                            if r.status_code == 200:
                                with open(temp_file, "wb") as f:
                                    for chunk in r.iter_content(chunk_size=65536):
                                        if chunk:
                                            f.write(chunk)
                                actual_size = os.path.getsize(temp_file) if os.path.exists(temp_file) else 0
                                if actual_size >= min_size:
                                    print(f"[OK] Successfully downloaded media via requests ({actual_size / 1024:.1f} KB)")
                                    success_download = True
                            elif r.status_code == 404:
                                is_404 = True
                                print(f"URL returned 404: {chosen_url}")
                    except Exception as re_err:
                        print(f"Notice: requests fallback failed ({re_err})")

                if not success_download:
                    print(f"Failed to download healthy media from {chosen_url}.")
                    if os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except:
                            pass
                    if is_404 and chosen_url in urls:
                        urls.remove(chosen_url)
                        with open(filename, "w", encoding="utf-8") as f:
                            f.write("\n".join(urls) + "\n")
                    attempts += 1
                    time.sleep(1)
                    continue

                # Media downloaded successfully!
                return {
                    "type": "catbox",
                    "local_path": temp_file,
                    "media_url": chosen_url,
                    "is_video": is_video,
                    "original_path": None
                }
            if attempts >= 5:
                print("⚠️ External media URLs unreachable (Catbox connection timeout/outage). Activating repository media fallback...")
                candidates = ["fallback_media.mp4", "temp_media.mp4"] if is_video else ["fallback_media.jpg", "temp_media.jpg"]
                for fb in candidates:
                    if os.path.exists(fb) and os.path.getsize(fb) >= min_size:
                        cdn_url = f"https://cdn.jsdelivr.net/gh/paresh101p-jpg/Auto-Insta-Pooja@master/{fb}"
                        print(f"✅ Loaded repository fallback media: {fb} ({cdn_url})")
                        return {
                            "type": "repo_fallback",
                            "local_path": fb,
                            "media_url": cdn_url,
                            "is_video": is_video,
                            "original_path": None
                        }
                raise Exception("Failed to download healthy media after trying 5 different URLs and no local fallback available.")
        return None
    if next_type == "IMAGE":
        res = get_from_file("images_urls.txt", False)
        if res:
            with open(last_type_file, "w") as f: f.write("IMAGE")
            return res
        print("No images left, falling back to reel...")
        next_type = "REEL"

    if next_type == "REEL":
        res = get_from_file("reels_urls.txt", True)
        if res:
            with open(last_type_file, "w") as f: f.write("REEL")
            return res
        
        print("No reels left, falling back to image...")
        res = get_from_file("images_urls.txt", False)
        if res:
            with open(last_type_file, "w") as f: f.write("IMAGE")
            return res
            
    raise Exception("No media available at all! Please upload new media.")

def clean_caption(text):
    if not text:
        return ""
    import re
    # Remove markdown horizontal rules (---, ***, ___)
    cleaned = re.sub(r'^\s*[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    cleaned = re.sub(r'---\s*', '\n\n', cleaned)

    # Remove labels like "**PART 1 — HOOK:**", "PART 1: ...", etc.
    cleaned = re.sub(r'(?i)\*{0,2}(?:---\s*)?\*{0,2}PART\s*\d+\s*[—–\-:]+[^\n:]*:\*{0,2}', '', cleaned)
    cleaned = re.sub(r'(?i)\*{0,2}(?:HOOK & VIVID VISUAL OBSERVATION|HOOK|VIVID VISUAL OBSERVATION|OBSERVATION|STORY/DETAIL|STORY|DETAIL|FASHION STORY|AUDIENCE ENGAGEMENT|ENGAGEMENT|CALL TO ACTION|HASHTAGS)\s*:\*{0,2}', '', cleaned)

    # Remove square brackets around hashtags: [#tag] -> #tag
    cleaned = re.sub(r'\[\s*(#[a-zA-Z0-9_\u0900-\u097F]+)\s*\]', r'\1', cleaned)
    cleaned = re.sub(r'\[(#[^\]]+)\]', r'\1', cleaned)

    # Clean up empty markdown bold tags like ****
    cleaned = re.sub(r'\*\*\s*\*\*', '', cleaned)

    # Enforce Instagram maximum hashtag limit (30 max permitted by IG API)
    hashtags = re.findall(r'#[a-zA-Z0-9_\u0900-\u097F]+', cleaned)
    if len(hashtags) > 22:
        excess = hashtags[22:]
        for tag in excess:
            cleaned = re.sub(re.escape(tag) + r'(?:\s+|$)', '', cleaned)

    # Normalize excessive newlines (max 2 consecutive newlines)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()

def generate_caption(media_path):
    is_video = media_path.lower().endswith('.mp4')
    print(f"Analyzing {'video' if is_video else 'image'} using Gemini Vision...")
    prompt = (
        "You are a top-tier Fashion, Beauty & Lifestyle Instagram Content Creator with 10 million followers.\n\n"
        "Analyze the provided visual media (photo/video) very carefully and base your caption ENTIRELY on what is ACTUALLY visible:\n"
        "- OUTFIT & DETAILS: Identify the exact outfit style (saree, lehenga, gown, western dress, suit, co-ord set, casual), its vibrant colors, fabric texture (silk, georgette, velvet, chiffon, satin, organza), and intricate work (embroidery, zari, sequins, mirror work, prints).\n"
        "- STYLING & ACCESSORIES: Describe the jewelry (necklace, jhumkas, maang tikka, bangles, rings), hair styling, makeup look, and expressions in rich detail.\n"
        "- BACKDROP & AESTHETICS: Notice the setting (royal palace, heritage courtyard, festive lighting, modern studio, natural outdoors) and the luxurious, elegant ambiance.\n\n"
        "Write a LONG, POETIC, DEEPLY ENGAGING Instagram caption in a natural, vibrant mix of Hindi and English (Hinglish) that captivates followers.\n\n"
        "Structure the narrative smoothly (WITHOUT WRITING ANY LABELS OR HEADINGS LIKE 'PART 1', 'HOOK:', ETC.):\n\n"
        "1. HOOK & VIVID VISUAL OBSERVATION (3-4 lines):\n"
        "Start with an attention-grabbing, glamorous statement or compliment that stops the scroll instantly. Vividly describe what makes this visual so mesmerizing — the radiant look, colors, drape, and stunning presence.\n\n"
        "2. FASHION STORY & STYLING INSPIRATION (5-7 lines):\n"
        "Dive deep into the outfit details in an inspiring storytelling tone. Talk about the craftsmanship, the elegance of the silhouette, how the accessories elevate the entire ensemble, and what occasion this gorgeous look is perfect for (wedding guest, festive glam, cocktail evening, red carpet). Make the reader truly feel the magic of Indian & contemporary fashion.\n\n"
        "3. AUDIENCE ENGAGEMENT (2-3 lines):\n"
        "Ask 2 fun, engaging questions about the look (e.g. 'Aapko is look ka kaunsa element sabse best laga?' or 'Rate this royal look from 1 to 10 in the comments!'). Encourage everyone to comment with their favorite emojis.\n\n"
        "4. CALL TO ACTION (Include EXACTLY this block):\n"
        "For more amazing fashion & AI looks, follow us! 👇🔥\n"
        "Instagram: @pooja.perfect_ai\n"
        "Facebook: @pooja.perfectai\n\n"
        "Like ❤️ | Comment 💬 | Share 🚀 | Save 📌\n\n"
        "5. HASHTAGS (BASED ON THE VISUAL):\n"
        "Generate 12 to 15 UNIQUE, HIGHLY SPECIFIC, and TRENDING hashtags based directly on what you ACTUALLY see in this specific image/video (e.g., specific outfit type, color, fabric, jewelry, festive theme, aesthetic). Write them as plain space-separated hashtags (NO brackets, NO commas). ALWAYS append at the very end: #poojaperfectai #fashion #ootd #beauty #indianfashion #styleinspo\n\n"
        "CRITICAL FORMATTING INSTRUCTIONS (STRICTLY ENFORCED):\n"
        "- NEVER output section labels, numbers, or headings like 'PART 1', 'PART 2', 'PART 3', 'PART 4', 'PART 5', 'HOOK:', 'STORY:', 'AUDIENCE ENGAGEMENT:', 'CALL TO ACTION:', 'HASHTAGS:'.\n"
        "- NEVER include markdown divider lines like '---' or '***'.\n"
        "- NEVER put hashtags in square brackets like '[#tag]'.\n"
        "- Total caption length should be 150-250 words minimum.\n"
        "- Use emojis naturally throughout to make the caption visually attractive.\n"
        "- Output ONLY the final, seamless Instagram caption ready to post."
    )
    
    content_to_pass = None
    uploaded_file = None
    
    try:
        if is_video:
            print("Uploading video to Gemini...")
            uploaded_file = client.files.upload(file=media_path)
            import time
            wait_attempts = 0
            while uploaded_file.state.name != "ACTIVE" and wait_attempts < 20:
                if uploaded_file.state.name == "FAILED":
                    raise Exception("Gemini video processing failed.")
                print(f"Waiting for video processing in Gemini... Status: {uploaded_file.state.name}")
                time.sleep(3)
                wait_attempts += 1
                uploaded_file = client.files.get(name=uploaded_file.name)
            content_to_pass = uploaded_file
        else:
            from PIL import Image
            img = Image.open(media_path).convert("RGB")
            img.load()
            content_to_pass = img
            
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
                        caption = clean_caption(caption)
                        print("Caption generated successfully from visual!\n")
                        print(caption)
                        print("\n" + "="*50 + "\n")
                        return caption
                except Exception as e:
                    print(f"Gemini error on attempt {attempt} with {model_name}: {e}")
                    import time
                    time.sleep(3)

        # Fallback: Dynamically discover working models if predefined ones fail
        try:
            print("Attempting dynamic model discovery via client.models.list()...")
            discovered_models = []
            for m in client.models.list():
                m_name = m.name.replace("models/", "") if hasattr(m, "name") and m.name else ""
                supported = getattr(m, "supported_actions", []) or getattr(m, "supported_generation_methods", []) or []
                if m_name and ("generateContent" in supported or not supported) and m_name not in GEMINI_MODELS:
                    discovered_models.append(m_name)
            
            print(f"Discovered available models: {discovered_models[:5]}")
            for m_name in discovered_models:
                try:
                    print(f"Attempting with dynamically discovered model {m_name}...")
                    response = client.models.generate_content(
                        model=m_name,
                        contents=[content_to_pass, prompt]
                    )
                    if response.text:
                        caption = clean_caption(response.text)
                        print(f"Caption generated successfully using dynamic model {m_name}!\n")
                        print(caption)
                        print("\n" + "="*50 + "\n")
                        return caption
                except Exception as dyn_e:
                    print(f"Gemini error with dynamic model {m_name}: {dyn_e}")
        except Exception as list_e:
            print(f"Could not list models: {list_e}")
    finally:
        if uploaded_file:
            try:
                client.files.delete(name=uploaded_file.name)
                print("Cleaned up video from Gemini storage.")
            except:
                pass
                
    print("⚠️ WARNING: All Gemini Vision attempts failed, using fallback caption!")
    return clean_caption("""What a stunning and glamorous look! ✨ Royal vibes, effortless elegance, and timeless beauty all in one frame. Perfect inspiration for your next special occasion! 💃✨

For more amazing fashion & AI looks, follow us! 👇🔥
Instagram: @pooja.perfect_ai
Facebook: @pooja.perfectai

Like ❤️ | Comment 💬 | Share 🚀 | Save 📌

#poojaperfectai #fashion #ootd #beauty #indianfashion #styleinspo #ethnicwear #festivelook #glam #instafashion""")

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

def post_fb_video(caption, local_file):
    print("Posting to Facebook Feed (Video) via direct file upload...")
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/videos"
    try:
        with open(local_file, "rb") as vf:
            files = {
                'source': (local_file, vf, 'video/mp4')
            }
            payload = {
                'description': caption,
                'access_token': FB_ACCESS_TOKEN
            }
            res = requests.post(url, data=payload, files=files).json()
            
        if 'id' in res:
            print(f"✅ FB Video Success (ID: {res['id']})")
            return True
        else:
            print(f"❌ FB Video Failed: {res}")
            return False
    except Exception as e:
        print(f"❌ Error uploading FB Video: {e}")
        return False



def post_fb_video_story(local_file):
    print("Posting to Facebook Story (Video) via 3-step upload...")
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/video_stories"
    
    try:
        import os
        file_size = os.path.getsize(local_file)
        
        # Step 1: Start - initialize the upload session
        start_payload = {
            'upload_phase': 'start',
            'access_token': FB_ACCESS_TOKEN,
            'file_size': file_size
        }
        res_start = requests.post(url, data=start_payload).json()
        print(f"FB Video Story Start response: {res_start}")
        if 'video_id' not in res_start:
            print(f"❌ FB Video Story Start Failed: {res_start}")
            return False
            
        video_id = res_start['video_id']
        upload_url = res_start['upload_url']
        
        # Step 2: Transfer - upload the actual video bytes
        # Use raw binary upload with Content-Type header (NOT multipart)
        with open(local_file, "rb") as vf:
            video_data = vf.read()
        
        upload_headers = {
            'Authorization': f'OAuth {FB_ACCESS_TOKEN}',
            'offset': '0',
            'file_size': str(file_size)
        }
        res_up = requests.post(upload_url, data=video_data, headers=upload_headers)
        print(f"FB Video Story Upload response: {res_up.status_code} - {res_up.text[:200]}")
            
        # Give Meta's servers time to process the uploaded chunk!
        print("Waiting 30 seconds for Meta to process the video chunk...")
        time.sleep(30)
            
        # Step 3: Finish - publish the story
        finish_payload = {
            'upload_phase': 'finish',
            'access_token': FB_ACCESS_TOKEN,
            'video_id': video_id
        }
        res_finish = requests.post(url, data=finish_payload).json()
        print(f"FB Video Story Finish response: {res_finish}")
        if res_finish.get('success'):
            print(f"✅ FB Video Story Success (ID: {video_id})")
            return True
        else:
            print(f"❌ FB Video Story Finish Failed: {res_finish}")
            return False
    except Exception as e:
        print(f"❌ Error uploading FB Video Story: {e}")
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

def post_ig_media(ig_account_id, caption, media_url, is_story=False, is_video=False, local_file=None):
    target = "Story" if is_story else ("Reel" if is_video else "Feed")
    print(f"Posting to Instagram {target}...")
    media_endpoint_url = f"https://graph.facebook.com/v20.0/{ig_account_id}/media"
    
    # 1. Direct Resumable Binary Upload for Videos (Reels & Video Stories)
    if is_video and local_file and os.path.exists(local_file):
        try:
            file_size = os.path.getsize(local_file)
            print(f"Initiating Direct Resumable Upload for Instagram {target} ({file_size / (1024*1024):.2f} MB)...")
            init_payload = {
                'upload_type': 'resumable',
                'media_type': 'STORIES' if is_story else 'REELS',
                'access_token': FB_ACCESS_TOKEN
            }
            if not is_story:
                init_payload['caption'] = caption
            
            init_res = requests.post(media_endpoint_url, data=init_payload, timeout=20).json()
            if 'id' in init_res and 'uri' in init_res:
                container_id = init_res['id']
                upload_uri = init_res['uri']
                print(f"Resumable container created: {container_id}. Uploading binary stream directly to Meta...")
                
                with open(local_file, "rb") as vf:
                    video_bytes = vf.read()
                    
                upload_headers = {
                    'Authorization': f'OAuth {FB_ACCESS_TOKEN}',
                    'offset': '0',
                    'file_size': str(file_size),
                }
                up_res = requests.post(upload_uri, data=video_bytes, headers=upload_headers, timeout=60)
                print(f"Binary transfer completed with HTTP {up_res.status_code}. Waiting for Meta transcoding...")
                
                status = "IN_PROGRESS"
                wait_count = 0
                while status != "FINISHED" and wait_count < 30:
                    time.sleep(5)
                    wait_count += 1
                    status_res = requests.get(f"https://graph.facebook.com/v20.0/{container_id}?fields=status_code&access_token={FB_ACCESS_TOKEN}", timeout=15).json()
                    status = status_res.get('status_code', 'ERROR')
                    print(f"IG Video Status ({wait_count}/30): {status}")
                    if status == "FINISHED":
                        break
                    if status in ["ERROR", "EXPIRED"]:
                        print(f"❌ IG Resumable Video Processing Failed! Error details: {status_res}")
                        break
                        
                if status == "FINISHED":
                    publish_url = f"https://graph.facebook.com/v20.0/{ig_account_id}/media_publish"
                    pub_res = requests.post(publish_url, data={'creation_id': container_id, 'access_token': FB_ACCESS_TOKEN}, timeout=30).json()
                    if 'id' in pub_res:
                        print(f"✅ IG {target} Published Successfully via Direct Upload! (ID: {pub_res['id']})")
                        return True
                    else:
                        print(f"❌ IG Direct Publish Error: {pub_res}")
                else:
                    print(f"Warning: Direct upload processing status was '{status}'. Falling back to standard URL upload...")
        except Exception as direct_err:
            print(f"Notice: Direct resumable upload exception: {direct_err}. Falling back to URL method...")

    # Standard URL-based container creation (Images and Fallback)
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
        print(f"❌ IG Upload Error: {res}")
        return False
        
    container_id = res['id']
    print(f"Container Created: {container_id}. Waiting for processing...")
    
    if is_video:
        status = "IN_PROGRESS"
        while status != "FINISHED":
            time.sleep(10)
            status_res = requests.get(f"https://graph.facebook.com/v20.0/{container_id}?fields=status_code,status&access_token={FB_ACCESS_TOKEN}").json()
            status = status_res.get('status_code', 'ERROR')
            print(f"Video Status: {status} (Details: {status_res.get('status', 'N/A')})")
            if status == "ERROR" or status == "EXPIRED":
                print(f"❌ Video Processing Failed!")
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
        print(f"✅ IG {target} Published Successfully! (ID: {pub_res['id']})")
        return True
    else:
        print(f"❌ IG Publish Error: {pub_res}")
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


def create_story_image(local_path):
    try:
        img = Image.open(local_path).convert("RGB")
        target_w, target_h = 1080, 1920
        w, h = img.size
        
        # Create a proportionally zoomed background to fill the canvas without stretching
        bg_scale = max(target_w / w, target_h / h)
        bg_w, bg_h = int(w * bg_scale), int(h * bg_scale)
        bg = img.resize((bg_w, bg_h), Image.Resampling.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(radius=30))
        
        # Crop the center of the blurred background
        left = (bg_w - target_w) // 2
        top = (bg_h - target_h) // 2
        bg = bg.crop((left, top, left + target_w, top + target_h))
        
        # Foreground: preserve aspect ratio, fit inside the canvas
        scale = min(target_w / w, target_h / h)
        new_w, new_h = int(w * scale), int(h * scale)
        fg = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Paste foreground into the exact center
        y_offset = (target_h - new_h) // 2
        x_offset = (target_w - new_w) // 2
        bg.paste(fg, (x_offset, y_offset))
        import os
        base_name = os.path.basename(local_path)
        dir_name = os.path.dirname(local_path)
        story_path = os.path.join(dir_name, f"story_{base_name}") if dir_name else f"story_{base_name}"
        bg.save(story_path, quality=95)
        return story_path
    except Exception as e:
        print(f"Error creating story image: {e}")
        return local_path

def upload_to_catbox(file_path):
    try:
        import requests
        print(f"Uploading {file_path} to Catbox for story (timeout 4s)...")
        with open(file_path, 'rb') as f:
            response = requests.post('https://catbox.moe/user/api.php', data={'reqtype': 'fileupload'}, files={'fileToUpload': f}, timeout=4)
        if response.status_code == 200 and response.text.startswith("http"):
            return response.text.strip()
    except Exception as e:
        print(f"Catbox upload failed/skipped: {e}")
    return None

def retry_post(func, *args, **kwargs):
    for attempt in range(1, 4):
        try:
            if func(*args, **kwargs):
                return True
        except Exception as e:
            print(f"⚠️ Exception in attempt {attempt}: {e}")
        if attempt < 3:
            print(f"Retrying in 10 seconds (Attempt {attempt+1}/3)...")
            time.sleep(10)
    return False

if __name__ == "__main__":
    try:
        # Double-post safety lock: Prevent duplicate posts within 45 minutes
        last_post_time_file = "last_posted_timestamp.txt"
        min_interval_seconds = 45 * 60  # 45 minutes
        force_post = os.environ.get("FORCE_POST", "").lower() == "true" or "--force" in sys.argv or os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
        
        if not force_post and os.path.exists(last_post_time_file):
            try:
                with open(last_post_time_file, "r") as f:
                    content = f.read().strip()
                if content:
                    last_ts = float(content)
                    elapsed = time.time() - last_ts
                    if elapsed < min_interval_seconds:
                        minutes_ago = int(elapsed // 60)
                        print(f"⚠️ DOUBLE-POST SAFETY LOCK: A post was already published {minutes_ago} minutes ago (minimum interval is 45 minutes).")
                        print("Skipping execution to prevent duplicate posts. Exiting cleanly.")
                        sys.exit(0)
            except Exception as lock_err:
                print(f"Notice: Double-post lock check: {lock_err}")

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
        caption = clean_caption(caption)
        
        # Affiliate Marketing Rule Splitting
        ig_caption = caption + "\n\n🛒 Check out the link in my Bio!\n#ad #CommissionsEarned"
        fb_caption = caption + "\n\n🛒 Buy my favorite product here: https://link.amazon/A02oaFqo9\n#ad #CommissionsEarned"
        
        ig_account_id = get_ig_account_id()
        if not ig_account_id:
            raise Exception("No Instagram account linked to the page.")
            
        success = False
        
        # Prepare Story URL (if image, create blurred 9:16 background)
        story_url = media_info["media_url"]
        if not media_info["is_video"]:
            story_local = create_story_image(media_info["local_path"])
            if story_local != media_info["local_path"]:
                try:
                    import shutil
                    os.makedirs("posted_images", exist_ok=True)
                    temp_story_name = f"story_temp_{int(time.time())}.jpg"
                    story_git_path = f"posted_images/{temp_story_name}"
                    shutil.copy2(story_local, story_git_path)
                    subprocess.run(["git", "add", "-f", story_git_path], check=False)
                    git_commit_and_push("Upload temporary story image for IG API")
                    print("Waiting 25 seconds for GitHub/CDN to update...")
                    time.sleep(25)
                    cdn_story = f"https://cdn.jsdelivr.net/gh/paresh101p-jpg/Auto-Insta-Pooja@master/{story_git_path}"
                    story_url = cdn_story
                    print(f"Using JSDelivr URL for story: {story_url}")
                except Exception as story_err:
                    print(f"Notice: Story git upload failed: {story_err}. Falling back to original media URL.")
        
        ig_success = False
        fb_success = False
        
        # Post to Instagram Feed/Reel
        if retry_post(post_ig_media, ig_account_id, ig_caption, media_info["media_url"], is_story=False, is_video=media_info["is_video"], local_file=media_info["local_path"]):
            ig_success = True
            
        # Post to Instagram Story (using the story_url which has the blurred background for images)
        retry_post(post_ig_media, ig_account_id, ig_caption, story_url, is_story=True, is_video=media_info["is_video"], local_file=media_info["local_path"] if media_info["is_video"] else None)
        
        # Post to Facebook
        if media_info["is_video"]:
            # Need to ensure post_fb_video exists or just use feed
            if "post_fb_video" in globals():
                if retry_post(post_fb_video, fb_caption, media_info["local_path"]):
                    fb_success = True
            else:
                if retry_post(post_fb_feed, fb_caption, media_info["media_url"]):
                    fb_success = True
            
            if "post_fb_video_story" in globals():
                retry_post(post_fb_video_story, media_info["local_path"])
        else:
            if retry_post(post_fb_feed, fb_caption, media_info["media_url"]):
                fb_success = True
            if "post_fb_story" in globals():
                retry_post(post_fb_story, story_url)
        
        # Only treat as fully successful if Instagram succeeded (never consume queue if IG failed)
        if ig_success:
            print("Successfully posted to Instagram (and Facebook status: {})!".format("Success" if fb_success else "Failed"))
            try:
                with open("last_posted_timestamp.txt", "w") as f:
                    f.write(str(time.time()))
            except Exception as ts_err:
                print(f"Notice: Could not write last_posted_timestamp: {ts_err}")
            if media_info["type"] == "catbox":
                mark_url_as_used(media_info["media_url"], media_info["is_video"])
            else:
                git_commit_and_push("Update last_post_type and timestamp")
        else:
            print("⚠️ Instagram post failed! Keeping media in queue/restoring...")
            if "handle_failure" in globals():
                handle_failure(media_info)
            
        if os.path.exists(TEMP_VIDEO):
            os.remove(TEMP_VIDEO)
        if os.path.exists("story_temp.jpg"):
            os.remove("story_temp.jpg")

    except Exception as e:
        print(f"An error occurred: {e}")
        exit(1)
