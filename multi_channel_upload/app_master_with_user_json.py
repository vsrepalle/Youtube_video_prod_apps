import os, json, gc, shutil
from moviepy.editor import *
from moviepy.config import change_settings
from gtts import gTTS
from icrawler.builtin import BingImageCrawler

# --- 1. CONFIGURATION ---
# Update this path to your Magick.exe location
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})

W, H = 720, 1280 
BGM_PATH = "background_music.mp3"  # Place a lo-fi/study track in the folder

# --- 2. IMAGE FETCHING LOGIC ---
def fetch_images(search_key, folder_idx, max_imgs=3):
    """Downloads images using Bing Crawler and returns local paths."""
    save_dir = f"temp_images_{folder_idx}"
    if os.path.exists(save_dir):
        shutil.rmtree(save_dir)
    os.makedirs(save_dir)

    crawler = BingImageCrawler(storage={'root_dir': save_dir})
    crawler.crawl(keyword=search_key, max_num=max_imgs)
    
    # Get paths of downloaded images
    paths = [os.path.join(save_dir, f) for f in os.listdir(save_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
    return paths[:max_imgs]

# --- 3. VISUAL EFFECTS ---
def zoom_in_effect(clip, zoom_speed=0.04):
    """Ken Burns effect: slow zoom into the center."""
    return clip.resize(lambda t: 1 + zoom_speed * t).set_position('center')

# --- 4. MAIN GENERATOR ---
def generate_batch(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        items = json.load(f)

    for i, item in enumerate(items):
        print(f"🎬 Processing: {item['headline']}")
        
        # A. Audio & Ducking
        vo_path = f"vo_{i}.mp3"
        full_text = f"{item['hook_text']}. {item['headline']}."
        gTTS(text=full_text, lang='en').save(vo_path)
        vo_audio = AudioFileClip(vo_path).volumex(1.3)
        dur = vo_audio.duration

        if os.path.exists(BGM_PATH):
            bgm = AudioFileClip(BGM_PATH).volumex(0.12).loop(duration=dur).audio_fadeout(2)
            final_audio = CompositeAudioClip([vo_audio, bgm])
        else:
            final_audio = vo_audio

        # B. Image Fetching & Slideshow
        img_paths = fetch_images(item.get('search_key', 'latest news'), i)
        if not img_paths: # Fallback if no images found
            slideshow = ColorClip(size=(W, H), color=(20, 20, 20)).set_duration(dur)
        else:
            slide_dur = dur / len(img_paths)
            clips = [zoom_in_effect(ImageClip(p).set_duration(slide_dur).resize(width=W)) for p in img_paths]
            slideshow = concatenate_videoclips(clips, method="compose")

        # C. Overlays: Header (Top)
        header_bg = ColorClip(size=(W, 160), color=(10, 20, 45)).set_opacity(0.8).set_duration(dur)
        header_txt = TextClip(item['headline'].upper(), fontsize=40, color='yellow', 
                              font='Arial-Bold', method='caption', size=(W-60, None)).set_duration(dur)
        header = CompositeVideoClip([header_bg, header_txt.set_position('center')]).set_position(('center', 0))

        # D. Overlays: Subtitles (Bottom Red Banner)
        sub_bg = ColorClip(size=(W, 200), color=(160, 0, 0)).set_opacity(0.9).set_duration(dur)
        sub_txt = TextClip(item['hook_text'], fontsize=32, color='white', 
                           font='Arial-Bold', method='caption', size=(W-80, None)).set_duration(dur)
        subtitles = CompositeVideoClip([sub_bg, sub_txt.set_position('center')]).set_position(('center', H-200))

        # E. Final Assembly
        video = CompositeVideoClip([
            ColorClip(size=(W,H), color=(0,0,0)).set_duration(dur),
            slideshow.set_position('center'),
            subtitles,
            header
        ]).set_audio(final_audio)

        # F. Export
        out_name = f"Output_Video_{i+1}.mp4"
        video.write_videofile(out_name, fps=24, codec="libx264", audio_codec="aac")

        # G. Cleanup
        video.close(); vo_audio.close(); final_audio.close()
        if os.path.exists(vo_path): os.remove(vo_path)
        gc.collect()
        print(f"✅ Saved as {out_name}")

if __name__ == "__main__":
    generate_batch("news_data.json")