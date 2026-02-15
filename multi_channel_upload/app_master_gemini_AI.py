import customtkinter as ctk
import json
import os
import threading
from difflib import SequenceMatcher
from google import genai
from openai import OpenAI  # Used for the NVIDIA NIM Fallback
from create_video import generate_video

# --- 1. CONFIGURATION ---
HISTORY_FILE = "news_history.json"
GEMINI_KEY = "AIzaSyBEN__vT3tOUs83xEOOl9gdomLI4QYdH7w"
NVIDIA_KEY = "YOUR_NVIDIA_API_KEY"
MODEL_GEMINI = 'gemini-2.0-flash'
MODEL_NIM = "z-ai/glm5" # GLM-5 endpoint on NVIDIA NIM

# Clients
gemini_client = genai.Client(api_key=GEMINI_KEY)
nim_client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=NVIDIA_KEY)

# --- 2. THE STABLE SCHEMA ---
JSON_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "channel_id": {"type": "STRING"},
            "hook_text": {"type": "STRING"},
            "headline": {"type": "STRING"},
            "details": {"type": "STRING"},
            "search_key": {"type": "STRING"}
        },
        "required": ["channel_id", "hook_text", "headline", "details", "search_key"]
    }
}

class YoutubeAutomationApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gemini + NIM Fallback Automator 2026")
        self.geometry("600x650")
        
        self.label = ctk.CTkLabel(self, text="Dual-Engine Pipeline", font=("Arial", 22, "bold"))
        self.label.pack(pady=15)
        self.status_box = ctk.CTkTextbox(self, width=520, height=380)
        self.status_box.pack(pady=10)
        self.run_btn = ctk.CTkButton(self, text="START AUTOMATION", command=self.run_threaded)
        self.run_btn.pack(pady=15)

    def log(self, message):
        self.status_box.insert("end", f"> {message}\n")
        self.status_box.see("end")

    def fetch_with_nim(self, prompt):
        """Fallback: Fetches JSON from GLM-5 via NVIDIA NIM"""
        self.log("🔄 SWITCHING TO FALLBACK: GLM-5 (NVIDIA NIM)...")
        response = nim_client.chat.completions.create(
            model=MODEL_NIM,
            messages=[{"role": "user", "content": f"{prompt}\nReturn JSON matching this schema: {json.dumps(JSON_SCHEMA)}"}],
            response_format={"type": "json_object"}
        )
        # GLM-5 Thinking mode often wraps content, so we parse carefully
        return json.loads(response.choices[0].message.content)

    def run_threaded(self):
        self.run_btn.configure(state="disabled")
        threading.Thread(target=self.start_automation, daemon=True).start()

    def start_automation(self):
        prompt = """Generate news for 4 channels for Feb 15, 2026 (TrendWave, SpaceMind, ExamPulse, WonderFacts).
        Include Colombo rain news for cricket and Artemis 2 hydrogen fuel test success.
        Details must end with 'Tune with us for more such news.'
        Search key format: 'Keyword | Context'."""

        try:
            # --- PRIMARY ATTEMPT: GEMINI ---
            self.log("Attempting primary fetch: Gemini AI...")
            response = gemini_client.models.generate_content(
                model=MODEL_GEMINI,
                contents=prompt,
                config={'response_mime_type': 'application/json', 'response_schema': JSON_SCHEMA}
            )
            data = response.parsed
            self.log("✅ Gemini Success.")

        except Exception as e:
            # --- FALLBACK ATTEMPT: NVIDIA NIM ---
            if "429" in str(e) or "exhausted" in str(e).lower():
                try:
                    data = self.fetch_with_nim(prompt)
                    # Handle case where NIM returns a dict instead of a list
                    if isinstance(data, dict) and "items" in data: data = data["items"]
                    elif isinstance(data, dict) and not isinstance(data, list): data = [data]
                except Exception as nim_e:
                    self.log(f"❌ BOTH ENGINES FAILED: {str(nim_e)}")
                    return
            else:
                self.log(f"❌ GEMINI ERROR: {str(e)}")
                return

        # --- PROCESS VIDEOS ---
        for i, entry in enumerate(data):
            channel = entry['channel_id']
            self.log(f"🎬 Creating video for {channel}...")
            temp_file = f"temp_{channel}.json"
            with open(temp_file, "w") as f: json.dump([entry], f)
            generate_video(temp_file)
            
        self.log("🚀 ALL VIDEOS PROCESSED SUCCESSFULLY.")
        self.run_btn.configure(state="normal")

if __name__ == "__main__":
    app = YoutubeAutomationApp()
    app.mainloop()