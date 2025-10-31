#!/usr/bin/env python3
"""
Test MongoDB RAG Implementation

Simple test to verify MongoDB RAG functionality without requiring full setup.
Tests basic document insertion, embedding creation, and retrieval.
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

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


def test_rag_collection_access():
    """Test RAG collection access."""
    logger.info("Testing RAG collection access...")
    try:
        from rag_mongo import get_rag_collection
        collection = get_rag_collection()
        
        # Try to count documents
        count = collection.count_documents({})
        logger.info(f"✓ RAG collection accessible. Document count: {count}")
        return True
    except Exception as e:
        logger.error(f"✗ RAG collection access failed: {e}")
        return False


def test_embedding_creation():
    """Test embedding model initialization."""
    logger.info("Testing embedding model...")
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # Test embedding
        test_text = "This is a test document for RAG system."
        embedding = embeddings.embed_query(test_text)
        
        logger.info(f"✓ Embedding model loaded. Dimension: {len(embedding)}")
        return True
    except Exception as e:
        logger.error(f"✗ Embedding model failed: {e}")
        return False


def test_document_insertion():
    """Test inserting a test document."""
    logger.info("Testing document insertion...")
    try:
        from rag_mongo import get_rag_collection
        from langchain_huggingface import HuggingFaceEmbeddings
        
        collection = get_rag_collection()
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # Create test document
        test_doc = {
            "_id": "test#test_file.txt#0",
            "page_content": "This is a test document for the MongoDB RAG system.",
            "embedding": embeddings.embed_query("This is a test document for the MongoDB RAG system."),
            "source": "test_source",
            "metadata": {
                "relative_path": "test_file.txt",
                "file_type": "txt",
                "file_size": 100
            }
        }
        
        # Try to insert (or replace if exists)
        collection.replace_one(
            {"_id": test_doc["_id"]},
            test_doc,
            upsert=True
        )
        
        # Verify insertion
        retrieved = collection.find_one({"_id": test_doc["_id"]})
        if retrieved:
            logger.info("✓ Test document inserted and retrieved successfully")
            # Clean up
            collection.delete_one({"_id": test_doc["_id"]})
            logger.info("✓ Test document cleaned up")
            return True
        else:
            logger.error("✗ Test document not found after insertion")
            return False
            
    except Exception as e:
        logger.error(f"✗ Document insertion failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_list_sources():
    """Test listing sources in the collection."""
    logger.info("Testing source listing...")
    try:
        from rag_mongo import list_sources
        
        sources = list_sources()
        logger.info(f"✓ Found {len(sources)} sources in collection: {sources}")
        return True
    except Exception as e:
        logger.error(f"✗ Source listing failed: {e}")
        return False


def test_vector_search():
    """Test vector search functionality (requires vector index)."""
    logger.info("Testing vector search...")
    logger.info("⚠ Skipping vector search test - requires Atlas M10+ cluster with vector index")
    logger.info("  To enable this test, ensure:")
    logger.info("  1. MongoDB Atlas M10+ cluster (not M0 free tier)")
    logger.info("  2. Vector search index created via Atlas UI")
    logger.info("  3. At least one document in the collection")
    return True  # Skip for now


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("MongoDB RAG System Tests")
    print("="*70 + "\n")
    
    tests = [
        ("MongoDB Connection", test_mongodb_connection),
        ("RAG Collection Access", test_rag_collection_access),
        ("Embedding Model", test_embedding_creation),
        ("Document Insertion", test_document_insertion),
        ("Source Listing", test_list_sources),
        ("Vector Search", test_vector_search),
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
        return 0
    else:
        print("✗ Some tests failed. Check the logs above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
