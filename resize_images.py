import os
import glob
from PIL import Image

def crop_to_4_5(image_path):
    try:
        img = Image.open(image_path)
        w, h = img.size
        
        target_ratio = 4 / 5
        current_ratio = w / h
        
        # Already 4:5
        if abs(current_ratio - target_ratio) < 0.01:
            return
            
        if current_ratio > target_ratio:
            # Too wide
            new_w = int(h * target_ratio)
            left = (w - new_w) / 2
            right = (w + new_w) / 2
            top = 0
            bottom = h
        else:
            # Too tall
            new_h = int(w / target_ratio)
            top = (h - new_h) / 2
            bottom = (h + new_h) / 2
            left = 0
            right = w
            
        img_cropped = img.crop((left, top, right, bottom))
        # Ensure RGB mode to save as jpg or png safely
        if img_cropped.mode != 'RGB':
            img_cropped = img_cropped.convert('RGB')
        img_cropped.save(image_path)
        print(f"Resized {os.path.basename(image_path)}")
    except Exception as e:
        print(f"Error resizing {os.path.basename(image_path)}: {e}")

image_dir = r"d:\Online\DTF STICKER LISTING\Auto-Insta-Pooja\images\*.*"
images = glob.glob(image_dir)
for image_path in images:
    crop_to_4_5(image_path)

print("All images cropped to 4:5 ratio!")
