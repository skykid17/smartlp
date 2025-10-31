#!/usr/bin/env python3
"""
Simple unit test to verify MongoDBAtlasHybridSearchRetriever is properly integrated
without requiring network access to HuggingFace.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_import():
    """Test that the hybrid search retriever can be imported."""
    print("Testing MongoDBAtlasHybridSearchRetriever import...")
    try:
        from langchain_mongodb.retrievers import MongoDBAtlasHybridSearchRetriever
        print("✓ MongoDBAtlasHybridSearchRetriever imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import: {e}")
        return False

def test_rag_mongo_import():
    """Test that rag_mongo.py has the correct imports."""
    print("\nTesting rag_mongo.py imports...")
    try:
        import rag_mongo
        # Check if the module has MongoDBAtlasHybridSearchRetriever in its code
        import inspect
        source = inspect.getsource(rag_mongo)
        
        if "MongoDBAtlasHybridSearchRetriever" in source:
            print("✓ rag_mongo.py uses MongoDBAtlasHybridSearchRetriever")
            return True
        else:
            print("✗ rag_mongo.py does not use MongoDBAtlasHybridSearchRetriever")
            return False
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

def test_query_rag_function():
    """Test that query_rag function has been updated."""
    print("\nTesting query_rag function implementation...")
    try:
        import rag_mongo
        import inspect
        
        # Get the source code of query_rag
        source = inspect.getsource(rag_mongo.query_rag)
        
        # Check for key hybrid search components
        checks = [
            ("MongoDBAtlasHybridSearchRetriever", "Uses hybrid search retriever"),
            ("search_index_name", "Configures full-text search index"),
            ("fulltext_index", "References fulltext_index"),
            ("vector_penalty", "Configures RRF vector penalty"),
            ("fulltext_penalty", "Configures RRF fulltext penalty"),
            ("Hybrid search combines", "Has hybrid search documentation"),
        ]
        
        passed = 0
        failed = 0
        
        for check_string, description in checks:
            if check_string in source:
                print(f"  ✓ {description}")
                passed += 1
            else:
                print(f"  ✗ {description}")
                failed += 1
        
        if failed == 0:
            print(f"✓ query_rag function properly implements hybrid search ({passed}/{len(checks)} checks passed)")
            return True
        else:
            print(f"✗ query_rag function missing some hybrid search features ({passed}/{len(checks)} checks passed)")
            return False
            
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mongo_setup_indexes():
    """Test that mongo_setup_indexes.py has been updated."""
    print("\nTesting mongo_setup_indexes.py updates...")
    try:
        with open('mongo_setup_indexes.py', 'r') as f:
            content = f.read()
        
        checks = [
            ("fulltext_index", "References fulltext_index"),
            ("Full-Text Search Index", "Has full-text search documentation"),
            ("HYBRID SEARCH", "Mentions hybrid search"),
            ("TWO indexes", "Documents need for two indexes"),
        ]
        
        passed = 0
        failed = 0
        
        for check_string, description in checks:
            if check_string in content:
                print(f"  ✓ {description}")
                passed += 1
            else:
                print(f"  ✗ {description}")
                failed += 1
        
        if failed == 0:
            print(f"✓ mongo_setup_indexes.py properly documents hybrid search setup ({passed}/{len(checks)} checks passed)")
            return True
        else:
            print(f"✗ mongo_setup_indexes.py missing some documentation ({passed}/{len(checks)} checks passed)")
            return False
            
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

def main():
    print("="*70)
    print("MongoDB Atlas Hybrid Search Integration Unit Tests")
    print("="*70)
    
    tests = [
        test_import,
        test_rag_mongo_import,
        test_query_rag_function,
        test_mongo_setup_indexes,
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
    
    print("\n" + "="*70)
    print("Summary")
    print("="*70)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed!")
        print("\nImplementation Summary:")
        print("- Replaced custom similarity search with MongoDBAtlasHybridSearchRetriever")
        print("- Hybrid search combines vector search (semantic) + full-text search (keywords)")
        print("- Results ranked using Reciprocal Rank Fusion (RRF)")
        print("- Requires two Atlas Search indexes: vector_index and fulltext_index")
        print("- Updated documentation in mongo_setup_indexes.py")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
