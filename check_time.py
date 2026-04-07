import time
import requests
print(f"Local Time: {time.time()}")
print(f"Local Time String: {time.ctime()}")

# Check OSS server time by making a request
try:
    resp = requests.head("https://oss-cn-beijing.aliyuncs.com")
    print(f"OSS Server Date: {resp.headers.get('Date')}")
except:
    pass
