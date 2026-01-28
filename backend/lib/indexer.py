from typing import List, Dict, Any, Optional
from .supabase_client import supabase
from .embeddings import generate_embedding

def index_code(run_id: str, problem: str, file_path: str, code: str, metadata: Dict[str, Any] = None):
    """
    Generates an embedding for the problem and saves it to Supabase.
    """
    # Embed ONLY the problem description for better matching recall.
    # We want to find "similar problems", regardless of the implementation details.
    text_to_embed = problem
    
    vector = generate_embedding(text_to_embed)
    if not vector:
        return {"error": "Failed to generate embedding"}

    data = {
        "run_id": run_id,
        "problem_description": problem,
        "file_path": file_path,
        "code_content": code,
        "metadata": metadata or {},
        "embedding": vector
    }

    try:
        response = supabase.table("code_artifacts").insert(data).execute()
        return response
    except Exception as e:
        print(f"Error indexing code: {e}")
        return {"error": str(e)}

def search_similar_code(problem: str, threshold: float = 0.85, limit: int = 3):
    """
    Searches for existing code artifacts that match the problem description.
    """
    vector = generate_embedding(problem)
    if not vector:
        return []

    try:
        # Call the RPC function defined in db_schema.sql
        response = supabase.rpc(
            "match_code_artifacts",
            {
                "query_embedding": vector,
                "match_threshold": threshold,
                "match_count": limit
            }
        ).execute()
        
        return response.data
    except Exception as e:
        print(f"Error searching code: {e}")
        return []
