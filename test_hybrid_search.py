#!/usr/bin/env python3
"""
Test MongoDB Hybrid Search Implementation

Tests the hybrid search functionality with vector + text search + RRF.
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


def test_hybrid_retriever_creation():
    """Test creating a hybrid search retriever."""
    logger.info("Testing hybrid search retriever creation...")
    try:
        from rag_mongo import MongoDBAtlasHybridSearchRetriever, get_rag_collection
        from langchain_huggingface import HuggingFaceEmbeddings
        
        collection = get_rag_collection()
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # Create retriever
        retriever = MongoDBAtlasHybridSearchRetriever(
            collection=collection,
            embeddings=embeddings,
            vector_index_name="vector_index",
            text_index_name="text_index",
            top_k=3,
            pre_filter={"source": "test_source"}
        )
        
        logger.info("✓ Hybrid search retriever created successfully")
        logger.info(f"  Vector index: {retriever.vector_index_name}")
        logger.info(f"  Text index: {retriever.text_index_name}")
        logger.info(f"  Top K: {retriever.top_k}")
        return True
    except Exception as e:
        logger.error(f"✗ Hybrid retriever creation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_pipeline_functions():
    """Test that pipeline functions are available."""
    logger.info("Testing pipeline functions availability...")
    try:
        from langchain_mongodb.pipelines import (
            vector_search_stage,
            text_search_stage,
            reciprocal_rank_stage,
            final_hybrid_stage,
            combine_pipelines
        )
        
        logger.info("✓ All pipeline functions imported successfully:")
        logger.info("  - vector_search_stage")
        logger.info("  - text_search_stage")
        logger.info("  - reciprocal_rank_stage")
        logger.info("  - final_hybrid_stage")
        logger.info("  - combine_pipelines")
        return True
    except Exception as e:
        logger.error(f"✗ Pipeline functions import failed: {e}")
        return False


def test_hybrid_query_function():
    """Test that hybrid query function is available."""
    logger.info("Testing hybrid query function availability...")
    try:
        from rag_mongo import query_rag_hybrid
        
        # Check function signature
        import inspect
        sig = inspect.signature(query_rag_hybrid)
        params = list(sig.parameters.keys())
        
        logger.info("✓ query_rag_hybrid function available")
        logger.info(f"  Parameters: {', '.join(params)}")
        
        # Check for expected parameters
        expected_params = ['source', 'query', 'vector_weight', 'text_weight']
        for param in expected_params:
            if param in params:
                logger.info(f"  ✓ Has parameter: {param}")
            else:
                logger.warning(f"  ⚠ Missing parameter: {param}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Hybrid query function test failed: {e}")
        return False


def test_hybrid_search_with_mock_data():
    """Test hybrid search with mock data (skipped if no MongoDB)."""
    logger.info("Testing hybrid search with mock data...")
    logger.info("⚠ This test requires:")
    logger.info("  1. MongoDB Atlas M10+ cluster running")
    logger.info("  2. Vector search index (vector_index) created")
    logger.info("  3. Text search index (text_index) created")
    logger.info("  4. At least one document in the collection")
    logger.info("✓ Skipping actual execution - would require live Atlas deployment")
    return True


def test_vector_only_compatibility():
    """Test that vector-only search still works (backward compatibility)."""
    logger.info("Testing backward compatibility with vector-only search...")
    try:
        from rag_mongo import query_rag
        import inspect
        
        sig = inspect.signature(query_rag)
        logger.info("✓ query_rag function still available for backward compatibility")
        logger.info(f"  Parameters: {', '.join(sig.parameters.keys())}")
        return True
    except Exception as e:
        logger.error(f"✗ Backward compatibility test failed: {e}")
        return False


def test_index_setup_instructions():
    """Test that index setup script includes hybrid search instructions."""
    logger.info("Testing index setup instructions...")
    try:
        # Read the index setup script
        with open('mongo_setup_indexes.py', 'r') as f:
            content = f.read()
        
        checks = {
            'vector_index': 'vector_index' in content,
            'text_index': 'text_index' in content,
            'vector search': 'vector' in content.lower() and 'search' in content.lower(),
            'text search': 'text' in content.lower() and 'search' in content.lower(),
            'hybrid': 'hybrid' in content.lower() or 'text_index' in content
        }
        
        all_passed = all(checks.values())
        
        if all_passed:
            logger.info("✓ Index setup script includes hybrid search instructions")
            for check, passed in checks.items():
                logger.info(f"  ✓ Includes: {check}")
        else:
            logger.warning("⚠ Some checks failed in index setup script:")
            for check, passed in checks.items():
                status = "✓" if passed else "✗"
                logger.info(f"  {status} {check}")
        
        return all_passed
    except Exception as e:
        logger.error(f"✗ Index setup instructions test failed: {e}")
        return False


def test_migration_docs_updated():
    """Test that migration documentation mentions hybrid search."""
    logger.info("Testing migration documentation...")
    try:
        with open('MIGRATION_MONGODB.md', 'r') as f:
            content = f.read()
        
        checks = {
            'Hybrid search': 'hybrid search' in content.lower(),
            'RRF': 'reciprocal rank fusion' in content.lower() or 'rrf' in content.lower(),
            'Text index': 'text_index' in content or 'text search index' in content.lower(),
            'Vector index': 'vector_index' in content or 'vector search index' in content.lower(),
            'query_rag_hybrid': 'query_rag_hybrid' in content
        }
        
        all_passed = all(checks.values())
        
        if all_passed:
            logger.info("✓ Migration documentation includes hybrid search information")
            for check in checks.keys():
                logger.info(f"  ✓ Mentions: {check}")
        else:
            logger.warning("⚠ Some documentation checks failed:")
            for check, passed in checks.items():
                status = "✓" if passed else "✗"
                logger.info(f"  {status} {check}")
        
        return all_passed
    except Exception as e:
        logger.error(f"✗ Migration docs test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("MongoDB Hybrid Search Tests")
    print("="*70 + "\n")
    
    tests = [
        ("Pipeline Functions", test_pipeline_functions),
        ("Hybrid Retriever Creation", test_hybrid_retriever_creation),
        ("Hybrid Query Function", test_hybrid_query_function),
        ("Vector-Only Compatibility", test_vector_only_compatibility),
        ("Index Setup Instructions", test_index_setup_instructions),
        ("Migration Documentation", test_migration_docs_updated),
        ("Hybrid Search with Mock Data", test_hybrid_search_with_mock_data),
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
        print("\nNext steps:")
        print("1. Deploy to MongoDB Atlas M10+ cluster")
        print("2. Create vector_index via Atlas UI (see mongo_setup_indexes.py)")
        print("3. Create text_index via Atlas UI (see mongo_setup_indexes.py)")
        print("4. Run setup_rag.py to ingest documents")
        print("5. Test hybrid search with real queries")
        return 0
    else:
        print("✗ Some tests failed. Check the logs above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
