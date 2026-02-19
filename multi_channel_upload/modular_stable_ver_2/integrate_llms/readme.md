Below is a comprehensive README.md file tailored for your project. This document explains how the AI integration, scheduling, and logging all work together, as well as clear instructions for running the system.

🤖 TrendWave Auto-Content Engine
TrendWave Auto-Content Engine is a fully autonomous pipeline designed to generate, render, and log high-quality video content for YouTube across four distinct niches: Cricket/Bollywood, Space Science, Education, and Gadgets/Tech.

Using the Groq AI (Llama-3) and MoviePy, the system fetches the latest viral trends and turns them into ready-to-upload MP4 videos without manual intervention.

🛠 Project Architecture
The system operates in a three-stage cycle:

The Scheduler (integrate_grok.py): Monitors the clock and matches current time with the config.json schedule.

The Brain (Groq API): Generates structured JSON data based on channel-specific prompts.

The Muscle (controller.py): Handles parallel rendering using a Multiprocessing Pool to prevent RAM crashes while managing video assets.

📁 File Structure
config.json: The heart of the automation. Defines channel names, AI prompts, and 3-slot daily schedules.

integrate_grok.py: The background service that manages the timing and internet resilience.

controller.py: The rendering engine that processes videos in parallel (capped at 2 for memory safety).

TrendWave_Logs.xlsx: An automatically generated Excel sheet tracking every run with clickable video links.

.env: Stores your sensitive API keys (GROQ_API_KEY).

🚀 How to Run Everything
Step 1: Environment Setup
Ensure you have Python 3.10+ installed and the required libraries:

Bash
pip install openai openpyxl moviepy python-dotenv
Step 2: Configuration
Update your config.json with your desired timings. The script checks these every 30 seconds.

JSON
{
  "channels": {
    "ExamPulse24_7": { "schedule": ["08:00", "14:00", "20:00"], ... },
    "TrendWave Now": { "schedule": ["09:00", "15:00", "21:00"], ... }
  }
}
Step 3: Launching the Engine
Run the main scheduler script:

Bash
python integrate_grok.py
Autonomous Mode: If a slot matches, it waits 15 seconds for an override, then proceeds automatically.

Internet Check: If your Wi-Fi is down, it will pause and retry every 60 seconds until the connection is restored.

📅 Scheduling for 24/7 Operation (Windows)
To ensure the script runs even if you restart your computer, follow these steps to add it to Windows Task Scheduler:

Open Task Scheduler and click Create Basic Task.

Trigger: Select "When I log on".

Action: Select "Start a Program".

Program/script: pythonw.exe (using pythonw prevents a black console window from staying open).

Add arguments: C:\path\to\your\project\integrate_grok.py

Start in: C:\path\to\your\project\ (Crucial for relative file paths!)

Conditions: Uncheck "Start the task only if the computer is on AC power" if using a laptop.

📊 Monitoring Logs
You don't need to check the console. Open TrendWave_Logs.xlsx to see:

Status: "Success" or specific Error messages.

Video Link: Click the blue underlined "Open Video" link to view the rendered MP4 instantly.

⚠️ Safety Guardrails
RAM Management: The controller.py uses multiprocessing.Pool(processes=2) to ensure your system doesn't freeze during heavy rendering.

Error Handling: Every failure is caught and logged to Excel so you can debug "Missed" slots later.