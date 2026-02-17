from typing import List, Dict, Any, Optional
# ABSOLUTE IMPORT FIX
from lib.indexer import search_similar_code
import datetime

# FIX: Import index_code as well
from lib.indexer import index_code

class RepositoryIndexModule:
    """
    Stateless module for looking up existing code artifacts.
    Attached to the Global Orchestrator.
    """

    def lookup(self, query: str, threshold: float = 0.85, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Search for existing code that matches the query.
        Returns strict artifact metadata.
        """
        results = search_similar_code(query, threshold=threshold, limit=limit)
        
        structured_results = []
        for match in results:
            structured_results.append({
                "artifact_id": match.get("run_id"),
                "problem_description": match.get("problem_description"),
                "file_path": match.get("file_path"),
                "similarity_score": match.get("similarity"),
                "metadata": match.get("metadata", {}), # Contains commit_sha, etc.
                "retrieved_at": datetime.datetime.now().isoformat()
            })
            
        return structured_results

    def index_run(self, run_id: str, problem: str, code_url: Optional[str] = None, metadata: Dict[str, Any] = None) -> bool:
        """
        Saves a completed run to the index for future retrieval.
        """
        if not problem:
            return False
            
        # If we have a code_url (e.g. GitHub link), use that as file_path or content reference
        file_path = code_url if code_url else f"runs/{run_id}"
        
        # We store minimal code content here since we rely on the problem description for matching
        # In a real system, we might fetch the README or key files.
        code_stub = f"Generated solution for: {problem}. See metadata for details."
        
        result = index_code(
            run_id=run_id,
            problem=problem,
            file_path=file_path,
            code=code_stub,
            metadata=metadata or {}
        )
        
        # index_code returns a Supabase response object or dict with error
        if isinstance(result, dict) and "error" in result:
            print(f"Indexing failed: {result['error']}")
            return False
            
        return True
