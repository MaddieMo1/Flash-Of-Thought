import os
path = r"d:\软件\Trae IDE\FlashOfThought\audio\录音.mp3"
if os.path.exists(path):
    print(f"File exists: {path}")
    print(f"Size: {os.path.getsize(path)} bytes")
else:
    print(f"File not found: {path}")
