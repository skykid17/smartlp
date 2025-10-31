"""
MongoDB-based RAG implementation - wrapper for backward compatibility.
All RAG functionality has been migrated to use MongoDB with hybrid search.
This module provides backward compatibility for existing code.
"""

import sys
import os

# Import from the new MongoDB implementation
sys.path.insert(0, os.path.dirname(__file__))
from rag_mongo import (
    create_embeddings,
    update_embeddings,
    delete_collection,
    list_collection_files,
    list_sources as list_collections,
    delete_file_from_collection,
    query_rag,
    TOP_K
)

# Export for backward compatibility
__all__ = [
    'create_embeddings',
    'update_embeddings', 
    'delete_collection',
    'list_collection_files',
    'list_collections',
    'delete_file_from_collection',
    'query_rag',
    'TOP_K'
]