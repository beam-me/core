import json
import os
from typing import List, Dict, Any, Optional

class KnowledgeBase:
    """
    A simple JSON-backed knowledge base tool.
    Allows agents to load and search structured data.
    """
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        if not os.path.exists(self.file_path):
            print(f"Knowledge Base file not found: {self.file_path}")
            return {}
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading Knowledge Base: {e}")
            return {}

    def search(self, category: str, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for items in a specific category (e.g., 'motors').
        If query is provided, filters by text match in values.
        """
        items = self.data.get(category, [])
        if not query:
            return items

        query = query.lower()
        results = []
        for item in items:
            # Convert all values to string and check for query
            values_str = " ".join([str(v).lower() for v in item.values()])
            if query in values_str:
                results.append(item)
        
        return results

    def get_categories(self) -> List[str]:
        return list(self.data.keys())
