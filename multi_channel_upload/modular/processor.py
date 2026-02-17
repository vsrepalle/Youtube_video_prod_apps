import os, json, shutil, gc, time, random
import tkinter as tk
from tkinter import filedialog
from gtts import gTTS
from moviepy.editor import *
from moviepy.config import change_settings
from PIL import Image
from icrawler.builtin import BingImageCrawler
import spacy

# Load spaCy NLP model
try:
    nlp = spacy.load("en_core_web_sm")
except:
    print("⚠️ Downloading spaCy model...")
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# --- CONFIG ---
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})
W, H = 720, 1280 
SPEED_FACTOR = 1.20
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# UI Dimensions
HEADER_END_Y = 260
SUBTITLE_START_Y = 880
GAP_HEIGHT = SUBTITLE_START_Y - HEADER_END_Y 

# --- UPLOAD LOGIC ---
try: 
    from stage3_upload import get_authenticated_service, upload_video_with_service
except ImportError: 
    print("⚠️ stage3_upload.py not found in modular folder.")

def get_priority_keywords(text):
    doc = nlp(text)
    people = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    venues = [ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC", "FAC", "ORG"]]
    if people: return people[:2], "Person"
    elif venues: return [venues[0]], "Venue"
    else: return [], "General"

def fetch_and_clean_images(item_data, index):
    raw_dir = os.path.join(BASE_DIR, f"raw_{index}")
    clean_dir = os.path.join(BASE_DIR, f"clean_{index}")
    for d in [raw_dir, clean_dir]:
        if os.path.exists(d): shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
    
    content_text = f"{item_data['headline']} {item_data['hook_text']}"
    entities, priority_type = get_priority_keywords(content_text)
    
    # User Preference format: Vijay | Bobby Deol
    query = item_data.get('metadata', {}).get('search_key', '').split('|')[0].strip()
    if not query:
        query = entities[0] if entities else item_data['headline']

    print(f"🎯 Search Key: {query}")
    crawler = BingImageCrawler(storage={'root_dir': raw_dir}, log_level=50)
    crawler.crawl(keyword=query, max_num=5)
    
    valid_paths = []
    files = [f for f in os.listdir(raw_dir) if os.path.isfile(os.path.join(raw_dir, f))]
    for i, f in enumerate(files):
        raw_path = os.path.join(raw_dir, f)
        try:
            with Image.open(raw_path) as img:
                clean_name = f"img_{index}_{i}.jpg"
                p = os.path.join(clean_dir, clean_name)
                img.convert('RGB').save(p, "JPEG")
                valid_paths.append(p)
        except: continue
    return valid_paths

def generate_video(json_path, youtube_service):
    with open(json_path, "r", encoding="utf-8") as f: 
        items = json.load(f)

    # Auth once at the start of the session
    youtube_service = get_authenticated_service()

    for i, item in enumerate(items):
        v_title = item.get('metadata', {}).get('title', "News Update")
        print(f"\n🎬 RENDERING: {v_title}")
        
        # 1. Audio
        full_text = f"{item['hook_text']} {item['details']}"
        tts_path = os.path.join(BASE_DIR, f"audio_{i}.mp3")
        gTTS(text=full_text, lang='en').save(tts_path)
        audio = AudioFileClip(tts_path)
        dur = audio.duration

        # 2. Base UI Layers
        bg = ColorClip(size=(W, H), color=(5, 5, 15)).set_duration(dur)
        
        # 3. Dynamic Visuals (Slideshow)
        img_paths = fetch_and_clean_images(item, i)
        if not img_paths:
            slideshow = ColorClip(size=(W, GAP_HEIGHT), color=(30, 30, 30)).set_duration(dur)
        else:
            slide_dur = dur / len(img_paths)
            slides = [ImageClip(p).set_duration(slide_dur).resize(width=W) for p in img_paths]
            slideshow = concatenate_videoclips(slides, method="compose")
        
        slideshow = slideshow.set_position(('center', HEADER_END_Y))

        # 4. Text Elements
        header = TextClip(item['headline'].upper(), fontsize=45, color='yellow', font='Arial-Bold', 
                          size=(W-80, None), method='caption').set_duration(dur).set_position(('center', 80))
        
        sub_text = TextClip(item['hook_text'].upper(), fontsize=35, color='white', method='caption', 
                            size=(W-100, None)).set_duration(dur).set_position(('center', SUBTITLE_START_Y))

        # CTA STRICTLY IN LAST SCENE ONLY
        cta = TextClip("TUNE WITH US FOR MORE NEWS", fontsize=40, color='white', bg_color='red',
                       size=(W, 100), method='caption').set_start(dur-3).set_duration(3).set_position(('center', 'bottom'))

        # 5. Compile (Layer order: Background first, then content)
        final = CompositeVideoClip([bg, slideshow, header, sub_text, cta]).set_audio(audio)
        final = final.fx(vfx.speedx, SPEED_FACTOR)
        
        out_name = os.path.join(BASE_DIR, f"TrendWave_Short_{i}.mp4")
        final.write_videofile(out_name, fps=24, codec="libx264")

        # --- UPLOAD PROMPT ---
        print(f"✅ Created: {out_name}")
        choice = input(f"🚀 Upload to YouTube? (y/s): ").lower()
        if choice == 'y':
            upload_video_with_service(youtube_service, out_name, v_title, item['details'], ["news", "trendwave"])

        # Cleanup
        final.close(); audio.close()
        gc.collect()

if __name__ == "__main__":
    # Your file picker logic
    root = tk.Tk(); root.withdraw()
    path = filedialog.askopenfilename()
    if path: generate_video(path)