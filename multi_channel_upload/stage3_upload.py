import os, json, argparse
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_authenticated_service():
    # Looks for your secret file in the same directory
    flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
    credentials = flow.run_local_server(port=0)
    return build("youtube", "v3", credentials=credentials)

def upload_from_json(json_file, video_file=None):
    if not os.path.exists(json_file):
        print(f"❌ JSON file not found: {json_file}")
        return

    with open(json_file, "r", encoding="utf-8") as f:
        data_raw = json.load(f)

    # Always grab the metadata from the first item in the list
    data = data_raw[0] if isinstance(data_raw, list) else data_raw
    meta = data.get("metadata", {})

    # File Path Logic
    video_filename = video_file or data.get("video_name") or "TrendWave_Latest.mp4"
    video_path = os.path.abspath(video_filename)

    if not os.path.exists(video_path):
        print(f"❌ Video file NOT FOUND at: {video_path}")
        return

    youtube = get_authenticated_service()

    # --- 2026 METADATA HANDLING ---
    # Title: Uses your Search Key preference (e.g., "OpenAI Ghost | Sam Altman")
    video_title = meta.get("title") or data.get("search_key", "TrendWave Update").split('|')[0].strip()
    
    # Category logic based on your channel requests
    # 27 = Education, 28 = Science & Tech (Shopping/Gadgets)
    cat_id = meta.get("category_id", "28") 

    request_body = {
        "snippet": {
            "title": video_title,
            "description": meta.get("description", f"{data.get('details', '')}\n\nTune with us for more such news."),
            "tags": meta.get("tags", ["news", "AI", "2026", "trends"]),
            "categoryId": cat_id
        },
        "status": {
            "privacyStatus": meta.get("privacy_status", "private"),
            "selfDeclaredMadeForKids": False,
            # MANDATORY 2026 Compliance: Altered/Synthetic Media Flag
            "containsSyntheticMedia": meta.get("self_declared_synthetic", True)
        }
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    print(f"🚀 Initializing Upload: {video_filename}")
    print(f"🏷️ Category: {'Education' if cat_id == '27' else 'Tech/Gadgets'}")
    print(f"🤖 AI Disclosure: {'ON' if request_body['status']['containsSyntheticMedia'] else 'OFF'}")
    
    request = youtube.videos().insert(part="snippet,status", body=request_body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status: 
            print(f"📈 Uploading... {int(status.progress() * 100)}%")

    print(f"✅ Upload Complete! Video ID: {response['id']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default="news_data.json")
    parser.add_argument("--file", default=None)
    args = parser.parse_args()
    upload_from_json(args.json, video_file=args.file)