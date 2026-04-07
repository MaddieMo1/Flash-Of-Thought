from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class NoteStructure(BaseModel):
    title: str
    summary: str
    core_ideas: List[str] = []
    key_features: List[str] = []
    possible_applications: List[str] = []
    tags: List[str] = []
    
    # Analysis results (optional)
    expanded_idea: Optional[Dict[str, Any]] = None
    roadmap: Optional[Dict[str, Any]] = None
    score: Optional[Dict[str, Any]] = None

class NoteCreate(BaseModel):
    raw_text: str
    source_url: Optional[str] = None

class NoteResponse(NoteStructure):
    id: str
    raw_text: Optional[str] = None
    source_url: Optional[str] = None
    created_at: Optional[str] = None
