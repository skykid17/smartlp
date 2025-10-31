# Migration Guide: ChromaDB to MongoDB Vector Store

This document explains the changes made to migrate the RAG system from ChromaDB to MongoDB Atlas Vector Search.

## Overview

The SmartLP RAG system has been refactored to use MongoDB as the vector store backend instead of ChromaDB. This change provides:

- **Unified data storage**: All data (application data + vector embeddings) in one database
- **Better scalability**: MongoDB Atlas provides enterprise-grade scalability
- **Hybrid search capabilities**: Combines vector search (semantic) with full-text search (keyword matching) using Reciprocal Rank Fusion (RRF)
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

Follow the instructions to create the vector search index via MongoDB Atlas UI.

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
- **New**: `query_rag("splunk_addons", "my query")` (same)

The function signature is backward compatible.

### Filtering
New capability - filter by source and additional metadata:
```python
query_rag(
    source="splunk_addons",
    query="search query",
    filter_metadata={"metadata.file_type": "yaml"}
)
```

## MongoDB Requirements

### For Production (Atlas)
- MongoDB Atlas M10+ cluster (M0 free tier does NOT support vector search)
- Vector search index created via Atlas UI
- Recommended regions: US East, EU West (lower latency)

### For Development (Local)
- MongoDB 6.0+ with Atlas Search
- Or use MongoDB Atlas free/shared tier for testing (without vector search)
- Or mock/skip vector search for development

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

## Hybrid Search

The RAG system now uses **MongoDB Atlas Hybrid Search** via `MongoDBAtlasHybridSearchRetriever`:

### How It Works
- **Vector Search**: Semantic similarity using embeddings (finds conceptually similar content)
- **Full-Text Search**: Keyword matching using Atlas Search (finds exact matches)
- **RRF Ranking**: Results from both searches are combined using Reciprocal Rank Fusion algorithm

### Index Requirements
Two Atlas Search indexes are required:

**1. Vector Search Index (`vector_index`)**
```json
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 384,
      "similarity": "cosine"
    },
    {
      "type": "filter",
      "path": "source"
    }
  ]
}
```

**2. Full-Text Search Index (`fulltext_index`)**
```json
{
  "mappings": {
    "dynamic": false,
    "fields": {
      "page_content": {
        "type": "string"
      },
      "source": {
        "type": "string"
      }
    }
  }
}
```

### Tuning Parameters
You can adjust the balance between vector and full-text search:
- `vector_penalty`: Lower = more weight on semantic similarity (default: 60.0)
- `fulltext_penalty`: Lower = more weight on keyword matching (default: 60.0)
- `vector_weight`: Multiplier for vector scores (default: 1.0)
- `fulltext_weight`: Multiplier for full-text scores (default: 1.0)

## Future Enhancements

Planned improvements:
- Multi-language embedding support
- Real-time incremental updates
- Better metadata filtering and faceting
- Query result caching
- Tunable hybrid search parameters via API
