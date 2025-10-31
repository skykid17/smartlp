#!/usr/bin/env python3
"""
MongoDB RAG Index Setup Script

This script creates the necessary indexes for the RAG vector store in MongoDB.
Run this after setting up your MongoDB instance and before running setup_rag.py.

Usage:
    python mongo_setup_indexes.py
"""

import os
import sys
from pymongo import MongoClient
from pymongo.errors import OperationFailure

# Add src to path to import config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from config.settings import config
except ImportError:
    print("Error: Could not import configuration. Make sure you're running from the project root.")
    sys.exit(1)


def create_compound_index(collection):
    """Create compound index for source and metadata filtering."""
    try:
        # Check if index already exists
        existing_indexes = collection.list_indexes()
        index_exists = False
        for idx in existing_indexes:
            if 'source_1_metadata.relative_path_1' in idx['name']:
                index_exists = True
                break
        
        if index_exists:
            print("✓ Compound index already exists")
            return True
        
        # Create the index
        collection.create_index([("source", 1), ("metadata.relative_path", 1)])
        print("✓ Created compound index on source and metadata.relative_path")
        return True
    except Exception as e:
        print(f"✗ Error creating compound index: {e}")
        return False


def check_atlas_search_indexes(db_name, collection_name):
    """
    Check if Atlas Search indexes exist.
    Note: Search indexes must be created via Atlas UI or API.
    """
    print("\n" + "="*70)
    print("ATLAS SEARCH INDEXES SETUP (REQUIRED FOR HYBRID SEARCH)")
    print("="*70)
    print("\nAtlas Search indexes MUST be created via MongoDB Atlas UI.")
    print("This script cannot create them programmatically for you.")
    print("\nFor HYBRID SEARCH, you need TWO indexes:")
    print("\n" + "="*70)
    print("INDEX 1: Vector Search Index")
    print("="*70)
    print("\n1. Go to MongoDB Atlas → Database → Search")
    print("2. Click 'Create Search Index'")
    print("3. Select 'JSON Editor'")
    print("4. Use this configuration:")
    print("\n" + "-"*70)
    print("""{
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
}""")
    print("-"*70)
    print(f"\n5. Name the index: vector_index")
    print(f"6. Select database: {db_name}")
    print(f"7. Select collection: {collection_name}")
    
    print("\n" + "="*70)
    print("INDEX 2: Full-Text Search Index")
    print("="*70)
    print("\n1. Go to MongoDB Atlas → Database → Search")
    print("2. Click 'Create Search Index'")
    print("3. Select 'JSON Editor'")
    print("4. Use this configuration:")
    print("\n" + "-"*70)
    print("""{
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
}""")
    print("-"*70)
    print(f"\n5. Name the index: fulltext_index")
    print(f"6. Select database: {db_name}")
    print(f"7. Select collection: {collection_name}")
    
    print("\n✓ After creating BOTH indexes, you can proceed with setup_rag.py")
    print("="*70)


def main():
    """Main setup function."""
    print("\n" + "="*70)
    print("MongoDB RAG Index Setup")
    print("="*70)
    
    # Get MongoDB configuration
    try:
        mongo_url = config.database.mongo_url
        db_name = config.database.rag_db_name
        collection_name = config.database.rag_collection
    except Exception as e:
        print(f"\n✗ Error reading configuration: {e}")
        print("Make sure your .env file is properly configured with:")
        print("  - MONGO_URL")
        print("  - MONGO_RAG_DB (optional, defaults to 'rag')")
        print("  - MONGO_RAG_COLLECTION (optional, defaults to 'rag')")
        sys.exit(1)
    
    print(f"\nConnecting to MongoDB...")
    print(f"  Database: {db_name}")
    print(f"  Collection: {collection_name}")
    
    # Connect to MongoDB
    try:
        client = MongoClient(mongo_url)
        # Test connection
        client.admin.command('ismaster')
        print("✓ Connected to MongoDB successfully")
    except Exception as e:
        print(f"\n✗ Failed to connect to MongoDB: {e}")
        print("\nPlease check:")
        print("  1. MongoDB is running")
        print("  2. MONGO_URL in .env is correct")
        print("  3. Network connectivity")
        sys.exit(1)
    
    # Get database and collection
    db = client[db_name]
    collection = db[collection_name]
    
    print(f"\n" + "-"*70)
    print("Creating Standard Indexes...")
    print("-"*70)
    
    # Create compound index
    success = create_compound_index(collection)
    
    if success:
        print("\n✓ Standard indexes created successfully")
    else:
        print("\n✗ Some standard indexes failed to create")
    
    # Show search indexes instructions
    check_atlas_search_indexes(db_name, collection_name)
    
    # Check MongoDB deployment type
    print("\n" + "-"*70)
    print("MongoDB Deployment Check")
    print("-"*70)
    try:
        build_info = client.admin.command('buildInfo')
        server_info = client.server_info()
        
        print(f"\nMongoDB Version: {server_info.get('version', 'Unknown')}")
        
        # Check if this is Atlas
        if 'atlas' in mongo_url.lower():
            print("Deployment: MongoDB Atlas (Cloud)")
            print("\n⚠ IMPORTANT: Vector search requires at least an M10 cluster.")
            print("   Free tier (M0) does NOT support vector search.")
            print("   Upgrade your cluster if needed: Atlas → Clusters → Modify")
        else:
            print("Deployment: Self-hosted or Local MongoDB")
            print("\n⚠ NOTE: Self-hosted MongoDB requires Atlas Search to be installed")
            print("   and configured separately for vector search functionality.")
            print("   See: https://www.mongodb.com/docs/atlas/atlas-search/")
    except Exception as e:
        print(f"Could not determine deployment type: {e}")
    
    print("\n" + "="*70)
    print("Setup Complete")
    print("="*70)
    print("\nNext steps:")
    print("1. Create BOTH search indexes via Atlas UI (see instructions above)")
    print("   - vector_index (for vector similarity search)")
    print("   - fulltext_index (for full-text keyword search)")
    print("2. Run: python setup_rag.py --siem both")
    print("3. Verify embeddings are created: mongo shell or Compass")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
