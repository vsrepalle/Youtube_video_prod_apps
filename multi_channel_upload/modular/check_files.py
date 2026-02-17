import os

folder = os.path.dirname(os.path.abspath(__file__))
print(f"Checking folder: {folder}")
print("Files found:", os.listdir(folder))

target = "client_secret.json"
if target in os.listdir(folder):
    print(f"✅ SUCCESS: {target} found!")
else:
    print(f"❌ ERROR: {target} NOT found in this folder.")