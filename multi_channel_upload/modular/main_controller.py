import os
import tkinter as tk
from tkinter import filedialog
# Importing from our modular files
from processor import generate_video
from stage3_upload import get_authenticated_service

def run():
    print("🔐 Authenticating YouTube Account...")
    # This triggers the one-time browser login or loads token.pickle
    youtube_service = get_authenticated_service()

    # File Selection UI
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    print("📁 Please select your News JSON file...")
    selected_json = filedialog.askopenfilename(
        title="Select News Metadata JSON", 
        filetypes=[("JSON Files", "*.json")]
    )
    root.destroy()

    if selected_json:
        # Pass both the JSON and the active YouTube service to the processor
        generate_video(selected_json, youtube_service)
    else:
        print("🛑 Operation cancelled: No JSON file selected.")

if __name__ == "__main__":
    run()