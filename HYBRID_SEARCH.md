# MongoDB Atlas Hybrid Search Implementation

## Overview

The SmartLP RAG system uses **MongoDB Atlas Hybrid Search** via the `MongoDBAtlasHybridSearchRetriever` from LangChain's MongoDB integration. This provides superior search results by combining two complementary search methods.

## How Hybrid Search Works

### Two Search Methods

1. **Vector Search (Semantic)**
   - Uses embedding vectors to find conceptually similar content
   - Good for: Understanding intent, synonyms, related concepts
   - Example: Searching "error messages" might find content about "exceptions" or "failures"

2. **Full-Text Search (Keyword)**
   - Uses traditional text indexing to find exact matches
   - Good for: Specific terms, technical names, codes
   - Example: Searching "ERROR-404" finds exact occurrences

### Reciprocal Rank Fusion (RRF)

Results from both searches are combined using the RRF algorithm:
- Each method ranks documents independently
- Scores are calculated as: `score = weight / (rank + penalty)`
- Final results are sorted by combined scores
- This ensures both semantic relevance and keyword matches are considered

## Implementation Details

### Code Location
- **Primary Implementation**: `rag_mongo.py` - `query_rag()` function
- **Index Setup**: `mongo_setup_indexes.py`
- **Tests**: `test_hybrid_search.py`, `test_hybrid_unit.py`

### Key Components

```python
from langchain_mongodb.retrievers import MongoDBAtlasHybridSearchRetriever

retriever = MongoDBAtlasHybridSearchRetriever(
    vectorstore=vector_store,          # MongoDBAtlasVectorSearch instance
    search_index_name="fulltext_index", # Atlas Search index for full-text
    k=3,                                # Number of results to return
    pre_filter={"source": "my_source"}, # Optional metadata filter
    vector_penalty=60.0,                # RRF penalty for vector search
    fulltext_penalty=60.0,              # RRF penalty for full-text search
    vector_weight=1.0,                  # Weight multiplier for vector scores
    fulltext_weight=1.0,                # Weight multiplier for full-text scores
)
```

## Required Atlas Search Indexes

### 1. Vector Index (`vector_index`)

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

**Purpose**: Enables vector similarity search on the embedding field

### 2. Full-Text Index (`fulltext_index`)

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

**Purpose**: Enables keyword search on the page_content field

## Tuning Parameters

### Penalty Parameters
- **Lower penalty = Higher importance**
- Default: 60.0 for both vector and full-text
- Range: Typically 1-100

```python
vector_penalty=40.0    # Increase importance of semantic search
fulltext_penalty=80.0  # Decrease importance of keyword search
```

### Weight Parameters
- **Higher weight = More influence**
- Default: 1.0 for both
- Range: 0.0 to any positive value

```python
vector_weight=2.0      # Double the vector search contribution
fulltext_weight=1.0    # Keep full-text at normal weight
```

### Oversampling Factor
- Controls candidate pool size
- Default: 10
- Candidates retrieved = k × oversampling_factor

```python
oversampling_factor=20  # Larger pool for better ranking
```

## Testing

### Run All Tests
```bash
python test_hybrid_search.py
```

### Run Unit Tests Only
```bash
python test_hybrid_unit.py
```

### Expected Results
- All imports should succeed
- MongoDB connection should work
- Hybrid retriever should initialize
- Document count should be accessible
- Query tests will skip if collection is empty or indexes are missing

## Setup Instructions

1. **Start MongoDB Atlas** (M10+ cluster required)

2. **Create Indexes**:
   ```bash
   python mongo_setup_indexes.py
   ```
   Follow the instructions to create both indexes via Atlas UI

3. **Ingest Documents**:
   ```bash
   python setup_rag.py --siem both
   ```

4. **Test Hybrid Search**:
   ```bash
   python test_hybrid_search.py
   ```

## Troubleshooting

### "Index not found" errors
- Ensure both `vector_index` and `fulltext_index` are created
- Verify index names match exactly
- Wait for indexes to finish building (check Atlas UI)

### Poor search results
- Try adjusting penalty parameters
- Ensure documents are properly ingested
- Check that embeddings are generated correctly

### "M0 cluster not supported" error
- MongoDB Atlas free tier (M0) does not support vector search
- Upgrade to at least M10 cluster
- Or use a self-hosted MongoDB with Atlas Search

## Benefits Over Simple Vector Search

1. **Better Recall**: Finds both semantically similar and exact matches
2. **Robustness**: Works even when query terminology differs from documents
3. **Precision**: Keyword matching ensures important terms are included
4. **Flexibility**: Tunable to prioritize semantic or keyword matching

## References

- [LangChain MongoDB Documentation](https://langchain-mongodb.readthedocs.io/)
- [MongoDB Atlas Search](https://www.mongodb.com/docs/atlas/atlas-search/)
- [RRF Algorithm (Microsoft)](https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking)
- [MongoDBAtlasHybridSearchRetriever API](https://langchain-mongodb.readthedocs.io/en/latest/langchain_mongodb/retrievers/langchain_mongodb.retrievers.hybrid_search.MongoDBAtlasHybridSearchRetriever.html)

## Future Improvements

- Make penalties and weights configurable via API/UI
- Add A/B testing framework to compare search strategies
- Implement query analytics to optimize parameters
- Support custom RRF implementations
- Add hybrid search metrics and monitoring
