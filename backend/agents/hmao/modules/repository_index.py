from typing import List, Dict, Any
# ABSOLUTE IMPORT FIX
from lib.indexer import search_similar_code
import datetime

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
