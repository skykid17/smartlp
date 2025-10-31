# Migration Guide: ChromaDB to MongoDB Vector Store with Hybrid Search

This document explains the changes made to migrate the RAG system from ChromaDB to MongoDB Atlas Vector Search with hybrid search capabilities.

## Overview

The SmartLP RAG system has been refactored to use MongoDB as the vector store backend instead of ChromaDB. This change provides:

- **Unified data storage**: All data (application data + vector embeddings) in one database
- **Better scalability**: MongoDB Atlas provides enterprise-grade scalability
- **Hybrid search capabilities**: Combines vector search and text search using Reciprocal Rank Fusion (RRF)
- **Improved retrieval accuracy**: Hybrid search provides better results than vector-only search
- **Simplified deployment**: No need to manage separate ChromaDB instances

## What Changed

### 1. Dependencies
- **Removed**: `langchain-chroma`, `chromadb`
- **Added**: `langchain-mongodb==0.7.2`

### 2. Configuration
New environment variables in `.env`:
```bash
MONGO_RAG_DB=rag                    # Database for RAG vectors (default: rag)
MONGO_RAG_COLLECTION=rag            # Collection name (default: rag)
```

### 3. Code Structure
- **New file**: `rag_mongo.py` - MongoDB-based RAG implementation
- **Updated**: `rag_func.py` - Now a wrapper around `rag_mongo.py` for backward compatibility
- **Updated**: `setup_rag.py` - Uses MongoDB implementation
- **Updated**: `src/config/settings.py` - Added RAG database configuration

### 4. Data Model Changes

#### ChromaDB (Old)
- Multiple collections: `splunk_addons`, `elastic_packages`, etc.
- Each collection stored independently
- File metadata in JSON mapping files

#### MongoDB (New)
- Single collection: `rag` (configurable)
- Documents distinguished by `source` field
- Document structure:
```json
{
  "_id": "source#file_path#chunk_index",
  "page_content": "Document text content",
  "embedding": [0.1, 0.2, ...],  // 384-dimensional vector
  "source": "splunk_addons",     // Source identifier
  "metadata": {
    "relative_path": "path/to/file.yaml",
    "file_hash": "sha256_hash",
    "modification_time": "2024-01-01T00:00:00",
    "file_size": 1024,
    "file_type": "yaml",
    ...
  }
}
```

## Migration Steps for Existing Deployments

### 1. Backup Existing Data (if needed)
If you have important ChromaDB data:
```bash
# Backup ChromaDB directory
tar -czf chroma_backup_$(date +%Y%m%d).tar.gz ./rag/chroma/
```

### 2. Update Code
```bash
git checkout mongo-vector-store
pip install -r requirements.txt
```

### 3. Update Environment Variables
Add to `.env`:
```bash
MONGO_RAG_DB=rag
MONGO_RAG_COLLECTION=rag
```

### 4. Setup MongoDB Indexes
```bash
python mongo_setup_indexes.py
```

Follow the instructions to create both:
1. **Vector search index** (`vector_index`) - for semantic similarity search
2. **Text search index** (`text_index`) - for keyword-based search

Both indexes are required for hybrid search functionality.

### 5. Re-ingest Documents
Since the data models are different, you need to re-ingest all documents:

```bash
# Full re-ingestion
python setup_rag.py --siem both

# Or selectively:
python setup_rag.py --siem elastic
python setup_rag.py --siem splunk
```

### 6. Test the Migration
```bash
python test_rag_mongo.py
```

### 7. Clean Up (Optional)
Once verified working, remove old ChromaDB data:
```bash
rm -rf ./rag/chroma/
```

## API Changes

### Collection/Source Naming
- **Old**: `create_embeddings("./path", "splunk_addons")`
- **New**: `create_embeddings("./path", "splunk_addons")` (same)

The `collection_name` parameter is now called `source` internally but the API remains compatible.

### Querying
- **Old**: `query_rag("splunk_addons", "my query")`
- **New (vector-only)**: `query_rag("splunk_addons", "my query")` (same)
- **New (hybrid search)**: `query_rag_hybrid("splunk_addons", "my query")`

The function signature is backward compatible. Use `query_rag_hybrid()` for better results with combined vector and text search.

### Filtering
New capability - filter by source and additional metadata:
```python
# Vector-only search with filtering
query_rag(
    source="splunk_addons",
    query="search query",
    filter_metadata={"metadata.file_type": "yaml"}
)

# Hybrid search with filtering and custom weights
query_rag_hybrid(
    source="splunk_addons",
    query="search query",
    filter_metadata={"metadata.file_type": "yaml"},
    vector_weight=1.0,  # Weight for semantic similarity
    text_weight=1.5     # Weight for keyword matching
)
```

## MongoDB Requirements

### For Production (Atlas)
- MongoDB Atlas M10+ cluster (M0 free tier does NOT support vector search or Atlas Search)
- **Two indexes required**:
  1. **Vector search index** (`vector_index`) - for semantic similarity
  2. **Text search index** (`text_index`) - for keyword matching
- Recommended regions: US East, EU West (lower latency)

### For Development (Local)
- MongoDB 6.0+ with Atlas Search installed
- Local Atlas deployment via `atlas deployments setup` supports both vector and text search
- Or use MongoDB Atlas free/shared tier for testing (M10+ required for hybrid search)
- Or mock/skip hybrid search for development and use vector-only search

### Hybrid Search Requirements
- Both vector and text search indexes must be created in MongoDB Atlas
- Hybrid search uses Reciprocal Rank Fusion (RRF) to combine results
- Text search uses Lucene's BM25 algorithm for keyword matching
- Vector search uses cosine similarity for semantic matching

## Performance Considerations

### Vector Search Performance
- Requires MongoDB Atlas M10+ cluster
- Create the vector search index before ingestion
- Index creation can take a few minutes for large collections

### Ingestion Performance
- Similar to ChromaDB
- Batch size controlled by `max_batch_size` parameter
- MongoDB handles concurrent writes better than ChromaDB

### Query Performance
- Vector search: Similar to ChromaDB (cosine similarity)
- Can combine with metadata filters for better precision
- Benefits from MongoDB's query optimization

## Troubleshooting

### "No module named 'langchain_mongodb'"
```bash
pip install langchain-mongodb==0.7.2
```

### "Collection not found" or "Database not found"
Check your `.env` configuration:
```bash
MONGO_URL=mongodb://localhost:27017/
MONGO_RAG_DB=rag
MONGO_RAG_COLLECTION=rag
```

### "Vector search not supported"
- Ensure you're using MongoDB Atlas M10+ (not M0 free tier)
- Verify vector search index is created via Atlas UI
- Check index name matches: `vector_index`

### Slow queries
- Verify vector search index exists and is active
- Check index configuration (384 dimensions, cosine similarity)
- Consider upgrading MongoDB Atlas cluster tier

### Import errors in existing code
If you have code importing from old modules:
```python
# Old (still works via wrapper)
from rag_func import create_embeddings, query_rag

# New (recommended)
from rag_mongo import create_embeddings, query_rag
```

## Rollback Plan

If you need to rollback to ChromaDB:

1. Checkout previous commit:
```bash
git checkout <previous-commit-hash>
```

2. Reinstall dependencies:
```bash
pip install -r requirements.txt
```

3. Restore ChromaDB backup (if created):
```bash
tar -xzf chroma_backup_YYYYMMDD.tar.gz
```

4. Verify old system works:
```bash
python setup_rag.py --skip-repos --skip-fields
```

## Support

For issues or questions:
1. Check logs: `./rag/rag_setup.log`
2. Run diagnostics: `python test_rag_mongo.py`
3. Review MongoDB connection: `python mongo_setup_indexes.py`
4. Open GitHub issue with logs and error messages

## Future Enhancements

Planned improvements:
- ✅ **Hybrid search (vector + text) with reciprocal rank fusion (RRF)** - IMPLEMENTED
- Adaptive weight tuning based on query type
- Multi-language embedding support
- Real-time incremental updates
- Better metadata filtering and faceting
- Query result caching
- Query performance analytics
