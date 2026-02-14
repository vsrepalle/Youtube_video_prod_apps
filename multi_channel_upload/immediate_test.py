import os
import json
from create_video import generate_video # Ensure this matches your file name

def run_immediate_test():
    with open("news_data.json", "r", encoding="utf-8") as f:
        all_news = json.load(f)

    for entry in all_news:
        channel = entry.get('channel_id')
        print(f"\n🚀 STARTING IMMEDIATE TEST: {channel}")
        
        # Create a temporary JSON for just this channel item
        temp_json = f"temp_{channel}.json"
        with open(temp_json, "w", encoding="utf-8") as f:
            json.dump([entry], f)
        
        try:
            # This triggers your provided logic: voice, effects, and upload prompt
            generate_video(temp_json)
            print(f"✅ Finished generating/uploading for {channel}")
        except Exception as e:
            print(f"❌ Failed for {channel}: {e}")
        finally:
            if os.path.exists(temp_json):
                os.remove(temp_json)

if __name__ == "__main__":
    run_immediate_test()