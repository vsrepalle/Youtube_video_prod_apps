import schedule
import time
import os
from create_video import generate_video

# Peak timings for India (IST)
SCHEDULES = {
    "TrendWave_Now": "18:00",    # 6 PM
    "SpaceMind_AI": "19:00",     # 7 PM
    "ExamPulse24_7": "20:00",    # 8 PM
    "WonderFacts24_7": "21:00"   # 9 PM
}

def run_pipeline(channel_name):
    print(f"--- Processing {channel_name} ---")
    # You would pass specific channel credentials to stage3_upload here
    generate_video("news_data.json") 

def test_immediately():
    print("🚀 Running Immediate Test for all 4 channels...")
    for channel in SCHEDULES.keys():
        run_pipeline(channel)

if __name__ == "__main__":
    choice = input("Run (T)est now or (S)chedule for peak hours? ").lower()
    
    if choice == 't':
        test_immediately()
    else:
        for channel, peak_time in SCHEDULES.items():
            schedule.every().day.at(peak_time).do(run_pipeline, channel)
        
        print("🤖 Scheduler Active. Waiting for peak hours...")
        while True:
            schedule.run_pending()
            time.sleep(60)