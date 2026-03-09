import requests
url = "https://dashscope-result-bj.oss-cn-beijing.aliyuncs.com/paraformer-v2/20260304/13%3A01/cc334cd0-aed4-4b88-af43-0d2949b64b65-1.json?Expires=1772686913&OSSAccessKeyId=LTAI5tQZd8AEcZX6KZV4G8qL&Signature=OEVIz2RzgiqWYaaNpIeS%2FPH%2BsUE%3D"
resp = requests.get(url)
with open("result.json", "w", encoding="utf-8") as f:
    f.write(resp.text)
print("Downloaded result.json")
