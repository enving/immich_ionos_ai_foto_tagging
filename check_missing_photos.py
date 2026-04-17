import os
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime
from pathlib import Path

SOURCE_DIR = "/Users/macenving/Pictures/Google Photos"
DEST_DIR = "/Users/macenving/immich-server/library/imported"
TARGET_MONTH = 2
TARGET_YEAR = 2021

def get_date_taken(path):
    try:
        if path.lower().endswith('.heic'):
            return None 
            
        with Image.open(path) as img:
            exif = img._getexif()
            if not exif:
                return None
            
            for tag, value in exif.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "DateTimeOriginal":
                    return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                if decoded == "DateTime":
                     return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except Exception:
        return None
    return None

def scan_dir(directory, label):
    print(f"Scanning {label} ({directory}) for photos from {TARGET_MONTH}/{TARGET_YEAR}...")
    found = {}
    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff')):
                full_path = os.path.join(root, file)
                date = get_date_taken(full_path)
                if date and date.year == TARGET_YEAR and date.month == TARGET_MONTH:
                    unique_id = f"{file}_{os.path.getsize(full_path)}"
                    found[unique_id] = full_path
                    count += 1
                    if count % 10 == 0:
                        print(f"[{label}] Found {count}...", end="\r")
    print(f"\n[{label}] Done. Found {count} matching photos.")
    return found

source_photos = scan_dir(SOURCE_DIR, "SOURCE")
dest_photos = scan_dir(DEST_DIR, "DEST")

print("\n--- Comparison ---")
missing_in_dest = []
for uid, path in source_photos.items():
    if uid not in dest_photos:
        missing_in_dest.append(path)

print(f"Photos in Source: {len(source_photos)}")
print(f"Photos in Dest: {len(dest_photos)}")
print(f"Missing in Dest: {len(missing_in_dest)}")

if missing_in_dest:
    print("\nFirst 10 missing photos:")
    for p in missing_in_dest[:10]:
        print(p)
    
    with open("missing_feb_2021.txt", "w") as f:
        for p in missing_in_dest:
            f.write(p + "\n")
    print(f"\nFull list saved to missing_feb_2021.txt")
else:
    print("\nAll source photos found in destination!")
