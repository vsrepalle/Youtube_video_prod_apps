import json
import multiprocessing
import tkinter as tk
from tkinter import filedialog
import os
import sys  # Added for path handling
from datetime import datetime, timedelta
from processor import generate_video_single

def run():
    print("\n" + "="*40 + "\n🚀 MULTI-CHANNEL CONTROLLER\n" + "="*40)

    # --- PATH LOGIC UPDATE ---
    # Use the path passed from Grok script if available
    if len(sys.argv) > 1:
        selected_json = sys.argv[1]
    else:
        # Select JSON manually via UI
        root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
        selected_json = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        root.destroy()
    # -------------------------

    if not selected_json or not os.path.exists(selected_json): 
        print(f"❌ No valid file found at: {selected_json}. Exiting.")
        return

    with open(selected_json, "r", encoding="utf-8") as f:
        items = json.load(f)

    print(f"📂 Loaded: {selected_json}")
    print(f"✅ Ready to process {len(items)} scenes.")
    
    # Auto-select parallel if triggered by Grok, otherwise ask
    if len(sys.argv) > 1:
        mode = 'y'
    else:
        mode = input("🚀 Parallel Render? (y/n): ").lower()
    
    if mode == 'y':
        # Limit to 2 concurrent renders to avoid the "Unable to allocate MiB" RAM error
        max_concurrent = 2 
        print(f"🚀 Starting Parallel Render (Max {max_concurrent} at a time)...")
        
        # We use a Pool to manage the queue
        with multiprocessing.Pool(processes=max_concurrent) as pool:
            pool_results = []
            for i in range(len(items)):
                # 1. Determine Channel
                scene_channel = items[i].get('channel', items[i].get('type', 'default'))

                # 2. Calculate Automated Date
                target_date = datetime.now() + timedelta(days=i)
                formatted_date = target_date.strftime("%Y-%m-%d")
                
                # 3. Add to Pool (instead of p.start())
                result = pool.apply_async(
                    generate_video_single, 
                    args=(selected_json, i, scene_channel, formatted_date)
                )
                pool_results.append(result)
            
            # This ensures the script waits for all renders to finish
            for r in pool_results:
                r.get()
    else:
        for i in range(len(items)):
            scene_channel = items[i].get('channel', items[i].get('type', 'default'))
            target_date = datetime.now() + timedelta(days=i)
            formatted_date = target_date.strftime("%Y-%m-%d")
            generate_video_single(selected_json, i, scene_channel, formatted_date)

    print("\n🏆 Rendering Cycle Complete. Files are now ready for batch_manager.py")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    run()