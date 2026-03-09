import json
import time
import uuid
import os
from typing import List, Dict, Any, Optional
from app.core.config import get_settings
from app.services.llm_service import llm_service

try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("Warning: chromadb module not found. Using in-memory mock storage.")
    # Dummy classes
    class chromadb:
        pass
    class embedding_functions:
        class EmbeddingFunction:
            pass

settings = get_settings()

if CHROMADB_AVAILABLE:
    class QwenEmbeddingFunction(embedding_functions.EmbeddingFunction):
        def __call__(self, input: list[str]) -> list[list[float]]:
            return llm_service.get_embeddings(input)

class RagService:
    def __init__(self):
        if CHROMADB_AVAILABLE:
            # Initialize ChromaDB client
            # Ensure directory exists
            os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
            
            self.client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
            self.embedding_fn = QwenEmbeddingFunction()
            
            self.collection = self.client.get_or_create_collection(
                name="idea_pills",
                embedding_function=self.embedding_fn
            )
        else:
            self.mock_db = {}  # id -> {document, metadata}
            data_dir = os.path.dirname(settings.CHROMA_DB_PATH) or "./data"
            os.makedirs(data_dir, exist_ok=True)
            self.mock_db_path = os.path.join(data_dir, "mock_notes.json")
            self._load_mock_db()

    def _load_mock_db(self) -> None:
        if CHROMADB_AVAILABLE:
            return
        try:
            if os.path.exists(self.mock_db_path):
                with open(self.mock_db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self.mock_db = data
        except Exception as e:
            print(f"Warning: failed to load mock db: {e}")
            self.mock_db = {}

    def _persist_mock_db(self) -> None:
        if CHROMADB_AVAILABLE:
            return
        try:
            with open(self.mock_db_path, "w", encoding="utf-8") as f:
                json.dump(self.mock_db, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: failed to persist mock db: {e}")

    def add_note(self, note_data: Dict[str, Any], raw_text: str, source_url: str = ""):
        """
        Add a note to the vector database.
        note_data should come from LLM structure_note.
        """
        note_id = str(uuid.uuid4())
        
        # We index the summary + new fields + raw_text for better retrieval
        core_ideas = ", ".join(note_data.get('core_ideas', []))
        key_features = ", ".join(note_data.get('key_features', []))
        possible_applications = ", ".join(note_data.get('possible_applications', []))
        
        document_text = f"Title: {note_data.get('title', '')}\nSummary: {note_data.get('summary', '')}\nCore Ideas: {core_ideas}\nKey Features: {key_features}\nApplications: {possible_applications}\nRaw: {raw_text}"
        
        metadata = {
            "title": note_data.get('title', '无标题'),
            "summary": note_data.get('summary', ''),
            "tags": ",".join(note_data.get('tags', [])),
            "source_url": source_url,
            "created_at": str(int(time.time()))
        }
        
        # Serialize analysis results if present
        if note_data.get('expanded_idea'):
            metadata['expanded_idea'] = json.dumps(note_data['expanded_idea'], ensure_ascii=False)
        if note_data.get('roadmap'):
            metadata['roadmap'] = json.dumps(note_data['roadmap'], ensure_ascii=False)
        if note_data.get('score'):
            metadata['score'] = json.dumps(note_data['score'], ensure_ascii=False)
        
        if CHROMADB_AVAILABLE:
            self.collection.add(
                documents=[document_text],
                metadatas=[metadata],
                ids=[note_id]
            )
        else:
            self.mock_db[note_id] = {
                "document": document_text,
                "metadata": metadata
            }
            self._persist_mock_db()
            
        return note_id

    def query_notes(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Query notes by semantic similarity.
        """
        if CHROMADB_AVAILABLE:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=limit
            )
            
            # Format results
            formatted_results = []
            if results['ids']:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        "id": results['ids'][0][i],
                        "score": results['distances'][0][i] if results['distances'] else 0,
                        "metadata": results['metadatas'][0][i],
                        "document": results['documents'][0][i]
                    })
            return formatted_results
        else:
            # Mock search: return all notes (up to limit)
            # In a real mock we might check for substring match
            results = []
            for nid, data in self.mock_db.items():
                if query_text.lower() in data['document'].lower() or query_text.lower() in data['metadata']['title'].lower():
                     results.append({
                        "id": nid,
                        "score": 0.9,
                        "metadata": data['metadata'],
                        "document": data['document']
                     })
            return results[:limit]

    def get_all_notes(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get all notes from the collection, sorted by created_at desc.
        """
        if CHROMADB_AVAILABLE:
            # Fetch all (or large number) to sort by date in memory
            results = self.collection.get(
                include=['metadatas', 'documents']
            )
            
            formatted_results = []
            if results['ids']:
                for i in range(len(results['ids'])):
                    metadata = results['metadatas'][i]
                    # Safely get created_at, default to 0
                    created_at_val = metadata.get('created_at', 0)
                    try:
                        created_at = int(created_at_val)
                    except ValueError:
                        # Handle case where created_at is a string like '2025-03-07 14:06:09'
                        # Or just invalid
                        # Try to parse string format or fallback to 0
                        try:
                            # If it looks like YYYY-MM-DD HH:MM:SS
                            created_at = int(time.mktime(time.strptime(str(created_at_val), '%Y-%m-%d %H:%M:%S')))
                        except:
                            created_at = 0
                    
                    formatted_results.append({
                        "id": results['ids'][i],
                        "metadata": metadata,
                        "document": results['documents'][i],
                        "_created_at": created_at
                    })
        else:
            formatted_results = []
            for nid, data in self.mock_db.items():
                metadata = data['metadata']
                # Safely get created_at, default to 0
                created_at_val = metadata.get('created_at', 0)
                try:
                    created_at = int(created_at_val)
                except ValueError:
                    try:
                        created_at = int(time.mktime(time.strptime(str(created_at_val), '%Y-%m-%d %H:%M:%S')))
                    except:
                        created_at = 0
                formatted_results.append({
                    "id": nid,
                    "metadata": metadata,
                    "document": data['document'],
                    "_created_at": created_at
                })

        # Sort by created_at descending
        formatted_results.sort(key=lambda x: x['_created_at'], reverse=True)
        
        # Remove internal key and limit
        final_results = []
        # If limit is 0 or negative, return all
        target_results = formatted_results if limit <= 0 else formatted_results[:limit]
        
        for item in target_results:
            item.pop('_created_at')
            # Fix: Handle case where created_at is already formatted string
            ts_val = item['metadata'].get('created_at', 0)
            try:
                ts = int(ts_val)
                if ts > 0:
                    item['metadata']['created_at'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))
            except ValueError:
                # Assume it's already a string or formatted
                pass
            
            # Deserialize analysis results if present
            if 'expanded_idea' in item['metadata']:
                try:
                    item['metadata']['expanded_idea'] = json.loads(item['metadata']['expanded_idea'])
                except: pass
            
            if 'roadmap' in item['metadata']:
                try:
                    item['metadata']['roadmap'] = json.loads(item['metadata']['roadmap'])
                except: pass
                
            if 'score' in item['metadata']:
                try:
                    item['metadata']['score'] = json.loads(item['metadata']['score'])
                except: pass
            
            final_results.append(item)
            
        return final_results

    def delete_note(self, note_id: str):
        """
        Delete a note by ID.
        """
        if CHROMADB_AVAILABLE:
            self.collection.delete(ids=[note_id])
        else:
            if note_id in self.mock_db:
                del self.mock_db[note_id]
                self._persist_mock_db()
        return True

    def update_note(self, note_id: str, note_data: Dict[str, Any], raw_text: str = None):
        """
        Update a note. We delete and re-add it (or update in place).
        """
        
        # We need to reconstruct document text and metadata
        core_ideas = ", ".join(note_data.get('core_ideas', []))
        key_features = ", ".join(note_data.get('key_features', []))
        possible_applications = ", ".join(note_data.get('possible_applications', []))
        
        if CHROMADB_AVAILABLE:
            existing = self.collection.get(ids=[note_id], include=['documents', 'metadatas'])
            if not existing['ids']:
                 return False # Not found
                 
            original_doc = existing['documents'][0]
            original_meta = existing['metadatas'][0]
        else:
            if note_id not in self.mock_db:
                return False
            original_doc = self.mock_db[note_id]['document']
            original_meta = self.mock_db[note_id]['metadata']
        
        # Helper to get from payload or fallback to original (deserialized)
        def get_analysis_data(key):
            # Check if provided in payload
            if key in note_data and note_data[key]:
                 return json.dumps(note_data[key], ensure_ascii=False)
            
            # Check if exists in original metadata
            if key in original_meta:
                 return original_meta[key]
            return None

        exp = get_analysis_data('expanded_idea')
        road = get_analysis_data('roadmap')
        score = get_analysis_data('score')
        
        # Try to extract raw text from original doc if not provided
        # Format: ... \nRaw: {raw_text}
        final_raw_text = raw_text
        if final_raw_text is None:
             if "Raw: " in original_doc:
                 try:
                    final_raw_text = original_doc.split("Raw: ", 1)[1]
                 except IndexError:
                    final_raw_text = ""
             else:
                 final_raw_text = ""

        document_text = f"Title: {note_data.get('title', '')}\nSummary: {note_data.get('summary', '')}\nCore Ideas: {core_ideas}\nKey Features: {key_features}\nApplications: {possible_applications}\nRaw: {final_raw_text}"
        
        # Preserve original created_at
        created_at = original_meta.get('created_at', str(int(time.time())))
        
        metadata = {
            "title": note_data.get('title', '无标题'),
            "summary": note_data.get('summary', ''),
            "tags": ",".join(note_data.get('tags', [])),
            "source_url": original_meta.get('source_url', ''),
            "created_at": created_at,
            "updated_at": str(int(time.time()))
        }
        
        if exp: metadata['expanded_idea'] = exp
        if road: metadata['roadmap'] = road
        if score: metadata['score'] = score
        
        if CHROMADB_AVAILABLE:
            self.collection.update(
                ids=[note_id],
                documents=[document_text],
                metadatas=[metadata]
            )
        else:
            self.mock_db[note_id] = {
                "document": document_text,
                "metadata": metadata
            }
            self._persist_mock_db()
            
        return True

    def get_notes_in_time_range(self, start_ts: int, end_ts: int) -> List[Dict[str, Any]]:
        """
        Get notes created within a specific time range.
        """
        if CHROMADB_AVAILABLE:
            results = self.collection.get(
                include=['metadatas', 'documents']
            )
            
            ids = results['ids']
            metadatas = results['metadatas']
            documents = results['documents']
        else:
            ids = list(self.mock_db.keys())
            metadatas = [v['metadata'] for v in self.mock_db.values()]
            documents = [v['document'] for v in self.mock_db.values()]
        
        filtered_results = []
        if ids:
            for i in range(len(ids)):
                metadata = metadatas[i]
                # Fix: Handle non-int created_at
                created_at_val = metadata.get('created_at', 0)
                try:
                    created_at = int(created_at_val)
                except ValueError:
                    try:
                        created_at = int(time.mktime(time.strptime(str(created_at_val), '%Y-%m-%d %H:%M:%S')))
                    except:
                        created_at = 0
                
                if start_ts <= created_at <= end_ts:
                    formatted_note = {
                        "id": ids[i],
                        "metadata": metadata,
                        "document": documents[i]
                    }
                    # Add readable time
                    if created_at > 0:
                        formatted_note['metadata']['created_at_str'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(created_at))
                    
                    filtered_results.append(formatted_note)
        
        # Sort by created_at descending
        filtered_results.sort(key=lambda x: str(x['metadata'].get('created_at', '')), reverse=True)
        
        return filtered_results

rag_service = RagService()
