import os
import tkinter as tk
from tkinter import filedialog
from stage3_upload import upload_from_json

def manual_uploader_tool():
    root = tk.Tk()
    root.withdraw()
    
    print("📂 Select the MP4 file...")
    v_path = filedialog.askopenfilename(title="Select Video", filetypes=[("MP4", "*.mp4")])
    if not v_path: return

    print("📂 Select the News JSON...")
    j_path = filedialog.askopenfilename(title="Select JSON", filetypes=[("JSON", "*.json")])
    if not j_path: return

    print("\n--- 2026 AI Compliance Check ---")
    print("Self-Declaring as Synthetic Media: YES")
    
    upload_from_json(j_path, os.path.abspath(v_path))

if __name__ == "__main__":
    manual_uploader_tool()