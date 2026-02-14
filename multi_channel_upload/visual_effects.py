import os
from moviepy.editor import *
from PIL import Image, ImageDraw

def create_rounded_box(w, h, color, radius=40, opacity=220):
    rect_img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(rect_img)
    fill_color = color + (opacity,) 
    draw.rounded_rectangle([0, 0, w, h], radius=radius, fill=fill_color)
    temp_p = "temp_box.png"
    rect_img.save(temp_p)
    clip = ImageClip(temp_p).set_ismask(False)
    return clip

def get_styled_header(text, dur, W):
    box_w, box_h = W - 60, 160
    bg = create_rounded_box(box_w, box_h, (15, 25, 55), opacity=240)
    txt = TextClip(text.upper(), fontsize=42, color='yellow', font='Arial-Bold', 
                   size=(box_w-40, box_h-20), method='caption').set_position('center')
    return CompositeVideoClip([bg, txt]).set_duration(dur)

def get_styled_ticker(text, dur, W, box_h):
    box_w = W - 40
    bg = create_rounded_box(box_w, box_h, (100, 0, 0), opacity=255)
    txt = TextClip(text, fontsize=32, color='white', font='Arial-Bold', method='caption',
                   size=(box_w-60, box_h-40), align='center').set_position('center')
    return CompositeVideoClip([bg, txt]).set_duration(dur)

def get_progress_bar(dur, W, H):
    """Creates a pulsing yellow progress bar for high engagement."""
    base = ColorClip(size=(W, 12), color=(30, 30, 30)).set_duration(dur).set_opacity(0.6)
    
    def make_frame(t):
        progress_w = max(1, int((t / dur) * W))
        # Add a slight pulsing effect to the color for 'Glow'
        pulse = 200 + int(55 * (t % 1)) 
        return ColorClip(size=(progress_w, 12), color=(pulse, pulse, 0)).to_ImageClip().img
    
    bar = VideoClip(make_frame, duration=dur).set_position(('left', 'bottom'))
    return CompositeVideoClip([base, bar]).set_position(('center', H-12))