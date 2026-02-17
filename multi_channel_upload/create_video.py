import os, json, shutil
from datetime import datetime
from gtts import gTTS
from moviepy.editor import *
from moviepy.config import change_settings
from PIL import Image
from icrawler.builtin import BingImageCrawler

try:
    from stage3_upload import upload_from_json
except ImportError:
    print("⚠️ stage3_upload.py not found. Uploading will be disabled.")

from visual_effects import get_styled_header, get_styled_ticker, get_progress_bar


# ---------------- CONFIG ----------------
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})

W, H = 720, 1280
BGM_PATH = "bg_music.mp3"


# ---------------- IMAGE FETCH ----------------
def fetch_and_clean_images(query, index):
    raw_dir, clean_dir = f"raw_{index}", f"clean_{index}"

    for d in [raw_dir, clean_dir]:
        if os.path.exists(d):
            shutil.rmtree(d)
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
        except:
            continue

    return valid_paths


# ---------------- CINEMATIC IMAGE EFFECT ----------------
def get_cinematic_slide(image_path, duration):
    """
    Ken Burns zoom + slow vertical motion + fade in/out
    """
    base = ImageClip(image_path).set_duration(duration)

    # Resize properly for Shorts
    base = base.resize(height=580)

    # Slow cinematic zoom
    zoomed = base.resize(lambda t: 1 + 0.08 * (t / duration))

    # Slight vertical float
    moving = zoomed.set_position(
        lambda t: ('center', 280 - 10 * (t / duration))
    )

    return moving.fadein(0.5).fadeout(0.5)


# ---------------- VIDEO GENERATOR ----------------
def generate_video(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        items = json.load(f)

    all_scenes = []

    for i, item in enumerate(items):
        print(f"🎬 Rendering Scene {i+1}...")

        # ---- TTS GENERATION ----
        q_text = f"{item['hook_text']}. {item['headline']}."
        gTTS(text=q_text, lang='en').save(f"q_{i}.mp3")
        q_audio = AudioFileClip(f"q_{i}.mp3")

        a_text = f"{item['details']}"
        gTTS(text=a_text, lang='en').save(f"a_{i}.mp3")
        a_audio = AudioFileClip(f"a_{i}.mp3")

        silence = AudioClip(lambda t: [0, 0], duration=1.5, fps=44100)

        audio = concatenate_audioclips([q_audio, silence, a_audio])
        audio = audio.audio_fadein(0.3)

        dur = audio.duration

        # ---- VISUAL ELEMENTS ----
        header = get_styled_header(item['hook_text'], dur, W)\
            .set_position(('center', 60))\
            .fadein(0.4)

        footer = get_styled_ticker(item['details'], dur, W, 300)\
            .set_position(('center', 920))\
            .fadein(0.5)

        prog_bar = get_progress_bar(dur, W, H)

        # ---- SLIDESHOW ----
        img_paths = fetch_and_clean_images(item.get('search_key', ''), i)

        if img_paths:
            slide_duration = dur / len(img_paths)
            slides = [
                get_cinematic_slide(p, slide_duration)
                for p in img_paths
            ]
            slideshow = concatenate_videoclips(slides, method="compose")
        else:
            slideshow = ColorClip(
                size=(W-100, 580),
                color=(40, 40, 60)
            ).set_duration(dur).set_position(('center', 280))

        # ---- BACKGROUND ----
        bg = ColorClip(size=(W, H), color=(0, 0, 15)).set_duration(dur)

        # ---- COMPOSE SCENE ----
        scene = CompositeVideoClip([
            bg,
            header,
            slideshow,
            footer,
            prog_bar
        ]).set_audio(audio)

        scene = scene.fadein(0.4).fadeout(0.4)

        all_scenes.append(scene)

    # ---- SCENE TRANSITIONS ----
    final_v = concatenate_videoclips(
        all_scenes,
        method="compose",
        padding=-0.4
    )

    # ---- CTA (Animated) ----
    cta_text = "Please Like & Subscribe For More Updates"

    cta = TextClip(
        cta_text,
        fontsize=40,
        color='white',
        bg_color='darkred',
        size=(W, 100),
        method='caption'
    )

    cta = cta.set_start(final_v.duration - 3.5)\
        .set_duration(3.5)\
        .set_position(lambda t: (
            'center',
            H - 250 + 40 * (1 - min(1, t/0.5))
        ))\
        .fadein(0.5)

    final_output = CompositeVideoClip([final_v, cta])

    # ---- BACKGROUND MUSIC ----
    if os.path.exists(BGM_PATH):
        bgm = AudioFileClip(BGM_PATH)\
            .volumex(0.08)\
            .set_duration(final_output.duration)\
            .audio_fadein(1)

        final_output = final_output.set_audio(
            CompositeAudioClip([final_output.audio, bgm])
        )

    # ---- EXPORT ----
    out_name = os.path.abspath(
        f"Viral_Short_{datetime.now().strftime('%M%S')}.mp4"
    )

    final_output.write_videofile(
        out_name,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="medium"
    )

    # ---- CLEANUP ----
    for f in os.listdir():
        if f.endswith(".mp3") and (
            f.startswith("q_") or
            f.startswith("a_")
        ):
            try:
                os.remove(f)
            except:
                pass

    print(f"\n✅ Video Generated: {out_name}")

    user_choice = input("🚀 Upload to YouTube now? (y/n): ").lower()
    if user_choice == 'y':
        upload_from_json(json_file, video_file=out_name)
    else:
        print("⏭️ Upload skipped.")


if __name__ == "__main__":
    generate_video("news_data.json")
