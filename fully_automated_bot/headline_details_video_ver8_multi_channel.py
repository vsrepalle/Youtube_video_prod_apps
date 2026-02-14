import os, json, shutil, pickle, logging
from datetime import datetime
from gtts import gTTS
from moviepy.editor import *
from moviepy.config import change_settings
from PIL import Image
from icrawler.builtin import BingImageCrawler
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- 1. SETUP LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("automation.log"), # Saves to file
        logging.StreamHandler()                # Prints to console
    ]
)
logger = logging.getLogger(__name__)

# --- CONFIG ---
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})
W, H = 720, 1280 
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

from visual_effects import get_styled_header, get_styled_ticker, get_progress_bar

# --- YOUTUBE CHANNEL AUTOMATION ---
def get_youtube_service(channel_name):
    logger.info(f"🔑 Authenticating for channel: {channel_name}")
    safe_name = channel_name.replace(" ", "_").lower()
    token_file = f"token_{safe_name}.pickle"
    creds = None
    
    if os.path.exists(token_file):
        logger.info(f"🔄 Loading existing token from {token_file}")
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
            
    if not creds or not creds.valid:
        logger.warning(f"⚠️ No valid token found for {channel_name}. Opening browser for login...")
        flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
            
    return build("youtube", "v3", credentials=creds)

def upload_to_youtube(service, file_path, meta):
    try:
        logger.info(f"📤 Starting upload: {meta['title']}")
        body = {
            'snippet': {
                'title': meta['title'],
                'description': meta.get('description', ''),
                'tags': meta.get('tags', []),
                'categoryId': meta.get('category_id', '22')
            },
            'status': {'privacyStatus': 'private', 'selfDeclaredMadeForKids': False}
        }
        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
        request = service.videos().insert(part="snippet,status", body=body, media_body=media)
        response = request.execute()
        logger.info(f"✅ Upload successful! Video ID: {response.get('id')}")
    except Exception as e:
        logger.error(f"❌ Failed to upload: {str(e)}", exc_info=True)

# --- PROCESSING ENGINE ---
def generate_channel_shorts(json_file):
    logger.info(f"📂 Reading JSON data from {json_file}")
    if not os.path.exists(json_file):
        logger.critical(f"🛑 CRITICAL: {json_file} not found!")
        return

    try:
        with open(json_file, "r", encoding="utf-8") as f:
            items = json.load(f)
    except Exception as e:
        logger.critical(f"🛑 Failed to parse JSON: {e}")
        return

    for i, item in enumerate(items):
        chan = item['target_channel']
        logger.info(f"🎬 --- Processing Video {i+1} for {chan} ---")
        
        try:
            # Audio Generation
            voice_p = f"audio_{i}.mp3"
            logger.info(f"🎙️ Generating TTS for: {item['headline']}")
            gTTS(text=f"{item['hook_text']}. {item['headline']}. {item['details']}", lang='en').save(voice_p)
            audio = AudioFileClip(voice_p)
            dur = audio.duration

            # Image Fetching
            img_dir = f"imgs_{i}"
            logger.info(f"🖼️ Fetching images for query: {item['search_key']}")
            if os.path.exists(img_dir): shutil.rmtree(img_dir)
            crawler = BingImageCrawler(storage={'root_dir': img_dir}, log_level=50)
            crawler.crawl(keyword=f"{item['search_key']} 2026", max_num=3)
            
            img_files = [os.path.join(img_dir, f) for f in os.listdir(img_dir)]
            if not img_files:
                logger.error(f"❌ No images found for {item['search_key']}")
                continue

            # Visual Rendering
            logger.info("🎥 Rendering Video Layers...")
            header = get_styled_header(item['hook_text'], dur, W).set_position(('center', 60))
            footer = get_styled_ticker(item['details'], dur, W, 300).set_position(('center', 920))
            prog_bar = get_progress_bar(dur, W, H)
            
            slides = [ImageClip(p).set_duration(dur/len(img_files)).resize(height=580) for p in img_files]
            slideshow = concatenate_videoclips(slides, method="compose").set_position(('center', 280))

            bg = ColorClip(size=(W, H), color=(0, 0, 15)).set_duration(dur)
            final_video = CompositeVideoClip([bg, header, slideshow, footer, prog_bar]).set_audio(audio)

            out_name = f"Short_{chan.replace(' ', '_')}_{i}.mp4"
            final_video.write_videofile(out_name, fps=24, codec="libx264")
            logger.info(f"💾 Rendered file saved: {out_name}")

            # Automation Switch
            ans = input(f"🤔 Ready to upload to {chan}? (y/n): ").lower()
            if ans == 'y':
                youtube = get_youtube_service(chan)
                upload_to_youtube(youtube, out_name, item['metadata'])
            else:
                logger.info("⏩ Skipping upload as per user request.")

        except Exception as e:
            logger.error(f"💥 Error processing video {i}: {str(e)}", exc_info=True)

if __name__ == "__main__":
    logger.info("🚀 Script Execution Started")
    generate_channel_shorts("news_data.json")
    logger.info("🏁 Script Execution Finished")