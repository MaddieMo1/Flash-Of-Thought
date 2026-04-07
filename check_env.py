try:
    import fastapi
    print("FastAPI: OK")
except ImportError:
    print("FastAPI: Missing")

try:
    import uvicorn
    print("Uvicorn: OK")
except ImportError:
    print("Uvicorn: Missing")

try:
    import streamlit
    print("Streamlit: OK")
except ImportError:
    print("Streamlit: Missing")

try:
    import chromadb
    print("ChromaDB: OK")
except ImportError:
    print("ChromaDB: Missing")
    
try:
    import dashscope
    print("DashScope: OK")
except ImportError:
    print("DashScope: Missing")
