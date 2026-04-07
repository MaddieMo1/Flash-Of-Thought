import oss2
import os
from dotenv import load_dotenv

load_dotenv()

access_key_id = os.getenv("OSS_ACCESS_KEY_ID")
access_key_secret = os.getenv("OSS_ACCESS_KEY_SECRET")
bucket_name = os.getenv("OSS_BUCKET_AUDIO")
endpoint = os.getenv("OSS_ENDPOINT")

print(f"Connecting to OSS... Endpoint: {endpoint}, Bucket: {bucket_name}")

try:
    auth = oss2.Auth(access_key_id, access_key_secret)
    bucket = oss2.Bucket(auth, endpoint, bucket_name)
    
    # Try to create bucket
    try:
        bucket.create_bucket()
        print(f"Bucket '{bucket_name}' created successfully (or already exists).")
    except oss2.exceptions.OssError as e:
        print(f"Bucket creation info: {e}")

    # Set ACL to public-read
    bucket.put_bucket_acl(oss2.BUCKET_ACL_PUBLIC_READ)
    print("Bucket ACL set to public-read.")
    
except oss2.exceptions.OssError as e:
    print(f"Error creating bucket: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
