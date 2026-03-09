from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os
from app.api.routes import router as api_router

# Load environment variables
load_dotenv()

app = FastAPI(
    title="IdeaPills API",
    description="Backend for IdeaPills - Voice Note Assistant",
    version="0.1.0"
)

# Mount static files for local storage fallback
os.makedirs("static/uploads", exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory="static/uploads"), name="static")

# Include API Router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "Welcome to IdeaPills API",
        "status": "running",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
