import oss2
import os
import requests
from dotenv import load_dotenv

load_dotenv()

access_key_id = os.getenv("OSS_ACCESS_KEY_ID")
access_key_secret = os.getenv("OSS_ACCESS_KEY_SECRET")
bucket_name = os.getenv("OSS_BUCKET_AUDIO")
endpoint = os.getenv("OSS_ENDPOINT")

print(f"Endpoint: {endpoint}")
print(f"Bucket: {bucket_name}")

auth = oss2.Auth(access_key_id, access_key_secret)
bucket = oss2.Bucket(auth, endpoint, bucket_name)

# Upload a test file
test_key = "test_url.txt"
bucket.put_object(test_key, "Hello OSS")

# Generate signed URL
url = bucket.sign_url('GET', test_key, 60)
print(f"Generated URL: {url}")

# Test access
resp = requests.get(url)
print(f"Access Status: {resp.status_code}")
print(f"Content: {resp.text}")
