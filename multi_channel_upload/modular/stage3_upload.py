import os
import pickle
import google.oauth2.credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- DYNAMIC PATH FIX ---
# Gets the absolute directory of THIS script (stage3_upload.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Point to the secret file and token file in the SAME directory as this script
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "client_secret.json")
TOKEN_PICKLE = os.path.join(BASE_DIR, "token.pickle")

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_authenticated_service():
    """Authenticates once and saves/loads a token to avoid repeat logins."""
    creds = None
    
    # 1. Load existing token if it exists
    if os.path.exists(TOKEN_PICKLE):
        print(f"🔄 Loading existing credentials from: {TOKEN_PICKLE}")
        with open(TOKEN_PICKLE, 'rb') as token:
            creds = pickle.load(token)
            
    # 2. If no valid credentials, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("⏳ Credentials expired. Refreshing...")
            creds.refresh(Request())
        else:
            print("🔑 No valid token found. Starting browser authentication...")
            if not os.path.exists(CLIENT_SECRETS_FILE):
                raise FileNotFoundError(f"❌ Missing {CLIENT_SECRETS_FILE}. Please place your Google JSON here.")
            
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # 3. Save the credentials for next time
        with open(TOKEN_PICKLE, 'wb') as token:
            pickle.dump(creds, token)
            print(f"💾 Credentials saved to: {TOKEN_PICKLE}")

    return build("youtube", "v3", credentials=creds)

def upload_video_with_service(youtube, video_file, title, description, tags, category="22", privacy="private"):
    """Performs the actual upload using the persistent service."""
    if not os.path.exists(video_file):
        print(f"❌ Error: Video file not found: {video_file}")
        return None

    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': category
        },
        'status': {
            'privacyStatus': privacy,
            'selfDeclaredMadeForKids': False
        }
    }

    insert_request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=MediaFileUpload(video_file, chunksize=-1, resumable=True)
    )

    print(f"🚀 Uploading to YouTube: {title}...")
    response = insert_request.execute()
    print(f"✅ Upload Complete! Video ID: https://youtu.be/{response.get('id')}")
    return response

if __name__ == "__main__":
    # Test block
    print("Running Authentication Test...")
    try:
        service = get_authenticated_service()
        print("🎉 Authentication successful!")
    except Exception as e:
        print(f"💥 Auth failed: {e}")