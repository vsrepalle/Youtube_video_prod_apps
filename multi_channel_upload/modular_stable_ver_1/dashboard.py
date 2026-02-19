import os
from collections import Counter
from datetime import datetime

def run_dashboard():
    print("\n" + "="*40)
    print("🚀 YOUTUBE AUTOMATION DASHBOARD")
    print("="*40)

    log_file = "upload_history.txt"
    
    # 1. AUTHENTICATION STATUS
    print("\n📡 CHANNEL AUTH STATUS:")
    channels_dir = "channels"
    if os.path.exists(channels_dir):
        for folder in os.listdir(channels_dir):
            token_exists = os.path.exists(os.path.join(channels_dir, folder, "token.pickle"))
            status = "✅ READY" if token_exists else "❌ NEEDS LOGIN"
            print(f" - {folder.ljust(20)} : {status}")
    else:
        print(" ! No channel folders found.")

    # 2. UPLOAD STATISTICS
    print("\n📊 UPLOAD STATISTICS:")
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Extract channel names from log lines
        channel_names = []
        for line in lines:
            if "CHANNEL: " in line:
                part = line.split("CHANNEL: ")[1].split(" |")[0]
                channel_names.append(part)
        
        stats = Counter(channel_names)
        total = sum(stats.values())
        
        for ch, count in stats.items():
            print(f" - {ch.ljust(20)} : {count} videos")
        print(f"----------------------------------------")
        print(f" TOTAL UPLOADS: {total}")
    else:
        print(" ! No upload history found yet.")

    # 3. RECENT ACTIVITY
    print("\n🕒 RECENT 5 UPLOADS:")
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines[-5:]:
            print(f" > {line.strip()}")
    else:
        print(" ! No recent activity.")

    print("\n" + "="*40)

if __name__ == "__main__":
    run_dashboard()