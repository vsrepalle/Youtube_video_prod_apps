import os, json, shutil, gc, time, random
import tkinter as tk
from tkinter import filedialog
from gtts import gTTS
from moviepy.editor import *
from moviepy.config import change_settings
from PIL import Image
from icrawler.builtin import BingImageCrawler
import spacy

# Load spaCy NLP model for Entity Priority
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

# UI Dimensions
HEADER_END_Y = 260
SUBTITLE_START_Y = 880
GAP_HEIGHT = SUBTITLE_START_Y - HEADER_END_Y 

# --- IMPORT UPLOAD LOGIC ---
try: 
    from stage3_upload import get_authenticated_service, upload_from_json
except ImportError: 
    print("⚠️ stage3_upload.py not found.")

def get_priority_keywords(text):
    """Extracts People (High Priority) and Locations (Medium Priority)."""
    doc = nlp(text)
    people = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    venues = [ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC", "FAC", "ORG"]]
    if people: return people[:2], "Person"
    elif venues: return [venues[0]], "Venue"
    else: return [], "General"

def fetch_and_clean_images(item_data, index):
    raw_dir, clean_dir = f"raw_{index}", f"clean_{index}"
    for d in [raw_dir, clean_dir]:
        if os.path.exists(d): shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
    
    content_text = f"{item_data['headline']} {item_data['hook_text']}"
    entities, priority_type = get_priority_keywords(content_text)
    
    if priority_type == "Person":
        query = f"{entities[0]} cinematic professional"
    elif priority_type == "Venue":
        query = f"{entities[0]} scenery cinematic"
    else:
        query = item_data.get('search_key', '').split('|')[0].strip()

    print(f"🎯 Image Priority: {priority_type} | Query: {query}")
    crawler = BingImageCrawler(storage={'root_dir': raw_dir}, log_level=50)
    crawler.crawl(keyword=query, max_num=5, offset=random.randint(0, 8))
    
    valid_paths = []
    files = [f for f in os.listdir(raw_dir) if os.path.isfile(os.path.join(raw_dir, f))]
    for i, f in enumerate(files):
        raw_path = os.path.join(raw_dir, f)
        try:
            with Image.open(raw_path) as img:
                clean_name = f"img_{index}_{i}_{int(time.time())}.jpg"
                p = os.path.join(clean_dir, clean_name)
                img.convert('RGB').save(p, "JPEG")
                valid_paths.append(p)
        except: continue
    return valid_paths

def apply_ken_burns(clip):
    return clip.fx(vfx.resize, lambda t: 1 + 0.05 * t) 

def generate_video(json_path):
    with open(json_path, "r", encoding="utf-8") as f: 
        items = json.load(f)

    for i, item in enumerate(items):
        v_title = item.get('metadata', {}).get('title', "News Update")
        print(f"\n" + "="*50)
        print(f"🎬 RENDERING {i+1}/{len(items)}: {v_title}")
        print("="*50)
        
        # 1. Audio
        full_text = f"{item['hook_text']} {item['details']}"
        tts_path = f"audio_{i}.mp3"
        gTTS(text=full_text, lang='en').save(tts_path)
        audio = AudioFileClip(tts_path)
        dur = audio.duration

        # 2. Base UI
        bg = ColorClip(size=(W, H), color=(5, 5, 15)).set_duration(dur)
        banner = TextClip(" PLEASE SUBSCRIBE ", fontsize=32, color='white', 
                          bg_color='red', font='Arial-Bold').set_duration(dur).set_position(('center', 20))
        header = TextClip(item['headline'].upper(), fontsize=44, color='yellow', font='Arial-Bold', 
                          size=(W-80, 180), method='caption').set_duration(dur).set_position(('center', 100))

        # 3. Dynamic Visuals
        img_paths = fetch_and_clean_images(item, i)
        if not img_paths:
            slideshow = ColorClip(size=(W, GAP_HEIGHT), color=(30, 30, 30)).set_duration(dur).set_position(('center', HEADER_END_Y))
        else:
            slide_dur = dur / len(img_paths)
            slides = [apply_ken_burns(ImageClip(p).set_duration(slide_dur).resize(width=W).resize(height=GAP_HEIGHT)) for p in img_paths]
            slideshow = concatenate_videoclips(slides, method="compose").set_position(('center', HEADER_END_Y))

        # 4. Text & CTA
        sent_dur = dur / 2
        s1 = TextClip(item['hook_text'].upper(), fontsize=36, color='white', method='caption', 
                      size=(W-100, None)).set_duration(sent_dur).set_position(('center', SUBTITLE_START_Y))
        s2 = TextClip(item['details'].upper(), fontsize=36, color='yellow', method='caption', 
                      size=(W-100, None)).set_start(sent_dur).set_duration(sent_dur).set_position(('center', SUBTITLE_START_Y))
        
        # Last Scene CTA ONLY
        cta = TextClip("Tune with us for more such news", fontsize=38, color='white', bg_color='darkred', 
                       size=(W, 100), method='caption').set_start(dur-3.5).set_duration(3.5).set_position(('center', H-150))

        # 5. Compile & Speed
        final = CompositeVideoClip([bg, header, banner, slideshow, s1, s2, cta]).set_audio(audio)
        final = final.fx(vfx.speedx, SPEED_FACTOR)
        
        out_name = f"Render_Short_{i+1}.mp4"
        final.write_videofile(out_name, fps=24, codec="libx264", threads=8, preset="ultrafast")
        
        # 6. Cleanup Memory
        final.close(); audio.close(); slideshow.close()
        gc.collect()
        
        # --- NEW: INTERACTIVE UPLOAD PROMPT ---
        print(f"\n✅ Video Created: {out_name}")
        user_choice = input(f"🚀 Upload '{v_title}' to YouTube now? (y = Yes / s = Skip to next): ").lower()
        
        if user_choice == 'y':
            try:
                print(f"📡 Uploading to YouTube...")
                upload_from_json(json_path, video_file=out_name, index=i)
                print("🏁 Upload Finished!")
            except Exception as e:
                print(f"⚠️ Upload Error: {e}")
        else:
            print(f"⏭️ Skipping upload for scene {i+1}. Moving to next video.")

        time.sleep(1)

if __name__ == "__main__":
    root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
    selected_json = filedialog.askopenfilename(title="Select Metadata JSON", filetypes=[("JSON Files", "*.json")])
    root.destroy()
    if selected_json:
        generate_video(selected_json)
    else:
        print("🛑 No JSON file selected.")