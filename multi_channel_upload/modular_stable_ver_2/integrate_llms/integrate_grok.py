import os
import re
import json
import subprocess
import sys
import time
import select
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- AI LOGIC (Same as before) ---
def get_ai_answer(channel, user_topic):
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.getenv("GROQ_API_KEY"))
    prompt = f"Generate 3 news/fact entries for {channel} about {user_topic}. Use the standard JSON format with subscribe hooks."
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        # Assuming clean_json_response is defined as before
        return completion.choices[0].message.content 
    except Exception as e:
        return f"❌ AI Error: {e}"

def save_and_run(json_data, channel_name):
    folder = os.path.join(BASE_DIR, "generated_content")
    os.makedirs(folder, exist_ok=True)
    static_filepath = os.path.join(folder, "news_data.json")
    with open(static_filepath, "w", encoding="utf-8") as f:
        f.write(json_data)
    
    controller_path = os.path.join(BASE_DIR, "controller.py")
    print(f"🚀 Triggering Parallel Controller for {channel_name}...")
    subprocess.run(["python", controller_path, static_filepath], check=True)

# --- NEW AUTONOMOUS SCHEDULER LOGIC ---
def check_schedule():
    with open(os.path.join(BASE_DIR, "config.json"), "r") as f:
        config = json.load(f)
    
    current_time = datetime.now().strftime("%H:%M")
    for name, data in config["channels"].items():
        if current_time in data["schedule"]:
            return name, data["prompt"]
    return None, None

def main():
    print("--- 🤖 GEMINI-CORE AUTONOMOUS SCHEDULER STARTED ---")
    last_run_time = ""

    while True:
        current_time = datetime.now().strftime("%H:%M")
        
        # Prevent running multiple times in the same minute
        if current_time != last_run_time:
            target_channel, target_prompt = check_schedule()
            
            if target_channel:
                print(f"\n⏰ SCHEDULE MATCH: {current_time}")
                print(f"Target: {target_channel} | Prompt: {target_prompt}")
                print(f"Press ANY KEY within 15s to OVERRIDE, otherwise starting...")

                # Non-blocking wait for 15 seconds
                rlist, _, _ = select.select([sys.stdin], [], [], 15)
                
                if rlist:
                    sys.stdin.readline() # clear buffer
                    print("⌨️ Override detected!")
                    channel = input("📺 Enter Channel Name: ")
                    topic = input("📝 Enter Topic: ")
                else:
                    print("🤖 No override. Proceeding automatically...")
                    channel = target_channel
                    topic = target_prompt
                
                # Execute Pipeline
                result = get_ai_answer(channel, topic)
                save_and_run(result, channel)
                
                last_run_time = current_time
                print(f"\n✅ Cycle Complete. Sleeping until next slot...")
        
        time.sleep(30) # Check every 30 seconds

if __name__ == "__main__":
    main()