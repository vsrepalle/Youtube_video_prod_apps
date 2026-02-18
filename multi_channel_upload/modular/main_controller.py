import json
import multiprocessing
import tkinter as tk
from tkinter import filedialog
import os
from processor import generate_video_single

def run():
    print("\n" + "="*40 + "\n🚀 MULTI-CHANNEL CONTROLLER\n" + "="*40)

    # Select JSON
    root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
    selected_json = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
    root.destroy()

    if not selected_json: return

    with open(selected_json, "r", encoding="utf-8") as f:
        items = json.load(f)

    print(f"✅ Ready to process {len(items)} scenes.")
    mode = input("🚀 Parallel Render? (y/n): ").lower()
    
    if mode == 'y':
        processes = []
        for i in range(len(items)):
            # --- FIX: GET CHANNEL PER SCENE ---
            # If "channel" field exists in JSON, use it. Otherwise, use "type".
            scene_channel = items[i].get('channel', items[i].get('type', 'default'))
            
            p = multiprocessing.Process(
                target=generate_video_single, 
                args=(selected_json, i, scene_channel)
            )
            p.start()
            processes.append(p)
        for p in processes: p.join()
    else:
        for i in range(len(items)):
            scene_channel = items[i].get('channel', items[i].get('type', 'default'))
            generate_video_single(selected_json, i, scene_channel)

    print("\n🏆 Rendering Cycle Complete. Files are now ready for batch_manager.py")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    run()