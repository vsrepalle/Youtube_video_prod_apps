import os
import json
import logging
import pickle
import subprocess
from datetime import datetime
from moviepy.editor import ColorClip, TextClip, CompositeVideoClip, AudioFileClip, CompositeAudioClip
from moviepy.config import change_settings
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# --- 🛠️ STEP 1: FIX IMAGEMAGICK PATH ---
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})

# --- CONFIGURATION ---
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
W, H = 1080, 1920  # standard 9:16 Shorts resolution

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("automation.log", encoding='utf-8'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# --- 🎥 VIDEO GENERATION ---
def render_short_video(item, output_filename):
    """Creates a 9:16 Short with text and the mandatory 'Tune with us' end scene."""
    logger.info(f"🎬 Rendering video for: {item['headline']}")
    duration = 15  # Total video length
    
    # 1. Background
    bg = ColorClip(size=(W, H), color=(0, 0, 30), duration=duration)
    
    # 2. Headline Text (Using MoviePy v2.0 compatible arguments)
    txt = TextClip(
        item['headline'],
        fontsize=80,
        color='white',
        method='caption',
        size=(W-200, None),
        align='center'
    ).set_position('center').set_duration(duration)
    
    # 3. Last Scene Hook (Mandatory: ONLY appears in last scene)
    cta = TextClip(
        "Tune with us for more such news",
        fontsize=50,
        color='yellow',
        bg_color='black'
    ).set_position(('center', H-400)).set_start(duration-4).set_duration(4)

    final_video = CompositeVideoClip([bg, txt, cta])
    
    # Check for background music
    if os.path.exists("bg_music.mp3"):
        bgm = AudioFileClip("bg_music.mp3").volumex(0.1).set_duration(duration)
        final_video = final_video.set_audio(bgm)

    final_video.write_videofile(output_filename, fps=24, codec="libx264")
    logger.info(f"✅ Video rendered: {output_filename}")

# --- 🔑 YOUTUBE AUTH ---
def get_youtube_service(channel_name):
    client_secrets_file = 'client_secret.json'
    pickle_file = f"token_{channel_name.replace(' ', '_')}.pickle"
    creds = None
    if os.path.exists(pickle_file):
        with open(pickle_file, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(pickle_file, 'wb') as token:
            pickle.dump(creds, token)
    return build('youtube', 'v3', credentials=creds)

# --- 📤 YOUTUBE UPLOAD ---
def upload_to_youtube(service, file_path, meta):
    try:
        body = {
            'snippet': {
                'title': meta['title'],
                'description': meta.get('description', 'Tune with us for more such news.'),
                'tags': meta.get('tags', []),
                'categoryId': meta.get('category_id', '22')
            },
            'status': {
                'privacyStatus': 'private', # Defaulting to private
                'selfDeclaredMadeForKids': False
            }
        }
        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
        request = service.videos().insert(part="snippet,status", body=body, media_body=media)
        response = request.execute()
        logger.info(f"✅ Success! YouTube ID: {response.get('id')}")
    except Exception as e:
        logger.error(f"❌ Upload failed: {str(e)}")

# --- 🚀 AUTOMATION LOOP ---
def run_automation(json_file):
    if not os.path.exists(json_file):
        logger.error(f"JSON {json_file} missing.")
        return

    with open(json_file, 'r', encoding='utf-8') as f:
        items = json.load(f)

    for i, item in enumerate(items):
        channel = item['target_channel']
        meta = item['metadata']
        video_filename = f"Short_{channel.replace(' ', '_')}_{i}.mp4"

        # 1. Generate Video
        try:
            render_short_video(item, video_filename)
        except Exception as e:
            logger.error(f"💥 Rendering failed: {e}")
            continue

        # 2. Upload Video
        if os.path.exists(video_filename):
            print(f"\n🎬 Done! Ready to upload to: {channel}")
            ans = input(f"Confirm upload for '{meta['title']}'? (y/n): ").lower()
            if ans == 'y':
                service = get_youtube_service(channel)
                upload_to_youtube(service, video_filename, meta)

if __name__ == "__main__":
    run_automation("news_data.json")