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
    VideoClip 
)
from moviepy.config import change_settings

# --- SYSTEM CONFIG ---
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})

W, H = 1080, 1920 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
MUSIC_DIR = os.path.join(ASSETS_DIR, "music")

def split_into_phrases(text, max_chars=35):
    """Splits text into readable chunks for better viewer engagement."""
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
    bg_music_map = {
        "trendwave_now": "bg_cricket.mp3",
        "SpaceMindAI": "bg_space.mp3",
        "ExamPulse": "bg_education.mp3",
        "WonderFacts24_7": "bg_facts.mp3"
    }
    track_name = bg_music_map.get(channel_name, "bg_default.mp3")
    target = os.path.join(MUSIC_DIR, track_name)
    if os.path.exists(target):
        music = AudioFileClip(target).volumex(0.12).set_duration(duration)
        if music.duration < duration:
            from moviepy.audio.fx.all import audio_loop
            music = audio_loop(music, duration=duration)
        return music
    return None

def fetch_images(item_data, index, channel_name):
    raw_dir = os.path.join(BASE_DIR, f"temp_raw_{channel_name}_{index}")
    if os.path.exists(raw_dir): shutil.rmtree(raw_dir)
    os.makedirs(raw_dir)
    search_query = item_data['metadata'].get('search_key', '').split('|')[0].strip()
    if not search_query: search_query = item_data['headline']
    crawler = BingImageCrawler(storage={'root_dir': raw_dir}, log_level=50)
    crawler.crawl(keyword=search_query, max_num=4)
    return [os.path.join(raw_dir, f) for f in os.listdir(raw_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]

# FIXED: Added scene_date to the arguments
def generate_video_single(json_path, index, channel, scene_date):
    try:
        channel_name = channel 
        print(f"🎬 Processing {channel_name} for date: {scene_date}")
        
        with open(json_path, "r", encoding="utf-8") as f:
            items = json.load(f)
        item = items[index]
        scene_id = f"{channel_name}_{index}"
        output_filename = f"Render_{scene_id}.mp4"

        # 1. AUDIO
        full_text = f"{item['hook_text']} {item['details']}"
        tts_path = os.path.join(BASE_DIR, f"temp_vo_{scene_id}.mp3")
        gTTS(text=full_text, lang='en').save(tts_path)
        voice = AudioFileClip(tts_path)
        dur = voice.duration
        bg_music = get_mood_music(channel_name, dur)
        from moviepy.audio.AudioClip import CompositeAudioClip
        final_audio = CompositeAudioClip([voice, bg_music]) if bg_music else voice

        # 2. VISUALS
        img_paths = fetch_images(item, index, channel_name)
        if img_paths:
            time_per_img = dur / len(img_paths)
            clips = [ImageClip(p).set_duration(time_per_img).resize(width=W) for p in img_paths]
            slideshow = concatenate_videoclips(clips, method="compose").set_position('center')
        else:
            slideshow = ColorClip(size=(W, H), color=(30,30,30)).set_duration(dur)

        # 3. OVERLAYS (Using scene_date here)
        head_bg = ColorClip(size=(W, 250), color=(0,0,0)).set_opacity(0.7).set_duration(dur).set_position(('center', 0))
        headline = TextClip(item['headline'].upper(), fontsize=70, color='yellow', font='Arial-Bold',
                            method='caption', size=(W-80, None)).set_duration(dur).set_position(('center', 50))
        loc_tag = TextClip(f"📍 {item['location'].upper()} | {scene_date}", fontsize=28, color='white', 
                            bg_color='darkred').set_duration(dur).set_position((40, 260))

        # 4. SENTENCE-BASED SUBTITLES
        phrases = split_into_phrases(full_text)
        phrase_dur = dur / len(phrases)
        sub_clips = []
        for i, phrase in enumerate(phrases):
            p_clip = TextClip(phrase.upper(), fontsize=75, color='white', font='Arial-Bold',
                              stroke_color='black', stroke_width=2, method='caption', size=(W-200, None)).set_start(i * phrase_dur).set_duration(phrase_dur).set_position(('center', 1400))
            sub_clips.append(p_clip)

        # 5. PROGRESS BAR
        def make_frame(t):
            curr_w = max(2, int((t/dur) * W))
            frame = np.zeros((15, W, 3), dtype="uint8")
            frame[:, :curr_w] = [255, 230, 0] 
            return frame
        prog_bar = VideoClip(make_frame, duration=dur).set_position((0, H - 160))

        # 6. ASSEMBLY
        final_video = CompositeVideoClip([slideshow, head_bg, headline, loc_tag, *sub_clips, prog_bar], size=(W, H)).set_audio(final_audio)
        final_video.write_videofile(output_filename, fps=24, codec="libx264", audio_codec="aac", logger=None)
        
        final_video.close(); voice.close(); gc.collect()
        if os.path.exists(tts_path): os.remove(tts_path)
        return output_filename

    except Exception as e:
        print(f"❌ Error in Process {index}: {str(e)}")
        return None