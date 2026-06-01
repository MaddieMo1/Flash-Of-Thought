from fastapi import APIRouter, UploadFile, File, HTTPException, Body
import re
from app.services.oss_service import oss_service
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service
from app.services.auth_service import get_current_user
from app.services.billing_service import billing_service
from app.models.note import NoteStructure, NoteResponse
from typing import List, Dict, Any
from fastapi import Depends

router = APIRouter()

CREDIT_COSTS = {
    "upload": 3,
    "process": 1,
    "analysis": 2,
    "chat": 1,
    "weekly_summary": 5,
}


@router.get("/billing/account", summary="Get quota account")
async def get_billing_account(current_user: Dict[str, Any] = Depends(get_current_user)):
    return billing_service.get_account(current_user["id"])


@router.get("/billing/plans", summary="List quota recharge plans")
async def list_billing_plans(current_user: Dict[str, Any] = Depends(get_current_user)):
    return {"plans": billing_service.list_plans()}


@router.post("/billing/payments/mock", summary="Create a mock paid recharge order")
async def create_mock_payment(plan_id: str = Body(..., embed=True), current_user: Dict[str, Any] = Depends(get_current_user)):
    return billing_service.create_mock_payment(current_user["id"], plan_id)

@router.post("/upload", summary="Upload audio and transcribe")
async def upload_audio(file: UploadFile = File(...), current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Upload audio file to OSS and transcribe it using ASR.
    """
    try:
        billing_service.ensure_credits(current_user["id"], CREDIT_COSTS["upload"])
        # Read file content
        content = await file.read()
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "mp3"
        
        # Upload to OSS
        file_key = oss_service.upload_file(content, file_extension)
        file_url = oss_service.get_file_url(file_key)
        
        # Transcribe
        transcription = llm_service.transcribe_audio(file_url)
        billing_service.spend_credits(current_user["id"], CREDIT_COSTS["upload"], "语音转写")
        
        return {
            "file_key": file_key,
            "file_url": file_url,
            "raw_text": transcription
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/notes/{note_id}", summary="Delete a note")
async def delete_note(note_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Delete a note by ID.
    """
    try:
        success = rag_service.delete_note(note_id, user_id=current_user["id"])
        if not success:
            raise HTTPException(status_code=404, detail="Note not found")
        return {"status": "deleted", "id": note_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/notes/{note_id}", summary="Update a note")
async def update_note_route(note_id: str, note: NoteStructure, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Update a note structure.
    """
    try:
        note_dict = note.model_dump()
        success = rag_service.update_note(note_id, note_dict, user_id=current_user["id"])
        if not success:
            raise HTTPException(status_code=404, detail="Note not found")
        return {"status": "updated", "id": note_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process", response_model=NoteStructure, summary="Structure raw text into a note")
async def process_text(raw_text: str = Body(..., embed=True), current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Process raw text using LLM to generate a structured note.
    """
    try:
        billing_service.ensure_credits(current_user["id"], CREDIT_COSTS["process"])
        structured_note = llm_service.structure_note(raw_text)
        billing_service.spend_credits(current_user["id"], CREDIT_COSTS["process"], "文本整理")
        return structured_note
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/save", summary="Save note to Vector DB")
async def save_note(
    note: NoteStructure,
    raw_text: str = Body(..., embed=True),
    source_url: str = Body("", embed=True),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Save the structured note and raw text to ChromaDB.
    """
    try:
        note_dict = note.model_dump()
        note_id = rag_service.add_note(note_dict, raw_text, source_url, user_id=current_user["id"])
        return {"id": note_id, "status": "saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", summary="Search notes")
async def search_notes(query: str = Body(..., embed=True), limit: int = 5, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Search for notes using semantic search.
    """
    try:
        results = rag_service.query_notes(query, limit, user_id=current_user["id"])
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notes", summary="List all notes")
async def list_notes(limit: int = 20, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    List recent notes from the database.
    """
    try:
        results = rag_service.get_all_notes(limit, user_id=current_user["id"])
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/expand", summary="Expand an idea")
async def expand_idea(raw_text: str = Body(..., embed=True), current_user: Dict[str, Any] = Depends(get_current_user)):
    try:
        billing_service.ensure_credits(current_user["id"], CREDIT_COSTS["analysis"])
        result = llm_service.expand_idea(raw_text)
        billing_service.spend_credits(current_user["id"], CREDIT_COSTS["analysis"], "AI 扩展想法")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/roadmap", summary="Generate roadmap")
async def generate_roadmap(raw_text: str = Body(..., embed=True), current_user: Dict[str, Any] = Depends(get_current_user)):
    try:
        billing_service.ensure_credits(current_user["id"], CREDIT_COSTS["analysis"])
        result = llm_service.generate_roadmap(raw_text)
        billing_service.spend_credits(current_user["id"], CREDIT_COSTS["analysis"], "AI 路线规划")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/score", summary="Score an idea")
async def score_idea(raw_text: str = Body(..., embed=True), current_user: Dict[str, Any] = Depends(get_current_user)):
    try:
        billing_service.ensure_credits(current_user["id"], CREDIT_COSTS["analysis"])
        result = llm_service.score_idea(raw_text)
        billing_service.spend_credits(current_user["id"], CREDIT_COSTS["analysis"], "AI 灵感评分")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat", summary="Chat with knowledge base")
async def chat_with_kb(query: str = Body(..., embed=True), current_user: Dict[str, Any] = Depends(get_current_user)):
    try:
        billing_service.ensure_credits(current_user["id"], CREDIT_COSTS["chat"])
        # 1. Search relevant notes
        context_notes = rag_service.query_notes(query, limit=5, user_id=current_user["id"])
        # 2. Generate answer
        answer = llm_service.chat_with_notes(query, context_notes)
        billing_service.spend_credits(current_user["id"], CREDIT_COSTS["chat"], "知识库问答")
        return {"answer": answer, "context": context_notes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/graph", summary="Get knowledge graph data")
async def get_graph_data(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get nodes and edges for knowledge graph visualization.

    Knowledge Galaxy structure:
    - Level 1: Core Idea (single, center star)
    - Level 2: Tags (dynamic clusters)
    - Level 3: Knowledge items (notes)
    """
    try:
        notes = rag_service.get_all_notes(limit=0, user_id=current_user["id"])

        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        existing_node_ids: set[str] = set()

        def add_node(node_id: str, label: str, group: str, size: int, color: str, title: str = "", **kwargs):
            if node_id in existing_node_ids:
                return
            node_data: Dict[str, Any] = {
                "id": node_id,
                "label": label,
                "group": group,
                "size": size,
                "color": color,
                "title": title,
            }
            node_data.update(kwargs)
            nodes.append(node_data)
            existing_node_ids.add(node_id)

        def split_tags(tags_value: Any) -> List[str]:
            if tags_value is None:
                return []
            if isinstance(tags_value, list):
                return [str(t).strip() for t in tags_value if str(t).strip()]
            text = str(tags_value)
            parts = re.split(r"[,，、\s]+", text)
            return [p.strip() for p in parts if p.strip()]

        core_id = "core_idea"
        add_node(
            core_id,
            "核心 Idea",
            "level1",
            40,
            "#FF6A3D",
            title="知识星系的中心恒星",
            full_title="核心 Idea",
            summary="知识星系中心：聚合所有灵感",
            tags=[],
            category="Core"
        )

        # Pre-defined colors for tags to cycle through
        tag_colors = [
            "#00F0FF", "#FF0055", "#00FF94", "#BD00FF", "#FFD700", 
            "#FF4B4B", "#1E90FF", "#ADFF2F", "#FF1493", "#00CED1"
        ]
        tag_color_map = {}
        tag_counter = 0

        # Process notes
        for note in notes:
            note_id = str(note.get("id", ""))
            meta = note.get("metadata", {}) or {}
            title = str(meta.get("title", "无标题"))
            summary = str(meta.get("summary", ""))
            tags_list = split_tags(meta.get("tags", ""))
            
            # Shorten title for display
            short_title = title
            if len(short_title) > 14:
                short_title = short_title[:14] + "…"

            # Add Note Node (Level 2)
            add_node(
                note_id,
                short_title,
                "level2",
                20,
                "#A0E0FF", # Default note color
                title=summary,
                full_title=title,
                summary=summary,
                tags=tags_list,
                category="Note",
                created_at=meta.get("created_at", ""),
                source_url=meta.get("source_url", ""),
            )
            
            # Connect Core -> Note
            edges.append({"source": core_id, "target": note_id})

            if tags_list:
                # Connect Note to each Tag
                for tag in tags_list:
                    tag_id = f"tag_{tag}"
                    
                    # Create Tag Node if not exists (Level 3)
                    if tag_id not in existing_node_ids:
                        # Assign color
                        if tag not in tag_color_map:
                            tag_color_map[tag] = tag_colors[tag_counter % len(tag_colors)]
                            tag_counter += 1
                        
                        add_node(
                            tag_id,
                            tag,
                            "level3",
                            15,
                            tag_color_map[tag],
                            title=f"标签：{tag}",
                            category="Tag"
                        )
                    
                    # Connect Note -> Tag
                    edges.append({"source": note_id, "target": tag_id})

        return {"nodes": nodes, "edges": edges}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/weekly_summary", summary="Generate weekly summary")
async def generate_weekly_summary(days: int = Body(7, embed=True), current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Generate a summary of notes from the last N days.
    """
    try:
        billing_service.ensure_credits(current_user["id"], CREDIT_COSTS["weekly_summary"])
        import time
        end_ts = int(time.time())
        start_ts = end_ts - (days * 24 * 60 * 60)
        
        # 1. Get notes
        notes = rag_service.get_notes_in_time_range(start_ts, end_ts, user_id=current_user["id"])
        
        # 2. Generate summary
        summary_data = llm_service.generate_weekly_summary(notes)
        billing_service.spend_credits(current_user["id"], CREDIT_COSTS["weekly_summary"], "AI 周报")
        
        return {
            "start_date": time.strftime('%Y-%m-%d', time.localtime(start_ts)),
            "end_date": time.strftime('%Y-%m-%d', time.localtime(end_ts)),
            "data": summary_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
