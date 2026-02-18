import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "client_secret.json")
# Scopes for uploading and reading channel info for the handshake
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly"]

def get_authenticated_service(channel_folder_name):
    """Fetches or creates a token.pickle within the specific channel folder."""
    channel_path = os.path.join(BASE_DIR, "channels", channel_folder_name)
    os.makedirs(channel_path, exist_ok=True)
    token_path = os.path.join(channel_path, "token.pickle")
    creds = None

    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    return build("youtube", "v3", credentials=creds)
def verify_channel_ownership(youtube, expected_name):
    try:
        request = youtube.channels().list(part="snippet", mine=True)
        response = request.execute()
        
        actual_title = response['items'][0]['snippet']['title']
        
        # Super-clean comparison (removes spaces and symbols)
        actual_clean = "".join(filter(str.isalnum, actual_title.lower()))
        expected_clean = "".join(filter(str.isalnum, expected_name.lower()))

        if expected_clean in actual_clean or actual_clean in expected_clean:
            print(f"🛡️  MATCH: YouTube Account '{actual_title}' verified for {expected_name}.")
            return True
        else:
            print(f"🛑  MISMATCH: Expected '{expected_name}', but you logged into '{actual_title}'.")
            print(f"👉  ACTION: Delete token.pickle in channels/{expected_name} and login to the correct Brand Account.")
            return False
    except Exception as e:
        print(f"⚠️  Verification Error: {e}")
        return False

def upload_video_with_service(youtube, video_file, item, channel_folder):
    """Handles the actual video upload with metadata."""
    if not verify_channel_ownership(youtube, channel_folder):
        print(f"🛑 IDENTITY SHIELD: Target '{channel_folder}' does not match logged-in account. Skipping.")
        return None

    # Retrieve metadata from JSON
    title = item['metadata'].get('title', item['headline'])[:100]
    desc = item.get('description', "Tune with us for more news!")
    tags = item['metadata'].get('tags', [])

    body = {
        'snippet': {'title': title, 'description': desc, 'tags': tags, 'categoryId': '24'},
        'status': {'privacyStatus': 'private', 'selfDeclaredMadeForKids': False}
    }

    media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
    
    print(f"🔼 Uploading to {channel_folder}...")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"   - Progress: {int(status.progress() * 100)}%")
    print(f"✅ Upload successful! ID: {response['id']}")
    return response['id']