import requests
import os
import json
import time

API_URL = "http://127.0.0.1:8000/api/v1"
AUDIO_FILE = r"d:\软件\Trae IDE\FlashOfThought\audio\录音.mp3"

def test_upload():
    print(f"Testing Upload with {AUDIO_FILE}...")
    if not os.path.exists(AUDIO_FILE):
        print(f"Error: File not found: {AUDIO_FILE}")
        return None

    try:
        with open(AUDIO_FILE, "rb") as f:
            files = {"file": ("录音.mp3", f, "audio/mp3")}
            response = requests.post(f"{API_URL}/upload", files=files)
            
        if response.status_code == 200:
            data = response.json()
            print("Upload Success!")
            print(f"Raw Text: {data.get('raw_text')[:50]}...")
            return data
        else:
            print(f"Upload Failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Upload Error: {e}")
        return None

def test_process(raw_text):
    print("\nTesting Process...")
    try:
        response = requests.post(f"{API_URL}/process", json={"raw_text": raw_text})
        
        if response.status_code == 200:
            data = response.json()
            print("Process Success!")
            print(f"Title: {data.get('title')}")
            print(f"Summary: {data.get('summary')}")
            return data
        else:
            print(f"Process Failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Process Error: {e}")
        return None

def test_save(note_data, raw_text, source_url):
    print("\nTesting Save...")
    try:
        payload = {
            "note": note_data,
            "raw_text": raw_text,
            "source_url": source_url
        }
        response = requests.post(f"{API_URL}/save", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Save Success! ID: {data.get('id')}")
            return data.get('id')
        else:
            print(f"Save Failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Save Error: {e}")
        return None

def test_search(query):
    print(f"\nTesting Search with query: '{query}'...")
    try:
        response = requests.post(f"{API_URL}/search", json={"query": query, "limit": 3})
        
        if response.status_code == 200:
            results = response.json()
            print(f"Search Success! Found {len(results)} results.")
            for res in results:
                print(f"- {res['metadata']['title']} (Score: {res['score']:.4f})")
        else:
            print(f"Search Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Search Error: {e}")

if __name__ == "__main__":
    # Wait for server to be ready
    print("Waiting for server...")
    time.sleep(3)
    
    upload_result = test_upload()
    if upload_result:
        raw_text = upload_result['raw_text']
        file_url = upload_result['file_url']
        
        # If raw_text is empty, we can't proceed meaningfully, but let's try with dummy text if needed
        if not raw_text:
            print("Warning: ASR returned empty text. Using dummy text for testing process.")
            raw_text = "我今天有一个想法，就是做一个语音笔记应用，可以自动整理我的思路，并且支持搜索。"
        
        note_data = test_process(raw_text)
        
        if note_data:
            note_id = test_save(note_data, raw_text, file_url)
            
            if note_id:
                test_search("笔记")
