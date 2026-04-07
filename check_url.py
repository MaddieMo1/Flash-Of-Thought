import requests
url = "https://flashnote-audio.oss-cn-beijing.aliyuncs.com/1772600046_f9400391.mp3?OSSAccessKeyId=LTAI5tG26BGkpX63PRqK93rE&Expires=1772636046&Signature=LlMrXiq%2BmE8hXu8uJ9wkE0OFuJM%3D"
print(f"Checking URL: {url}")
try:
    resp = requests.head(url)
    print(f"Status Code: {resp.status_code}")
    print(f"Headers: {resp.headers}")
except Exception as e:
    print(f"Error: {e}")
