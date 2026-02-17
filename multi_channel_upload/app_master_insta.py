import os, json, shutil, time
from datetime import datetime
from gtts import gTTS
from moviepy.editor import *
from moviepy.config import change_settings
from PIL import Image

# --- CONFIG ---
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})
W, H = 720, 1280 
SPEED_FACTOR = 1.15  # Slightly faster for Insta retention

def generate_video(json_file):
    with open(json_file, "r", encoding="utf-8") as f: 
        items = json.load(f)

    for i, item in enumerate(items):
        chan_id = item.get('channel_id', 'exampulse24_7')
        print(f"\n🎬 Creating Dual-Platform Video {i+1}")
        
        # Audio
        q_path, a_path = f"q_{i}.mp3", f"a_{i}.mp3"
        gTTS(text=item['hook_text'], lang='en').save(q_path)
        gTTS(text=item['details'], lang='en').save(a_path)
        audio = concatenate_audioclips([AudioFileClip(q_path), AudioClip(lambda t: [0,0], duration=1.0), AudioFileClip(a_path)])
        dur = audio.duration

        # --- INSTA OPTIMIZED SUBTITLES ---
        # Moved to center-middle (y=550) to avoid Instagram's "Like/Comment" buttons and "Caption" overlay
        subtitles = TextClip(f"{item['hook_text']}\n\n{item['details']}", 
                             fontsize=36, color='white', font='Arial-Bold',
                             stroke_color='black', stroke_width=2,
                             method='caption', size=(W-120, None), align='center').set_duration(dur).set_position(('center', 650))

        # Watermark (Smaller for Insta)
        watermark = TextClip(f"Follow: @{chan_id}", fontsize=22, color='white', 
                             font='Arial-Bold').set_duration(dur).set_opacity(0.5).set_position(('right', 30))

        # Visuals (Using a darker background for "Mars Water" cinematic feel)
        bg = ColorClip(size=(W, H), color=(5, 5, 20)).set_duration(dur)
        header = TextClip(item['headline'], fontsize=50, color='yellow', font='Arial-Bold',
                          size=(W-100, None), method='caption').set_duration(dur).set_position(('center', 150))

        # Compile
        final_video = CompositeVideoClip([bg, header, subtitles, watermark]).set_audio(audio)
        final_video = final_video.fx(vfx.speedx, SPEED_FACTOR)

        # Output for YouTube (Standard)
        yt_name = f"YT_Short_{i}.mp4"
        final_video.write_videofile(yt_name, fps=30, codec="libx264")

        # Output for Instagram (High Saturation/Vibrant)
        insta_name = f"INSTA_Reel_{i}.mp4"
        insta_video = final_video.fx(vfx.colorx, 1.2) # Boost colors for Insta
        insta_video.write_videofile(insta_name, fps=30, codec="libx264")

        print(f"✅ YT Saved: {yt_name} | ✅ Insta Saved: {insta_name}")

if __name__ == "__main__":
    generate_video("news_data.json")