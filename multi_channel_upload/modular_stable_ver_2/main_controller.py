import json
import multiprocessing
import tkinter as tk
from tkinter import filedialog
import os
from datetime import datetime, timedelta
from processor import generate_video_single

import shutil


def run():
    print("\n" + "="*40 + "\n🚀 MULTI-CHANNEL CONTROLLER\n" + "="*40)

    # Select JSON
    root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
    selected_json = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
    root.destroy()

    if not selected_json: 
        print("❌ No file selected. Exiting.")
        return

    with open(selected_json, "r", encoding="utf-8") as f:
        items = json.load(f)

    print(f"✅ Ready to process {len(items)} scenes.")
    mode = input("🚀 Parallel Render? (y/n): ").lower()
    
    if mode == 'y':
        processes = []
        for i in range(len(items)):
            # 1. Determine Channel
            scene_channel = items[i].get('channel', items[i].get('type', 'default'))

            # 2. Calculate Automated Date
            target_date = datetime.now() + timedelta(days=i)
            formatted_date = target_date.strftime("%Y-%m-%d")
            
            # 3. Create and Start Process
            p = multiprocessing.Process(
                target=generate_video_single, 
                args=(selected_json, i, scene_channel, formatted_date) 
            )
            p.start()
            processes.append(p)
            
        for p in processes: 
            p.join()
    else:
        for i in range(len(items)):
            scene_channel = items[i].get('channel', items[i].get('type', 'default'))
            
            # Calculate date for sequential mode too
            target_date = datetime.now() + timedelta(days=i)
            formatted_date = target_date.strftime("%Y-%m-%d")
            
            generate_video_single(selected_json, i, scene_channel, formatted_date)

    print("\n🏆 Rendering Cycle Complete. Files are now ready for batch_manager.py")

def organize_finished_videos():
    """Moves all 'Render_' files into a Ready_to_Upload folder."""
    target_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Ready_to_Upload")
    os.makedirs(target_folder, exist_ok=True)
    
    # Identify files starting with 'Render_' and ending in '.mp4'
    files = [f for f in os.listdir('.') if f.startswith('Render_') and f.endswith('.mp4')]
    
    if not files:
        print("📂 No new renders found to organize.")
        return

    print(f"📂 Organizing {len(files)} videos into 'Ready_to_Upload'...")
    for f in files:
        dest = os.path.join(target_folder, f)
        # If file already exists in destination, it will be overwritten
        shutil.move(f, dest)
        print(f"✅ Moved: {f}")

# --- Inside your run() function, add this to the very end ---
# print("\n🏆 Rendering Cycle Complete...")
# organize_finished_videos() # <--- CALL THIS HERE


if __name__ == "__main__":
    multiprocessing.freeze_support()
    run()