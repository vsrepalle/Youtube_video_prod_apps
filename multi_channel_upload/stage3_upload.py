import os, json, argparse
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- CONFIGURATION ---
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_authenticated_service():
    flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
    credentials = flow.run_local_server(port=0)
    return build("youtube", "v3", credentials=credentials)

def upload_from_json(json_file, video_file=None, index=0):
    if not os.path.exists(json_file):
        print(f"❌ JSON file not found: {json_file}")
        return

    with open(json_file, "r", encoding="utf-8") as f:
        data_raw = json.load(f)

    # --- 1. SYNC INDEX TO DATA ---
    # This ensures we pull title/desc/tags for ONLY the scene we are uploading
    if isinstance(data_raw, list):
        if index >= len(data_raw):
            print(f"⚠️ Index {index} out of range, using first item.")
            data = data_raw[0]
        else:
            data = data_raw[index]
    else:
        data = data_raw

    # Extract the metadata block for this specific index
    meta = data.get("metadata", {})

    # --- 2. DYNAMIC TITLE RESOLUTION ---
    # Ensures Title 1, Title 2, and Title 3 are unique
    base_title = meta.get("title") or data.get("search_key", "TrendWave Update").split('|')[0].strip()
    video_title = f"{base_title} - Part {index + 1}"

    # --- 3. DYNAMIC DESCRIPTION RESOLUTION ---
    # Combines specific scene details with your required 'Tune with us' call to action
    raw_desc = meta.get("description") or data.get("details", "Latest news update.")
    final_description = f"{raw_desc}\n\nTune with us for more such news."

    # --- 4. HASHTAG RESOLUTION ---
    # Pulls unique tags for this scene or uses defaults
    video_tags = meta.get("hashtags", ["news", "AI", "2026", "trends"])

    # --- FILE PATH CHECK ---
    video_filename = video_file or data.get("video_name") or f"scene_{index}.mp4"
    video_path = os.path.abspath(video_filename)

    if not os.path.exists(video_path):
        print(f"❌ Video file NOT FOUND: {video_path}")
        return

    youtube = get_authenticated_service()

    # --- API REQUEST BODY ---
    request_body = {
        "snippet": {
            "title": video_title,
            "description": final_description,
            "tags": video_tags,
            "categoryId": meta.get("category_id", "28") 
        },
        "status": {
            "privacyStatus": meta.get("privacy_status", "private"),
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": meta.get("self_declared_synthetic", True)
        }
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    print(f"🚀 Uploading Scene {index+1}: {video_filename}")
    print(f"📝 Title: {video_title}")
    print(f"🏷️ Tags: {', '.join(video_tags)}")
    
    request = youtube.videos().insert(part="snippet,status", body=request_body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status: 
            print(f"📈 Progress: {int(status.progress() * 100)}%")

    print(f"✅ Success! Video ID: {response['id']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default="news_data.json")
    parser.add_argument("--file", default=None)
    parser.add_argument("--index", type=int, default=0) 
    args = parser.parse_args()
    
    # Final Reminder: Cricket news (Ishan Kishan/Bumrah) is trending! 
    # Ensure your next JSON includes these high-performing stats.
    
    upload_from_json(args.json, video_file=args.file, index=args.index)