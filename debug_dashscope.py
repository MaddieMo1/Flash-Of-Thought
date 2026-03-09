
try:
    import dashscope
    # print(f"dashscope imported: {dashscope.__version__}")
    print(f"dashscope dir: {dir(dashscope)}")
    from dashscope.audio.asr import Transcription
    print("dashscope.audio.asr.Transcription imported")
    DASHSCOPE_AVAILABLE = True
except ImportError as e:
    print(f"ImportError: {e}")
    DASHSCOPE_AVAILABLE = False
except Exception as e:
    print(f"Exception: {e}")
    DASHSCOPE_AVAILABLE = False
    
print(f"DASHSCOPE_AVAILABLE: {DASHSCOPE_AVAILABLE}")
