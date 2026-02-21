import os
import json
import datetime
import tkinter as tk
from tkinter import filedialog
from stage3_upload import get_authenticated_service, upload_video_with_service

# --- CONFIGURATION ---
UPLOAD_DIR = "Ready_to_Upload"
BACKUP_DIR = "backups"

def log_event(message):
    """Prints a timestamped debug message."""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [DEBUG] {message}")

def run_batch_upload():
    print("\n" + "="*40 + "\n📦 MULTI-CHANNEL BATCH MANAGER\n" + "="*40)
    
    # 1. Select JSON File
    log_event("Opening file selector...")
    root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
    json_path = filedialog.askopenfilename(title="Select the JSON used for rendering")
    root.destroy()

    if not json_path:
        log_event("No JSON selected. Exiting.")
        return

    # 2. Load JSON Data
    with open(json_path, "r", encoding="utf-8") as f:
        items = json.load(f)
    log_event(f"Loaded {len(items)} items from JSON.")

    # 3. Scan Folder Contents
    if not os.path.exists(UPLOAD_DIR):
        log_event(f"CRITICAL: Folder '{UPLOAD_DIR}' not found!")
        return
        
    actual_files = os.listdir(UPLOAD_DIR)
    log_event(f"Files currently in {UPLOAD_DIR}: {actual_files}")

    # 4. Process Each Item
    for i, item in enumerate(items):
        target_channel = item.get('channel', 'TrendWave Now')
        video_filename = f"Render_{target_channel}_{i}.mp4"
        video_path = os.path.join(UPLOAD_DIR, video_filename)
        
        log_event(f"Searching for Scene {i}: {video_filename}...")

        if os.path.exists(video_path):
            log_event(f"✅ MATCH FOUND: {video_path}")
            
            # --- METADATA GENERATION ---
            title = f"{item['headline']} | {item['news_type']}"
            description = (
                f"{item['hook_text']}\n\n"
                f"{item['details']}\n\n"
                f"Location: {item['location']}\n"
                f"Date: {item['date']}\n"
                f"\n#TrendWaveNow #{item['news_type'].replace(' ', '')}"
            )
            
            # Prepare metadata for upload service
            metadata = {
                "title": title[:100],  # YouTube Title Limit
                "description": description,
                "tags": [item['news_type'], item['location'].split(',')[0]]
            }

            # --- UPLOAD PROCESS ---
            log_event(f"Initializing upload to channel: {target_channel}")
            try:
                service = get_authenticated_service(target_channel)
                video_id = upload_video_with_service(service, video_path, metadata, target_channel)
                
                if video_id:
                    log_event(f"🚀 SUCCESS! Video ID: {video_id}")
                    
                    # Move to Backups
                    os.makedirs(BACKUP_DIR, exist_ok=True)
                    dest_path = os.path.join(BACKUP_DIR, video_filename)
                    os.rename(video_path, dest_path)
                    log_event(f"Moved {video_filename} to {BACKUP_DIR}")
                else:
                    log_event(f"⚠️ SHIELD ACTIVE: Upload skipped for {video_filename}.")
            except Exception as e:
                log_event(f"❌ UPLOAD ERROR: {str(e)}")
        else:
            log_event(f"❌ MISSING: Could not find {video_filename} in {UPLOAD_DIR}")

if __name__ == "__main__":
    run_batch_upload()