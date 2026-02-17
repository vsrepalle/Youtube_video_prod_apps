import numpy as np
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# --------------------------------------------------
# ROUNDED BOX GENERATOR
# --------------------------------------------------
def create_rounded_box(w, h, color, radius=40, opacity=230):
    rect_img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(rect_img)
    fill_color = color + (opacity,)
    draw.rounded_rectangle([0, 0, w, h], radius=radius, fill=fill_color)
    return ImageClip(np.array(rect_img))

# --------------------------------------------------
# STYLED HEADER WITH GLOW
# --------------------------------------------------
def get_styled_header(text, dur, W):
    box_w, box_h = W - 60, 200
    
    # Glow effect
    glow_img = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_img)
    try: font = ImageFont.truetype("arialbd.ttf", 48)
    except: font = ImageFont.load_default()
    
    glow_draw.text((box_w//2, box_h//2), text.upper(), fill=(255, 255, 0, 180), anchor="mm", font=font)
    glow_img = glow_img.filter(ImageFilter.GaussianBlur(radius=15))
    glow_clip = ImageClip(np.array(glow_img)).set_duration(dur).set_opacity(0.6)

    # Box and Main Text
    bg = create_rounded_box(box_w, box_h, (10, 20, 45), opacity=245).set_duration(dur)
    txt = TextClip(text.upper(), fontsize=44, color='yellow', font='Arial-Bold',
                   size=(box_w - 40, box_h - 20), method='caption').set_position('center').set_duration(dur)

    header = CompositeVideoClip([bg, glow_clip, txt], size=(box_w, box_h)).set_duration(dur)
    return header.set_position(lambda t: ('center', 60 - 5 * (t / dur))).fadein(0.5)

# --------------------------------------------------
# STYLED TICKER
# --------------------------------------------------
def get_styled_ticker(text, dur, W):
    box_h = 120
    box_w = W - 40
    bg = create_rounded_box(box_w, box_h, (130, 0, 0), opacity=255).set_duration(dur)
    txt = TextClip(text, fontsize=32, color='white', font='Arial-Bold', method='label').set_duration(dur)
    
    scroll_speed = (txt.w + box_w) / dur
    txt_scrolling = txt.set_position(lambda t: (box_w - (scroll_speed * t), 'center'))
    
    return CompositeVideoClip([bg, txt_scrolling], size=(box_w, box_h)).set_duration(dur).fadein(0.6)

# --------------------------------------------------
# PROGRESS BAR
# --------------------------------------------------
def get_progress_bar(dur, W, H):
    bar_h = 14
    def make_frame(t):
        prog_w = max(1, int((t / dur) * W))
        img = np.zeros((bar_h, W, 3), dtype="uint8")
        img[:, :prog_w] = [255, 215, 0] 
        return img
    return VideoClip(make_frame, duration=dur).set_position(('center', H - bar_h))