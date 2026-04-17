import os
import requests
import time
from dotenv import load_dotenv

# Load .env from parent directory (since script is in ionos_multimodal_indexing/)
dotenv_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(dotenv_path)

IMMICH_URL = "http://localhost:2283"
EMAIL = os.getenv("IMMICH_USER_EMAIL")
PASSWORD = os.getenv("IMMICH_USER_PASSWORD")

def login():
    print(f"Logging in to {IMMICH_URL} as {EMAIL}...")
    try:
        response = requests.post(f"{IMMICH_URL}/api/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("accessToken")
    except Exception as e:
        print(f"❌ Login Error: {e}")
        try:
            print(f"Response: {response.text}")
        except:
            pass
        return None

def trigger_scans(token):
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    
    # Get all libraries
    try:
        libs = requests.get(f"{IMMICH_URL}/api/libraries", headers=headers, timeout=10).json()
    except Exception as e:
        print(f"❌ Failed to get libraries: {e}")
        return

    print(f"Found {len(libs)} libraries.")
    for lib in libs:
        lib_id = lib.get("id")
        name = lib.get("name")
        print(f"Triggering scan for library '{name}' ({lib_id})...")
        try:
            res = requests.post(f"{IMMICH_URL}/api/libraries/{lib_id}/scan", headers=headers, timeout=10)
            if res.status_code in [200, 201, 204]:
                print(f"✅ Scan triggered for '{name}'")
            else:
                print(f"⚠️ Scan trigger response: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"❌ Error triggering scan for '{name}': {e}")

if __name__ == "__main__":
    print("🚀 Auto-triggering Immich Library Scans...")
    if not EMAIL or not PASSWORD:
        print("❌ Missing credentials in .env")
        exit(1)
        
    token = login()
    if token:
        trigger_scans(token)
        print("Waiting 10 seconds for scans to initialize...")
        time.sleep(10)
    else:
        print("❌ Could not get access token. Skipping scan trigger.")
        exit(1)
