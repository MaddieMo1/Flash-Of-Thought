import oss2
import os
import requests
from dotenv import load_dotenv

load_dotenv()

access_key_id = os.getenv("OSS_ACCESS_KEY_ID")
access_key_secret = os.getenv("OSS_ACCESS_KEY_SECRET")
bucket_name = os.getenv("OSS_BUCKET_AUDIO")
endpoint = os.getenv("OSS_ENDPOINT")

auth = oss2.Auth(access_key_id, access_key_secret)
bucket = oss2.Bucket(auth, endpoint, bucket_name)

key = "test_acl.txt"
bucket.put_object(key, "Public Content")

try:
    bucket.put_object_acl(key, oss2.OBJECT_ACL_PUBLIC_READ)
    print("Set Object ACL to public-read: Success")
    
    # Construct public URL
    # https://bucket.endpoint/key
    public_url = f"https://{bucket_name}.{endpoint.replace('https://', '')}/{key}"
    print(f"Public URL: {public_url}")
    
    resp = requests.get(public_url)
    print(f"Public Access Status: {resp.status_code}")
    
except Exception as e:
    print(f"Set Object ACL failed: {e}")
