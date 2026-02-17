import requests
import time
import json
import argparse

# --- CONFIG ---
# Get these from the Meta Developers Portal (Free)
ACCESS_TOKEN = "YOUR_INSTA_GRAPH_TOKEN"
INSTA_ACCOUNT_ID = "YOUR_INSTA_BUSINESS_ID"

def upload_via_ngrok(json_file, ngrok_base_url, video_filename, index=0):
    # 1. Load Metadata
    with open(json_file, "r", encoding="utf-8") as f:
        data_raw = json.load(f)
    data = data_raw[index] if isinstance(data_raw, list) else data_raw
    meta = data.get("metadata", {})
    
    # Construct the Public URL for the local file
    public_video_url = f"{ngrok_base_url}/{video_filename}"
    caption = f"{meta.get('title')}\n\n{meta.get('description')}"

    print(f"🔗 Pointing Instagram to: {public_video_url}")

    # 2. STEP 1: Create Media Container
    url = f"https://graph.facebook.com/v19.0/{INSTA_ACCOUNT_ID}/media"
    payload = {
        'media_type': 'REELS',
        'video_url': public_video_url,
        'caption': caption,
        'access_token': ACCESS_TOKEN
    }
    
    response = requests.post(url, data=payload).json()
    creation_id = response.get('id')
    
    if not creation_id:
        print(f"❌ Container Error: {response}")
        return

    # 3. STEP 2: Wait for Instagram to finish downloading from your PC
    status_url = f"https://graph.facebook.com/v19.0/{creation_id}"
    print("⏳ Instagram is downloading the video from your local machine...")
    
    while True:
        check = requests.get(status_url, params={'fields': 'status_code', 'access_token': ACCESS_TOKEN}).json()
        status = check.get('status_code')
        if status == 'FINISHED':
            print("✅ Download Complete!")
            break
        elif status == 'ERROR':
            print(f"❌ Instagram failed to download: {check}")
            return
        time.sleep(10)

    # 4. STEP 3: Publish
    publish_url = f"https://graph.facebook.com/v19.0/{INSTA_ACCOUNT_ID}/media_publish"
    final_res = requests.post(publish_url, data={'creation_id': creation_id, 'access_token': ACCESS_TOKEN}).json()
    print(f"🚀 Published to Instagram! Reel ID: {final_res.get('id')}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True)
    parser.add_argument("--ngrok", required=True, help="e.g. https://1234.ngrok-free.app")
    parser.add_argument("--file", required=True, help="e.g. INSTA_Reel_0.mp4")
    parser.add_argument("--index", type=int, default=0)
    args = parser.parse_args()
    
    upload_via_ngrok(args.json, args.ngrok, args.file, args.index)