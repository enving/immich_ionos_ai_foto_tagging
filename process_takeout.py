import os
import zipfile
import shutil
import hashlib
from pathlib import Path

# Paths
ZIP_DIR = Path("/Users/macenving/immich-server/library/new_google_takeout")
IMPORT_DIR = Path("/Users/macenving/immich-server/library/imported")
TEMP_EXTRACT_DIR = ZIP_DIR / "temp_extracted"
KEEP_DIR = ZIP_DIR / "final_missing_files"

def get_file_identifiers(directory):
    """Scans directory and returns a dict of {filename_size: path} for quick comparison."""
    identifiers = {}
    print(f"Scanning existing library for duplicates in {directory}...")
    for root, _, files in os.walk(directory):
        for file in files:
            try:
                path = Path(root) / file
                # Use simple heuristic: filename + size. 
                key = f"{file}_{path.stat().st_size}"
                identifiers[key] = path
            except OSError:
                continue
    print(f"Index built with {len(identifiers)} items.")
    return identifiers

def process_zips():
    # 1. Build index of existing files (Dest)
    existing_files_map = get_file_identifiers(IMPORT_DIR)
    
    # Create output dir for missing files
    KEEP_DIR.mkdir(parents=True, exist_ok=True)
    
    # 2. Iterate over ZIPs
    zips = sorted(list(ZIP_DIR.glob("*.zip")))
    if not zips:
        print("No zip files found!")
        return

    for zip_path in zips:
        print(f"\n📦 Processing {zip_path.name}...")
        
        # Ensure temp clean
        if TEMP_EXTRACT_DIR.exists():
            shutil.rmtree(TEMP_EXTRACT_DIR)
        TEMP_EXTRACT_DIR.mkdir()

        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Unzip all content to temp dir
                print(f"   Extracting all files...")
                zf.extractall(TEMP_EXTRACT_DIR)
                
            print(f"   Analyzing contents...")
            deleted_count = 0
            kept_count = 0
            
            # Walk through extracted files
            for root, _, files in os.walk(TEMP_EXTRACT_DIR):
                for file in files:
                    file_path = Path(root) / file
                    
                    # Skip system files (but keep metadata.json)
                    if file.startswith("."):
                        file_path.unlink()
                        continue

                    key = f"{file}_{file_path.stat().st_size}"
                    
                    is_duplicate = False
                    if key in existing_files_map:
                        is_duplicate = True
                        
                    if is_duplicate:
                        # DUPLICATE -> DELETE
                        file_path.unlink()
                        deleted_count += 1
                    else:
                        # NEW -> MOVE TO KEEP DIR
                        # Preserve relative structure? 
                        # To cleanly separate, we rely on relative path from temp dir.
                        try:
                            rel_path = file_path.relative_to(TEMP_EXTRACT_DIR)
                        except ValueError:
                            rel_path = Path(file)
                            
                        dest_path = KEEP_DIR / rel_path
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(file_path), str(dest_path))
                        kept_count += 1
            
            print(f"   ✅ Done with {zip_path.name}: Deleted {deleted_count} duplicates, Kept {kept_count} new files.")
            
        except zipfile.BadZipFile:
            print(f"   ❌ Error: Bad Zip File {zip_path.name}")
        except Exception as e:
             print(f"   ❌ Error processing {zip_path.name}: {e}")
        finally:
            # Cleanup temp extract dir for this zip to free space
            if TEMP_EXTRACT_DIR.exists():
                shutil.rmtree(TEMP_EXTRACT_DIR)

    print("\n🎉 Processing Complete!")
    print(f"New unique files are located in: {KEEP_DIR}")
    print("You can verify them and then move them to library/imported.")

if __name__ == "__main__":
    process_zips()
