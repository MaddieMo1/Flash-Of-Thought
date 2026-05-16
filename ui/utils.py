import requests
import os

def normalize_api_base_url(raw_url):
    base_url = raw_url.rstrip("/")
    if not base_url.endswith("/api/v1"):
        base_url = f"{base_url}/api/v1"
    return base_url


API_BASE_URL = normalize_api_base_url(os.getenv("API_BASE_URL", "http://localhost:8000/api/v1"))
API_SESSION = requests.Session()
API_SESSION.trust_env = False

def parse_list_from_doc(document_text, key_name):
    """
    Extract comma-separated list from document text for a given key.
    Keys: "Core Ideas", "Key Features", "Applications"
    """
    if not document_text:
        return []
        
    start_marker = f"{key_name}: "
    if start_marker not in document_text:
        return []
        
    start_idx = document_text.find(start_marker) + len(start_marker)
    
    # Find the end of this section (start of next section)
    # Possible next sections
    markers = ["Title:", "Summary:", "Core Ideas:", "Key Features:", "Applications:", "Raw:"]
    end_idx = len(document_text)
    
    for marker in markers:
        # We look for \nMarker to ensure it's a header
        search_marker = f"\n{marker}"
        # Only search AFTER the start_idx
        idx = document_text.find(search_marker, start_idx)
        if idx != -1 and idx < end_idx:
            end_idx = idx
            
    content = document_text[start_idx:end_idx].strip()
    if not content:
        return []
        
    return [item.strip() for item in content.split(',') if item.strip()]

def save_analysis_result(note_id, current_note, analysis_type, result_data, access_token=None):
    """
    Helper to update note with new analysis data
    """
    try:
        # Construct the full note structure required for PUT
        meta = current_note.get("metadata", {})
        document_text = current_note.get("document", "")
        
        # Parse tags
        tags_raw = meta.get('tags', [])
        if isinstance(tags_raw, str):
            tags = [t.strip() for t in tags_raw.split(',') if t.strip()]
        else:
            tags = tags_raw

        # Recover structure from document text to avoid overwriting with empty lists
        core_ideas = parse_list_from_doc(document_text, "Core Ideas")
        key_features = parse_list_from_doc(document_text, "Key Features")
        possible_applications = parse_list_from_doc(document_text, "Applications")

        updated_note = {
            "title": meta.get('title', '无标题'),
            "summary": meta.get('summary', ''),
            "core_ideas": core_ideas, 
            "key_features": key_features,
            "possible_applications": possible_applications,
            "tags": tags,
            # Preserve existing analysis data
            "expanded_idea": meta.get('expanded_idea'),
            "roadmap": meta.get('roadmap'),
            "score": meta.get('score')
        }
        
        # Update with new data
        if analysis_type == 'expand':
            updated_note['expanded_idea'] = result_data
        elif analysis_type == 'roadmap':
            updated_note['roadmap'] = result_data
        elif analysis_type == 'score':
            updated_note['score'] = result_data
            
        headers = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        API_SESSION.put(f"{API_BASE_URL}/notes/{note_id}", json=updated_note, headers=headers, timeout=60)
    except Exception as e:
        print(f"Failed to auto-save analysis: {e}")
