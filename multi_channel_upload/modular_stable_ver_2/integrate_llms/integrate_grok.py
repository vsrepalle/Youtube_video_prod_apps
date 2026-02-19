import os
import re
import json
import subprocess
import sys
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# Load security keys
load_dotenv()

# --- DIRECTORY CONFIG ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- HARDCODED MASTER JSON STRUCTURE ---
JSON_TEMPLATE = """
[
  {
    "day": "Day Name",
    "date": "2026-02-19",
    "location": "City/Country",
    "type": "cricket or bollywood or facts",
    "channel": "{CHANNEL_NAME}",
    "headline": "Title",
    "hook_text": "Engaging start",
    "details": "Main content",
    "subscribe_hook": "NONE",
    "description": "Hashtags and summary",
    "metadata": {
      "title": "SEO Title",
      "tags": ["tag1", "tag2"],
      "search_key": "Keyword A | Keyword B"
    }
  }
]
"""

def clean_json_response(raw_text):
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
    return match.group(1).strip() if match else raw_text.strip()

def get_ai_answer(channel, user_topic):
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.getenv("GROQ_API_KEY")
    )
    prompt = f"""
    Generate 3 news/fact entries for the channel '{channel}' about '{user_topic}'.
    STRUCTURE: Use this exact JSON format: {JSON_TEMPLATE.replace("{CHANNEL_NAME}", channel)}
    
    STRICT RULES:
    1. Only provide valid JSON.
    2. LAST item only: 'details' must end with "Tune with us for more such news." 
       AND 'subscribe_hook' must be "Want to know more? Subscribe now!"
    3. All other items: 'subscribe_hook' must be "NONE".
    4. Use search_key format: 'Primary Topic | Secondary Topic'.
    """
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return clean_json_response(completion.choices[0].message.content)
    except Exception as e:
        return f"❌ AI Error: {e}"

def save_and_run(json_data, channel_name):
    # 1. Setup paths
    folder = os.path.join(BASE_DIR, "generated_content")
    os.makedirs(folder, exist_ok=True)
    static_filepath = os.path.join(folder, "news_data.json")
    
    with open(static_filepath, "w", encoding="utf-8") as f:
        f.write(json_data)
    
    # 2. LOCATE CONTROLLER.PY
    # This assumes controller.py is in the SAME folder as integrate_grok.py
    # If it's one folder up, use: os.path.join(os.path.dirname(BASE_DIR), "controller.py")
    controller_path = os.path.join(BASE_DIR, "controller.py")

    print(f"\n--- 📝 GENERATED CONTENT PREVIEW ---")
    try:
        data = json.loads(json_data)
        print(f"Final Scene Hook: {data[-1].get('subscribe_hook', 'NONE')}")
    except: pass
        
    print(f"\n✅ Data saved to: {static_filepath}")
    
    # Check if controller exists before running
    if not os.path.exists(controller_path):
        print(f"❌ Error: Cannot find controller.py at {controller_path}")
        print("Please ensure both files are in the same directory.")
        return

    print(f"🚀 Launching: {controller_path}")

    try:
        # Use the full path to the controller
        subprocess.run(["python", controller_path, static_filepath], check=True)
    except Exception as e:
        print(f"❌ Automation Error: {e}")
        
if __name__ == "__main__":
    channel = input("📺 Enter Channel Name: ")
    topic = input("📝 Enter Topic: ")
    result = get_ai_answer(channel, topic)
    
    if result.strip().startswith("["):
        save_and_run(result, channel)
    else:
        print("Invalid JSON received.")