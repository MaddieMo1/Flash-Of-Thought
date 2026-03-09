from mcp.server.fastmcp import FastMCP
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service
from app.models.note import NoteStructure
import json

# Initialize FastMCP server
mcp = FastMCP("IdeaPills")

@mcp.tool()
async def add_idea(text: str) -> str:
    """
    Process a text idea, structure it, and save it to the knowledge base.
    Args:
        text: The content of the idea or thought.
    """
    try:
        # 1. Structure the note
        note_data = llm_service.structure_note(text)
        
        # 2. Save to Vector DB
        # Convert dict to NoteStructure to validate, then back to dict if needed, 
        # but rag_service takes dict.
        note_id = rag_service.add_note(note_data, raw_text=text, source_url="mcp_input")
        
        return f"Successfully added idea! ID: {note_id}\nTitle: {note_data.get('title')}\nSummary: {note_data.get('summary')}"
    except Exception as e:
        return f"Error adding idea: {str(e)}"

@mcp.tool()
async def search_ideas(query: str, limit: int = 5) -> str:
    """
    Search for ideas in the knowledge base using semantic search.
    Args:
        query: The search query.
        limit: Number of results to return (default 5).
    """
    try:
        results = rag_service.query_notes(query, limit)
        
        if not results:
            return "No matching ideas found."
            
        formatted_output = "Found the following ideas:\n\n"
        for res in results:
            meta = res.get('metadata', {})
            formatted_output += f"- **{meta.get('title', 'Untitled')}** (Score: {res.get('score', 0):.2f})\n"
            formatted_output += f"  Summary: {meta.get('summary', '')}\n"
            formatted_output += f"  Tags: {meta.get('tags', '')}\n\n"
            
        return formatted_output
    except Exception as e:
        return f"Error searching ideas: {str(e)}"

if __name__ == "__main__":
    mcp.run()
