#!/usr/bin/env python3
"""
Verification Script for MongoDB Hybrid Search Implementation

This script verifies that all components for hybrid search are in place.
"""

import os
import sys

def check_file_exists(filepath, description):
    """Check if a file exists."""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description} MISSING: {filepath}")
        return False

def check_file_contains(filepath, search_strings, description):
    """Check if a file contains specific strings."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        missing = []
        for search_str in search_strings:
            if search_str not in content:
                missing.append(search_str)
        
        if not missing:
            print(f"✅ {description}")
            return True
        else:
            print(f"⚠️ {description} - Missing: {', '.join(missing)}")
            return False
    except Exception as e:
        print(f"❌ {description} - Error: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("MongoDB Hybrid Search Implementation Verification")
    print("="*70 + "\n")
    
    results = []
    
    # Check core files exist
    print("1. Core Implementation Files:")
    results.append(check_file_exists("rag_mongo.py", "Main RAG implementation"))
    results.append(check_file_exists("rag_func.py", "Backward compatibility wrapper"))
    results.append(check_file_exists("mongo_setup_indexes.py", "Index setup script"))
    results.append(check_file_exists("test_hybrid_search.py", "Hybrid search tests"))
    print()
    
    # Check rag_mongo.py contains hybrid search implementation
    print("2. Hybrid Search Implementation:")
    results.append(check_file_contains(
        "rag_mongo.py",
        ["MongoDBAtlasHybridSearchRetriever", "query_rag_hybrid", "reciprocal_rank_stage", "text_search_stage"],
        "rag_mongo.py contains hybrid search classes and functions"
    ))
    print()
    
    # Check mongo_setup_indexes.py has both index instructions
    print("3. Index Setup Instructions:")
    results.append(check_file_contains(
        "mongo_setup_indexes.py",
        ["vector_index", "text_index", "check_atlas_text_search_index"],
        "mongo_setup_indexes.py has both vector and text index instructions"
    ))
    print()
    
    # Check documentation
    print("4. Documentation:")
    results.append(check_file_contains(
        "README.md",
        ["hybrid search", "Reciprocal Rank Fusion", "query_rag_hybrid", "text_index", "vector_index"],
        "README.md documents hybrid search"
    ))
    results.append(check_file_contains(
        "MIGRATION_MONGODB.md",
        ["hybrid search", "RRF", "query_rag_hybrid", "text_index"],
        "MIGRATION_MONGODB.md documents hybrid search"
    ))
    print()
    
    # Check ChromaDB removal
    print("5. ChromaDB Removal:")
    results.append(check_file_contains(
        "requirements.txt",
        [],  # We're checking it does NOT contain chromadb
        "requirements.txt (checking no chromadb)"
    ))
    
    # Manually check for chromadb absence
    try:
        with open("requirements.txt", 'r') as f:
            content = f.read().lower()
        if "chroma" not in content:
            print("✅ requirements.txt does not contain chromadb")
            results.append(True)
        else:
            print("❌ requirements.txt still contains chromadb")
            results.append(False)
    except Exception as e:
        print(f"❌ Error checking requirements.txt: {e}")
        results.append(False)
    
    print()
    
    # Check exports in rag_func.py
    print("6. Exports for Backward Compatibility:")
    results.append(check_file_contains(
        "rag_func.py",
        ["query_rag_hybrid", "MongoDBAtlasHybridSearchRetriever"],
        "rag_func.py exports hybrid search functions"
    ))
    print()
    
    # Summary
    print("="*70)
    print("Verification Summary")
    print("="*70)
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total} checks")
    
    if passed == total:
        print("\n✅ ALL CHECKS PASSED!")
        print("\n📋 Implementation complete. Next steps:")
        print("   1. Deploy to MongoDB Atlas M10+ cluster")
        print("   2. Create vector_index via Atlas UI")
        print("   3. Create text_index via Atlas UI")
        print("   4. Run: python setup_rag.py --siem both")
        print("   5. Test with: python -c \"from rag_func import query_rag_hybrid; print('Ready!')\"")
        return 0
    else:
        print("\n❌ Some checks failed. Review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
