import os
import json
import datetime
import tkinter as tk
from tkinter import filedialog
from stage3_upload import get_authenticated_service, upload_video_with_service

def log_success(channel, title, video_id):
    """Saves upload details to a permanent text file."""
    log_file = "upload_history.txt"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] CHANNEL: {channel} | TITLE: {title} | URL: https://youtu.be/{video_id}\n"
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)

def run_batch_upload():
    print("\n" + "="*40 + "\n📦 MULTI-CHANNEL BATCH MANAGER\n" + "="*40)
    
    root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
    json_path = filedialog.askopenfilename(title="Select the JSON used for rendering")
    root.destroy()

    if not json_path: return

    with open(json_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    for i, item in enumerate(items):
        target_channel = item.get('channel', item.get('type', 'default'))
        video_filename = f"Render_{target_channel}_{i}.mp4"
        
        if os.path.exists(video_filename):
            print(f"\n📡 Found matching file: {video_filename}")
            service = get_authenticated_service(target_channel)
            
            # 1. Attempt Upload
            video_id = upload_video_with_service(service, video_filename, item, target_channel)
            
            # 2. If successful, Log and Move
            if video_id:
                log_success(target_channel, item['headline'], video_id)
                
                os.makedirs("backups", exist_ok=True)
                dest_path = os.path.join("backups", video_filename)
                if os.path.exists(dest_path):
                    ts = int(os.path.getmtime(video_filename))
                    dest_path = os.path.join("backups", f"{ts}_{video_filename}")
                
                os.rename(video_filename, dest_path)
                print(f"📦 Logged and Moved to: {dest_path}")
            else:
                print(f"⚠️ Keeping {video_filename} (Upload Skipped by Shield).")
        else:
            print(f"⚠️ Missing: {video_filename}")

if __name__ == "__main__":
    run_batch_upload()