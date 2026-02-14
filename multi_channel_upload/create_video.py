import os, json, shutil, time
from datetime import datetime
from gtts import gTTS
from moviepy.editor import *
from moviepy.config import change_settings
from PIL import Image
from icrawler.builtin import BingImageCrawler

# 1. NEW: Import the upload module
try:
    from stage3_upload import upload_from_json
except ImportError:
    print("⚠️ stage3_upload.py not found. Uploading will be disabled.")

from visual_effects import get_styled_header, get_styled_ticker, get_progress_bar

# --- CONFIG ---
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})

W, H = 720, 1280 
BGM_PATH = "bg_music.mp3"

def fetch_and_clean_images(query, index):
    raw_dir, clean_dir = f"raw_{index}", f"clean_{index}"
    for d in [raw_dir, clean_dir]:
        if os.path.exists(d): shutil.rmtree(d)
        os.makedirs(d)
    main_term = query.split('|')[0].strip()
    crawler = BingImageCrawler(storage={'root_dir': raw_dir}, log_level=50)
    crawler.crawl(keyword=f"{main_term} 2026 trending", max_num=5)
    valid_paths = []
    for f in sorted(os.listdir(raw_dir)):
        try:
            with Image.open(os.path.join(raw_dir, f)) as img:
                p = os.path.join(clean_dir, f"{f}.jpg")
                img.convert('RGB').save(p, "JPEG")
                valid_paths.append(p)
        except: continue
    return valid_paths

def generate_video(json_file):
    with open(json_file, "r", encoding="utf-8") as f: items = json.load(f)

    all_scenes = []
    for i, item in enumerate(items):
        print(f"Rendering Scene {i+1}...")
        voice_p = f"v_{i}.mp3"
        gTTS(text=f"{item['hook_text']}. {item['headline']}. {item['details']}", lang='en').save(voice_p)
        audio = AudioFileClip(voice_p)
        dur = audio.duration

        header = get_styled_header(item['hook_text'], dur, W).set_position(('center', 60))
        footer = get_styled_ticker(item['details'], dur, W, 300).set_position(('center', 920))
        prog_bar = get_progress_bar(dur, W, H)

        img_paths = fetch_and_clean_images(item.get('search_key', ''), i)
        if img_paths:
            slides = [ImageClip(p).set_duration(dur/len(img_paths)).resize(height=580) for p in img_paths]
            slideshow = concatenate_videoclips(slides, method="compose").set_position(('center', 280))
        else:
            slideshow = ColorClip(size=(W-100, 580), color=(40, 40, 60)).set_duration(dur).set_position(('center', 280))

        bg = ColorClip(size=(W, H), color=(0, 0, 15)).set_duration(dur)
        scene = CompositeVideoClip([bg, header, slideshow, footer, prog_bar]).set_audio(audio)
        all_scenes.append(scene)

    final_v = concatenate_videoclips(all_scenes, method="compose")
    cta = TextClip("Tune with us for more such news", fontsize=38, color='white', bg_color='darkred', size=(W, 100), method='caption'
                   ).set_start(final_v.duration-3.5).set_duration(3.5).set_position(('center', H-250))
    final_output = CompositeVideoClip([final_v, cta])
    
    if os.path.exists(BGM_PATH):
        bgm = AudioFileClip(BGM_PATH).volumex(0.1).set_duration(final_output.duration)
        final_output = final_output.set_audio(CompositeAudioClip([final_output.audio, bgm]))

    out_name = os.path.abspath(f"Viral_Short_{datetime.now().strftime('%M%S')}.mp4")
    final_output.write_videofile(out_name, fps=24, codec="libx264")

    # 2. NEW: ASK USER TO CONTINUE WITH UPLOAD
    print("\n" + "="*30)
    print(f"✅ Video Generated: {out_name}")
    user_choice = input("🚀 Do you want to upload this to YouTube now? (y/n): ").lower()
    
    if user_choice == 'y':
        print("📤 Starting Upload Pipeline...")
        try:
            # Pass the JSON data and the absolute path of the new video
            upload_from_json(json_file, video_file=out_name)
        except Exception as e:
            print(f"❌ Upload failed: {e}")
    else:
        print("⏭️ Upload skipped. Video saved locally.")

if __name__ == "__main__":
    generate_video("news_data.json")