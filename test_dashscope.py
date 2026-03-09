import dashscope
from dashscope.audio.asr import Transcription
import os
import oss2
from dotenv import load_dotenv

load_dotenv()
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

# Generate fresh signed URL
access_key_id = os.getenv("OSS_ACCESS_KEY_ID")
access_key_secret = os.getenv("OSS_ACCESS_KEY_SECRET")
bucket_name = os.getenv("OSS_BUCKET_AUDIO")
endpoint = os.getenv("OSS_ENDPOINT")

auth = oss2.Auth(access_key_id, access_key_secret)
bucket = oss2.Bucket(auth, endpoint, bucket_name)

# Upload a small test file
test_key = "dashscope_test.mp3"
# Create a dummy mp3 file (just text content, might fail ASR but should start task)
# Or copy existing file
with open(r"d:\软件\Trae IDE\IdeaPills\audio\录音.mp3", "rb") as f:
    bucket.put_object(test_key, f)

import requests
# Try OSS signed URL
url = bucket.sign_url('GET', test_key, 3600)
print(f"Testing URL: {url}")


# Verify URL locally
try:
    print("Verifying URL locally (GET)...")
    if url.startswith("http"):
        resp = requests.get(url, stream=True)
        print(f"Local Access Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Local Access Failed: {resp.text}")
    else:
        print("Skipping local http verify for non-http url")
except Exception as e:
    print(f"Local Access Error: {e}")

try:
    task_response = Transcription.async_call(
        model="paraformer-v1", # Hardcode model name to be sure
        file_urls=[url],
        language_hints=['zh', 'en']
    )
    print(f"Task Response: {task_response}")
    
    if task_response.status_code == 200:
        print("Task Started Successfully!")
        transcription_response = Transcription.wait(task=task_response.output.task_id)
        print(f"Transcription Response: {transcription_response}")
    else:
        print(f"Task Start Failed: {task_response.code} - {task_response.message}")

except Exception as e:
    print(f"Exception: {e}")
