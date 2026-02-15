import customtkinter as ctk
import json
import threading
from google import genai
from openai import OpenAI
from create_video import generate_video

# --- CONFIG ---
GEMINI_KEY = "AIzaSyBEN__vT3tOUs83xEOOl9gdomLI4QYdH7w"
NVIDIA_KEY = "YOUR_NVIDIA_API_KEY"
MODEL_GEMINI = 'gemini-2.0-flash'
MODEL_NIM = "z-ai/glm5"

# Initialize Clients
gemini_client = genai.Client(api_key=GEMINI_KEY)
nim_client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=NVIDIA_KEY)

class YoutubeAutomationApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Pipeline 2026")
        self.geometry("750x850")
        
        # UI Setup
        self.label = ctk.CTkLabel(self, text="Automation Pipeline", font=("Arial", 24, "bold"))
        self.label.pack(pady=20)

        # 1. AI Fetch Section
        self.auto_btn = ctk.CTkButton(self, text="✨ AUTO-GENERATE ALL NEWS", height=45, 
                                      fg_color="#3b8ed0", command=lambda: self.run_threaded("auto"))
        self.auto_btn.pack(pady=10)

        ctk.CTkLabel(self, text="──────────────── OR ────────────────").pack(pady=10)

        # 2. Manual JSON Section
        self.manual_label = ctk.CTkLabel(self, text="Paste JSON Content Below:", font=("Arial", 14))
        self.manual_label.pack(pady=5)
        
        self.manual_entry = ctk.CTkTextbox(self, width=650, height=250, border_width=2)
        self.manual_entry.pack(pady=5)

        # --- THE SUBMIT BUTTON ---
        self.submit_btn = ctk.CTkButton(self, text="🚀 SUBMIT MANUAL JSON", 
                                        fg_color="#27ae60", hover_color="#219150",
                                        height=50, width=250, font=("Arial", 16, "bold"),
                                        command=lambda: self.run_threaded("manual"))
        self.submit_btn.pack(pady=20)

        # 3. Status Output
        self.status_box = ctk.CTkTextbox(self, width=650, height=200, fg_color="#1e1e1e", text_color="#00ff00")
        self.status_box.pack(pady=10)

    def log(self, message):
        self.status_box.insert("end", f"> {message}\n")
        self.status_box.see("end")

    def run_threaded(self, mode):
        # Disable buttons during run
        self.submit_btn.configure(state="disabled")
        self.auto_btn.configure(state="disabled")
        threading.Thread(target=self.start_pipeline, args=(mode,), daemon=True).start()

    def start_pipeline(self, mode):
        data = []
        try:
            if mode == "manual":
                user_input = self.manual_entry.get("1.0", "end").strip()
                if not user_input:
                    self.log("❌ ERROR: Please paste JSON before submitting.")
                    return
                data = json.loads(user_input)
                self.log("✅ Manual JSON Loaded Successfully.")
            else:
                self.log("Connecting to AI engines...")
                # Fetch logic here...
                return

            # Processing
            if isinstance(data, dict): data = [data]
            for entry in data:
                channel = entry.get('channel_id', 'Unknown')
                self.log(f"🎬 Starting render for: {channel}")
                # Save and generate video
                with open(f"temp_{channel}.json", "w") as f:
                    json.dump([entry], f)
                generate_video(f"temp_{channel}.json")
            
            self.log("🏁 ALL VIDEOS GENERATED.")
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR: {str(e)}")
        finally:
            self.submit_btn.configure(state="normal")
            self.auto_btn.configure(state="normal")

if __name__ == "__main__":
    app = YoutubeAutomationApp()
    app.mainloop()