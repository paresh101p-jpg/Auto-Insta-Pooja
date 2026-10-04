import os
import glob
from PIL import Image
import concurrent.futures

image_folder = r"E:\Paresh\Auto Post\Auto-Insta-Pooja\images"
files = []
for ext in ('*.jpg', '*.jpeg', '*.png', '*.webp'):
    files.extend(glob.glob(os.path.join(image_folder, '**', ext), recursive=True))

print(f"Found {len(files)} images to compress.")

def compress_image(file_path):
    try:
        size_kb = os.path.getsize(file_path) / 1024
        if size_kb > 150: # Only compress if greater than 150 KB
            with Image.open(file_path) as img:
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                # Resize if larger than 1080x1080 (Instagram standard)
                img.thumbnail((1080, 1080), Image.Resampling.LANCZOS)
                
                # If it's a PNG, changing to JPG format heavily reduces size
                new_path = os.path.splitext(file_path)[0] + ".jpg"
                img.save(new_path, "JPEG", optimize=True, quality=60)
                
                # If the original was not .jpg, delete the original
                if file_path.lower() != new_path.lower():
                    os.remove(file_path)
                    
            return True
    except Exception as e:
        print(f"Failed {file_path}: {e}")
    return False

# Use multithreading for faster processing
compressed_count = 0
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    results = list(executor.map(compress_image, files))
    compressed_count = sum(1 for r in results if r)

print(f"Successfully compressed {compressed_count} images.")
