import json
import multiprocessing
import tkinter as tk
from tkinter import filedialog
import os
from datetime import datetime, timedelta
from processor import generate_video_single

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

if __name__ == "__main__":
    multiprocessing.freeze_support()
    run()