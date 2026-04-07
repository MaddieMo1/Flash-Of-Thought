try:
    import dashscope
    print(f"DashScope available")
except ImportError as e:
    print(f"DashScope NOT available: {e}")

try:
    import chromadb
    print(f"ChromaDB available: {chromadb.__version__}")
except ImportError as e:
    print(f"ChromaDB NOT available: {e}")

try:
    import oss2
    print(f"OSS2 available: {oss2.__version__}")
except ImportError as e:
    print(f"OSS2 NOT available: {e}")
