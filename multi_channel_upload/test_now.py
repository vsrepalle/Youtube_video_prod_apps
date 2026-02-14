import os
import json
from create_video import generate_video # Import your existing logic

# Define the channels we want to test
test_channels = ["TrendWave_Now", "SpaceMind_AI"]

def run_test():
    for channel in test_channels:
        print(f"\n--- Testing Channel: {channel} ---")
        json_file = f"{channel}_data.json"
        
        # Check if JSON exists, if not create a dummy one for the test
        if not os.path.exists(json_file):
            print(f"⚠️ {json_file} not found. Creating dummy data for test...")
            dummy_data = [{
                "hook_text": f"Welcome to {channel}",
                "headline": "This is a 2026 AI Test",
                "details": "Testing immediate multi-channel upload logic for India peak hours.",
                "search_key": "AI Technology 2026 | Future Trends"
            }]
            with open(json_file, "w") as f:
                json.dump(dummy_data, f)
        
        # Trigger your actual generation and upload logic
        try:
            generate_video(json_file)
        except Exception as e:
            print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    run_test()