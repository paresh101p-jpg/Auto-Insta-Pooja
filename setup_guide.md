# Auto-Instagram & Facebook Cross-Posting Bots Setup Guide

This document serves as a complete memory and reference guide for the automatic Instagram and Facebook posting bots created for **Paresh Padsala** and **Pooja Gupta**.

## 1. Architecture Overview
There are two completely independent bots running on separate GitHub repositories. They **do not and will never mix** because they use completely different Facebook Page IDs, Access Tokens, and GitHub Repositories.

| Feature | Bot 1 (Paresh) | Bot 2 (Pooja) |
| :--- | :--- | :--- |
| **Folder/Repo Name** | `Auto-Insta-Post` | `Auto-Insta-Pooja` |
| **GitHub URL** | `https://github.com/paresh101p-jpg/Auto-Insta-Post` | `https://github.com/paresh101p-jpg/Auto-Insta-Pooja` |
| **FB Page ID** | `361664183691656` | `1313997728621727` |
| **Target Niche** | Devotional/Spiritual Quotes | Fashion & Beauty / Women Outfits |
| **Schedule (IST)** | 09:00 AM, 03:00 PM, 09:00 PM | 09:00 AM, 03:00 PM, 09:00 PM |

---

## 2. Bot Features & Workflow
1. **GitHub Actions:** The bots run completely on GitHub's servers (`schedule.yml`). Your local PC does not need to be turned on.
2. **Media Queue & Selection:** The bot looks in the `images/` directory and picks the **first file in line alphabetically**.
   - If the file is an image (`.jpg`, `.png`), it posts it as a Photo.
   - If the file is a video (`.mp4`), it automatically switches to **Reels Mode** and posts it as an IG Reel, IG Story, and FB Video.
3. **AI Caption Generation (Gemini Vision):**
   - **Paresh Bot:** Reads Hindi text from the image/video, writes a deep spiritual Hinglish caption, adds `@pareshpadsala_`, and appends devotional hashtags.
   - **Pooja Bot:** Analyzes the woman's outfit/style/colors in the image/video, writes a catchy fashion Hinglish caption, adds `@pooja.perfect_ai`, and appends fashion hashtags.
4. **Facebook Feed & Story:** The bot posts photos to Feed & Story, and videos to Video Feed.
5. **Instagram Feed, Reel & Story:** The bot smartly posts photos to Feed/Story, and videos to Reels/Story.
6. **Auto-Cleanup:** **5 minutes (300 seconds)** after successfully posting, the bot automatically deletes the posted media from the GitHub repository to avoid duplicate posts.

---

## 3. Managing Images (Local PC vs GitHub)

**New Clean-PC Workflow (As requested by User):**
1. **Adding New Images/Videos:** Save your new media files into the `images/` folder on your PC.
2. **Uploading:** Tell me (the AI) to "Upload to GitHub" or use `git push`.
3. **Local Deletion:** Once the images are successfully uploaded to GitHub, you can **IMMEDIATELY DELETE** them from your local PC folder. This keeps your PC storage completely empty and clean!
4. **Auto-Deletion on GitHub:** Even though you deleted them from your PC, the images are safely queued on GitHub. The bot will automatically delete them from the GitHub server **5 minutes after posting** them to Instagram/Facebook.

*(Note: Since you are deleting them locally, you do not need to use `git pull` to sync deletions anymore. Just drop new files, push, and delete locally!)*

---

## 4. Generating a Permanent Page Token (For Future Bots)
If you ever need to create a 3rd bot for a new page, follow these exact steps:

### Step A: Graph API Explorer
1. Go to [Facebook Graph API Explorer](https://developers.facebook.com/tools/explorer/).
2. Select your Meta App (e.g., "Auto Post").
3. Click "User or Page" and select your **NEW Facebook Page**. (If it's not there, edit the Business Integrations in your Facebook settings and tick the new page).
4. Ensure permissions include: `pages_show_list`, `business_management`, `instagram_basic`, `instagram_content_publish`, `pages_read_engagement`, `pages_manage_posts`.
5. Copy the generated Short-Lived Access Token and save it in a file named `tokan.txt`.
6. Click "Submit" on `me?fields=id,name` to get your new **Page ID**.

### Step B: Permanent Token Generation
Run the python script provided in your folder using PowerShell. You will need your App ID and App Secret from the Facebook Developer Dashboard.
```powershell
$env:FB_APP_ID="your_app_id"
$env:FB_APP_SECRET="your_app_secret"
$env:FB_PAGE_ID="your_new_page_id"
python generate_fb_token.py
```
This will output a **Permanent Page Token** that never expires.

### Step C: GitHub Secrets
Create a new GitHub Repository and add the following under **Settings > Secrets and variables > Actions**:
- `GEMINI_API_KEY`: Your Google Gemini API Key.
- `FB_ACCESS_TOKEN`: The Permanent Page Token you generated in Step B.

---
*Setup completed and verified on September 25, 2026.*

## 5. Image Generation Rule (CRITICAL)
When I (the AI) am tasked with generating new images for **Auto-Insta-Pooja** (Fashion) or **Auto-Insta-Post** (Devotional/Paresh), I **MUST** generate them in a **1:1 (Square)** aspect ratio.
**Reason:** 1:1 aspect ratio perfectly supports Instagram Feed, Instagram Story, Facebook Feed, and avoids Facebook Story Graph API rejection errors. Do not generate 9:16 images as they will fail the IG Feed API and FB Story API constraints.

## 6. User Interaction Workflow (Strict Rules)
1. **GitHub Uploads:** Do NOT automatically push/upload files to GitHub. Only push changes or upload images to GitHub when the user explicitly commands: "github par upload karo".
2. **Image Generation:** Do NOT randomly generate images. Only generate images when the user explicitly commands: "pooja ki images banao" or "krishna/paresh ki images banao".
3. **Pooja Image Reference (STRICT):** When generating images for Pooja, always use the saved `reference.jpg` and strictly follow these rules:
   - **Neckline (CRITICAL):** The woman must wear a dress with the EXACT SAME V-neckline shape as the reference image. Do NOT change or cover the neckline.
   - **Clothing & Body:** Change the clothing color (e.g. bright red), make it a short dress, and show the waist (kamar).
   - **Pose & Setting:** Change the pose to a playful, dancing, or masti pose. Use a beautiful outdoor background (like a garden).
4. **Paresh Image Reference (STRICT):** When generating images for Paresh, you MUST strictly follow the Real-Life Mockup style:
   - **Background:** A hyper-realistic vintage/rustic background (e.g., old weathered wooden door, wooden block, boat, vintage book, stone wall).
   - **Text (CRITICAL):** The Hindi quote must be painted directly and realistically onto the surface like a natural mural or mockup, perfectly integrated with the texture.
   - **Elements:** Always include exactly TWO peacock feathers (morpankh) and ONE wooden flute (bansuri) resting near the text.
   - **Watermark:** Below the main quote, write the text '@PareshPadsala_' in smaller letters.
5. **Posting Schedule:** Both the Auto-Insta-Pooja and Auto-Insta-Post bots are configured to run 3 times a day strictly at **9:00 AM, 3:00 PM, and 9:00 PM (IST)**.
