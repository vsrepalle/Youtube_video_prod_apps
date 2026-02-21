import os
import json
import shutil
import gc
import re
import numpy as np
from gtts import gTTS
from icrawler.builtin import BingImageCrawler
from moviepy.editor import (
    TextClip, ImageClip, AudioFileClip, 
    CompositeVideoClip, ColorClip, concatenate_videoclips,
    VideoClip, CompositeAudioClip  # FIXED IMPORT
)
from moviepy.config import change_settings

# --- 1. LOAD EXTERNAL VIDEO CONFIG ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "video_config.json")

# Load with defaults in case file is missing or keys are wrong
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        v_cfg = json.load(f)
else:
    v_cfg = {}

# System Config
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})

# Safe dynamic assignment
W = v_cfg.get('dimensions', {}).get('width', 1080)
H = v_cfg.get('dimensions', {}).get('height', 1920)
FPS = v_cfg.get('dimensions', {}).get('fps', 24)
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
MUSIC_DIR = os.path.join(ASSETS_DIR, "music")

def split_into_phrases(text, max_chars=35):
    sentences = re.split('(?<=[.!?]) +', text)
    final_phrases = []
    for s in sentences:
        if len(s) > max_chars:
            words = s.split(' ')
            chunk = ""
            for word in words:
                if len(chunk) + len(word) < max_chars:
                    chunk += word + " "
                else:
                    final_phrases.append(chunk.strip())
                    chunk = word + " "
            final_phrases.append(chunk.strip())
        else:
            final_phrases.append(s.strip())
    return [p for p in final_phrases if p]

def get_mood_music(channel_name, duration):
    music_cfg = v_cfg.get('audio', {})
    music_map = music_cfg.get('music_map', {})
    track_name = music_map.get(channel_name, music_map.get("Default", "bg_default.mp3"))
    target = os.path.join(MUSIC_DIR, track_name)
    
    if os.path.exists(target):
        vol = music_cfg.get('music_volume', 0.12)
        music = AudioFileClip(target).volumex(vol).set_duration(duration)
        if music.duration < duration:
            from moviepy.audio.fx.all import audio_loop
            music = audio_loop(music, duration=duration)
        return music
    return None

def fetch_images(item_data, index, channel_name):
    raw_dir = os.path.join(BASE_DIR, f"temp_raw_{channel_name}_{index}")
    if os.path.exists(raw_dir): shutil.rmtree(raw_dir)
    os.makedirs(raw_dir)
    
    meta = item_data.get('metadata', {})
    search_query = meta.get('search_key', '').split('|')[0].strip()
    if not search_query: search_query = item_data.get('headline', 'news')
        
    crawler = BingImageCrawler(storage={'root_dir': raw_dir}, log_level=50)
    max_imgs = v_cfg.get('timing', {}).get('images_per_scene', 4)
    crawler.crawl(keyword=search_query, max_num=max_imgs)
    return [os.path.join(raw_dir, f) for f in os.listdir(raw_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]

def generate_video_single(json_path, index, channel, scene_date):
    try:
        channel_name = channel 
        print(f"🎬 Processing {channel_name}...")
        
        with open(json_path, "r", encoding="utf-8") as f:
            items = json.load(f)
        
        item = items[index]
        scene_id = f"{channel_name}_{index}"
        
        # --- SCRIPT & AUDIO ---
        headline_text = item.get('headline') or "Trending Update"
        intro_hook = item.get('hook_text') or ""
        main_details = item.get('details') or item.get('content') or ""
        sub_hook = item.get('subscribe_hook') or ""
        
        full_text = f"{intro_hook} {main_details} {sub_hook if sub_hook.upper() != 'NONE' else ''}"
        full_text = " ".join(full_text.split()).strip()

        tts_path = os.path.join(BASE_DIR, f"temp_vo_{scene_id}.mp3")
        gTTS(text=full_text, lang=v_cfg.get('audio', {}).get('tts_lang', 'en')).save(tts_path)
        voice = AudioFileClip(tts_path)
        dur = voice.duration
        
        bg_m = get_mood_music(channel_name, dur)
        final_audio = CompositeAudioClip([voice, bg_m]) if bg_m else voice

        # --- VISUALS ---
        img_paths = fetch_images(item, index, channel_name)
        if img_paths:
            time_per_img = dur / len(img_paths)
            clips = [ImageClip(p).set_duration(time_per_img).resize(width=W) for p in img_paths]
            slideshow = concatenate_videoclips(clips, method="compose").set_position('center')
        else:
            fallback_bg = v_cfg.get('visuals', {}).get('bg_color_fallback', [30, 30, 30])
            slideshow = ColorClip(size=(W, H), color=fallback_bg).set_duration(dur)

        # --- OVERLAYS ---
        style = v_cfg.get('style', {})
        head_bg = ColorClip(size=(W, 250), color=(0,0,0)).set_opacity(style.get('overlay_opacity', 0.7)).set_duration(dur).set_position(('center', 0))
        headline = TextClip(headline_text.upper(), fontsize=style.get('headline_font_size', 70), 
                            color=style.get('headline_color', 'yellow'), font='Arial-Bold',
                            method='caption', size=(W-80, None)).set_duration(dur).set_position(('center', 50))
        
        # --- SUBTITLES ---
        phrases = split_into_phrases(full_text)
        phrase_dur = dur / len(phrases)
        sub_clips = []
        for i, phrase in enumerate(phrases):
            p_clip = TextClip(phrase.upper(), fontsize=style.get('subtitle_font_size', 75), 
                              color=style.get('subtitle_color', 'white'), font='Arial-Bold',
                              stroke_color='black', stroke_width=2, method='caption', 
                              size=(W-200, None)).set_start(i * phrase_dur).set_duration(phrase_dur).set_position(('center', 1400))
            sub_clips.append(p_clip)

        # --- PROGRESS BAR ---
        def make_frame(t):
            curr_w = max(2, int((t/dur) * W))
            pb_h = style.get('progress_bar_height', 15)
            frame = np.zeros((pb_h, W, 3), dtype="uint8")
            frame[:, :curr_w] = style.get('progress_bar_color', [255, 230, 0])
            return frame
        prog_bar = VideoClip(make_frame, duration=dur).set_position((0, H - 160))

        # --- ASSEMBLY ---
        final_video = CompositeVideoClip([slideshow, head_bg, headline, *sub_clips, prog_bar], size=(W, H)).set_audio(final_audio)
        
        output_dir = os.path.join(BASE_DIR, "Ready_to_Upload")
        os.makedirs(output_dir, exist_ok=True)
        final_path = os.path.join(output_dir, f"Render_{scene_id}.mp4")
        
        final_video.write_videofile(final_path, fps=FPS, codec="libx264", audio_codec="aac", logger=None)
        
        final_video.close(); voice.close(); gc.collect()
        if os.path.exists(tts_path): os.remove(tts_path)
        return final_path

    except Exception as e:
        print(f"❌ Render Error: {str(e)}")
        return None