#!/usr/bin/env python3
"""
Test MongoDB Atlas Hybrid Search Retriever

This script tests the MongoDBAtlasHybridSearchRetriever integration.
It verifies that hybrid search (vector + full-text) works correctly.
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get the project root directory (where this file is located)
PROJECT_ROOT = Path(__file__).parent.absolute()

# Add src to path
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

def test_imports():
    """Test that all required imports work."""
    logger.info("Testing imports...")
    try:
        from langchain_mongodb import MongoDBAtlasVectorSearch
        from langchain_mongodb.retrievers import MongoDBAtlasHybridSearchRetriever
        from langchain_huggingface import HuggingFaceEmbeddings
        from config.settings import config
        from pymongo import MongoClient
        
        logger.info("✓ All imports successful")
        return True
    except Exception as e:
        logger.error(f"✗ Import failed: {e}")
        return False


def test_mongodb_connection():
    """Test MongoDB connection."""
    logger.info("Testing MongoDB connection...")
    try:
        from config.settings import config
        from pymongo import MongoClient
        
        client = MongoClient(config.database.mongo_url)
        client.admin.command('ismaster')
        logger.info("✓ MongoDB connection successful")
        return True
    except Exception as e:
        logger.error(f"✗ MongoDB connection failed: {e}")
        return False


def test_hybrid_search_retriever_setup():
    """Test that MongoDBAtlasHybridSearchRetriever can be instantiated."""
    logger.info("Testing MongoDBAtlasHybridSearchRetriever setup...")
    try:
        from langchain_mongodb import MongoDBAtlasVectorSearch
        from langchain_mongodb.retrievers import MongoDBAtlasHybridSearchRetriever
        from langchain_huggingface import HuggingFaceEmbeddings
        from rag_mongo import get_rag_collection
        
        # Get collection
        collection = get_rag_collection()
        
        # Initialize embeddings
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # Create vector store
        vector_store = MongoDBAtlasVectorSearch(
            collection=collection,
            embedding=embeddings,
            index_name="vector_index",
            text_key="page_content",
            embedding_key="embedding"
        )
        
        # Create hybrid search retriever
        retriever = MongoDBAtlasHybridSearchRetriever(
            vectorstore=vector_store,
            search_index_name="fulltext_index",
            k=3,
            pre_filter={"source": "test_source"},
            vector_penalty=60.0,
            fulltext_penalty=60.0,
            vector_weight=1.0,
            fulltext_weight=1.0,
        )
        
        logger.info("✓ MongoDBAtlasHybridSearchRetriever created successfully")
        logger.info(f"  - Vector index: vector_index")
        logger.info(f"  - Full-text index: fulltext_index")
        logger.info(f"  - Top K: 3")
        logger.info(f"  - Pre-filter: source=test_source")
        return True
        
    except Exception as e:
        logger.error(f"✗ MongoDBAtlasHybridSearchRetriever setup failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_document_count():
    """Test document count in collection."""
    logger.info("Testing document count...")
    try:
        from rag_mongo import get_rag_collection, list_sources
        
        collection = get_rag_collection()
        count = collection.count_documents({})
        sources = list_sources()
        
        logger.info(f"✓ Collection accessible")
        logger.info(f"  - Total documents: {count}")
        logger.info(f"  - Sources: {sources}")
        
        if count == 0:
            logger.warning("⚠ Collection is empty. Run setup_rag.py to add documents.")
        
        return True
    except Exception as e:
        logger.error(f"✗ Document count failed: {e}")
        return False


def test_hybrid_search_query():
    """Test a simple hybrid search query (requires indexes and documents)."""
    logger.info("Testing hybrid search query...")
    try:
        from rag_mongo import get_rag_collection, list_sources
        from langchain_mongodb import MongoDBAtlasVectorSearch
        from langchain_mongodb.retrievers import MongoDBAtlasHybridSearchRetriever
        from langchain_huggingface import HuggingFaceEmbeddings
        
        # Get collection and check if it has documents
        collection = get_rag_collection()
        count = collection.count_documents({})
        
        if count == 0:
            logger.warning("⚠ Skipping query test - collection is empty")
            logger.warning("  Run 'python setup_rag.py --siem both' to add documents")
            return True
        
        sources = list_sources()
        if not sources:
            logger.warning("⚠ Skipping query test - no sources available")
            return True
        
        # Use first available source
        test_source = sources[0]
        logger.info(f"  Testing with source: {test_source}")
        
        # Initialize embeddings
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # Create vector store
        vector_store = MongoDBAtlasVectorSearch(
            collection=collection,
            embedding=embeddings,
            index_name="vector_index",
            text_key="page_content",
            embedding_key="embedding"
        )
        
        # Create hybrid search retriever
        retriever = MongoDBAtlasHybridSearchRetriever(
            vectorstore=vector_store,
            search_index_name="fulltext_index",
            k=3,
            pre_filter={"source": test_source},
        )
        
        # Try a simple search
        test_query = "configuration"
        logger.info(f"  Executing query: '{test_query}'")
        
        documents = retriever.get_relevant_documents(test_query)
        
        logger.info(f"✓ Hybrid search query successful")
        logger.info(f"  - Retrieved {len(documents)} documents")
        
        if documents:
            logger.info(f"  - First result preview: {documents[0].page_content[:100]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Hybrid search query failed: {e}")
        logger.error("  This is expected if:")
        logger.error("  1. Atlas Search indexes are not created")
        logger.error("  2. Using MongoDB M0 free tier (doesn't support vector search)")
        logger.error("  3. Collection is empty")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("MongoDB Atlas Hybrid Search Retriever Tests")
    print("="*70 + "\n")
    
    tests = [
        ("Imports", test_imports),
        ("MongoDB Connection", test_mongodb_connection),
        ("Hybrid Search Retriever Setup", test_hybrid_search_retriever_setup),
        ("Document Count", test_document_count),
        ("Hybrid Search Query", test_hybrid_search_query),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test '{test_name}' raised exception: {e}")
            results.append((test_name, False))
        print()  # Blank line between tests
    
    # Summary
    print("="*70)
    print("Test Summary")
    print("="*70)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} - {test_name}")
    
    print("-"*70)
    print(f"Passed: {passed}/{total}")
    print("="*70 + "\n")
    
    if passed == total:
        print("✓ All tests passed!")
        print("\nHybrid Search Implementation Notes:")
        print("- Uses MongoDBAtlasHybridSearchRetriever from langchain-mongodb")
        print("- Combines vector search (semantic) + full-text search (keyword)")
        print("- Ranks results using Reciprocal Rank Fusion (RRF)")
        print("- Requires TWO Atlas Search indexes:")
        print("  1. vector_index (for embeddings)")
        print("  2. fulltext_index (for text search)")
        return 0
    else:
        print("✗ Some tests failed. Check the logs above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
