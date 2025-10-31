"""
MongoDB-based RAG (Retrieval-Augmented Generation) implementation.

This module provides embeddings creation, document ingestion, and retrieval
using MongoDB Atlas as the vector store backend with hybrid search capabilities.
"""

import os
import sys
import logging
import csv
import json
import hashlib
import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set
import yaml

from pymongo import MongoClient
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_mongodb.retrievers import MongoDBAtlasHybridSearchRetriever
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_community.document_loaders import JSONLoader, TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Import database utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from database.connection import db_connection
from config.settings import config

TOP_K = 3

# MongoDB client initialization
def get_mongo_client() -> MongoClient:
    """Get MongoDB client instance."""
    return MongoClient(config.database.mongo_url)


def get_rag_collection():
    """Get the RAG collection from MongoDB."""
    client = get_mongo_client()
    db = client[config.database.rag_db_name]
    return db[config.database.rag_collection]


class FileMetadata:
    """Helper class to manage file metadata for change detection"""
    
    def __init__(self, file_path: Path, base_path: Path):
        self.file_path = file_path
        self.relative_path = file_path.relative_to(base_path)
        self.modification_time = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
        self.file_hash = self._calculate_hash()
        self.file_size = file_path.stat().st_size
    
    def _calculate_hash(self) -> str:
        """Calculate SHA256 hash of file content"""
        hasher = hashlib.sha256()
        try:
            with open(self.file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logging.warning(f"Could not calculate hash for {self.file_path}: {e}")
            return f"error_{datetime.datetime.now().isoformat()}"
    
    def has_changed(self, other_metadata: Dict) -> bool:
        """Check if file has changed compared to stored metadata"""
        if not other_metadata:
            return True
        
        stored_mtime = other_metadata.get('modification_time', '')
        stored_hash = other_metadata.get('file_hash', '')
        stored_size = other_metadata.get('file_size', 0)
        
        # Quick check: modification time and size
        if (self.modification_time != stored_mtime or 
            self.file_size != stored_size):
            return True
        
        # Deep check: content hash
        return self.file_hash != stored_hash
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage in document metadata"""
        return {
            'relative_path': str(self.relative_path),
            'modification_time': self.modification_time.isoformat(),
            'file_hash': self.file_hash,
            'file_size': self.file_size,
            'last_processed': datetime.datetime.now().isoformat()
        }


def generate_document_id(source: str, relative_path: Path, chunk_index: int) -> str:
    """Generate consistent document ID based on source, file path and chunk index"""
    return f"{source}#{str(relative_path).replace(os.sep, '/')}#{chunk_index}"


def extract_file_path_from_id(doc_id: str) -> str:
    """Extract file path from document ID"""
    parts = doc_id.split('#')
    return parts[1] if len(parts) > 1 else ""


def get_existing_file_metadata(collection, source: str) -> Dict[str, Dict]:
    """Get metadata for all files currently in the collection for a given source"""
    try:
        # Query documents for this source
        docs = collection.find({"source": source}, {"metadata": 1, "_id": 0})
        file_metadata = {}
        
        for doc in docs:
            metadata = doc.get('metadata', {})
            if 'relative_path' in metadata:
                rel_path = metadata['relative_path']
                if rel_path not in file_metadata:
                    file_metadata[rel_path] = {
                        'modification_time': metadata.get('modification_time', ''),
                        'file_hash': metadata.get('file_hash', ''),
                        'file_size': metadata.get('file_size', 0),
                        'last_processed': metadata.get('last_processed', '')
                    }
        
        return file_metadata
    except Exception as e:
        logging.warning(f"Could not retrieve existing file metadata: {e}")
        return {}


def delete_file_chunks(collection, source: str, relative_path: str):
    """Delete all chunks for a specific file in a given source"""
    try:
        # Normalize path
        file_path_normalized = relative_path.replace(os.sep, '/')
        
        # Delete all documents matching this source and file path
        result = collection.delete_many({
            "source": source,
            "metadata.relative_path": file_path_normalized
        })
        
        deleted_count = result.deleted_count
        if deleted_count > 0:
            logging.info(f"Deleted {deleted_count} chunks for file: {relative_path} in source: {source}")
        return deleted_count
        
    except Exception as e:
        logging.error(f"Error deleting chunks for file {relative_path}: {e}")
        return 0


def create_embeddings(
    file_or_folder_path: str,
    collection_name: str,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    max_batch_size: int = 5461
) -> bool:
    """
    Create embeddings for files and store in MongoDB.
    
    Args:
        file_or_folder_path: Path to file or folder to process
        collection_name: Source identifier (e.g., 'splunk_addons', 'elastic_packages')
        embedding_model: HuggingFace embedding model name
        chunk_size: Size of text chunks for splitting
        chunk_overlap: Overlap between chunks
        max_batch_size: Maximum number of chunks to process in a single batch
        
    Returns:
        bool: True if successful, False otherwise
    """
    return _process_embeddings(
        file_or_folder_path=file_or_folder_path,
        collection_name=collection_name,
        embedding_model=embedding_model,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        max_batch_size=max_batch_size,
        operation_mode="create"
    )


def update_embeddings(
    file_or_folder_path: str,
    collection_name: str,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    max_batch_size: int = 5461,
    force_update: bool = False
) -> bool:
    """
    Update embeddings for changed files only.
    
    Args:
        file_or_folder_path: Path to file or folder to process
        collection_name: Source identifier (e.g., 'splunk_addons', 'elastic_packages')
        embedding_model: HuggingFace embedding model name
        chunk_size: Size of text chunks for splitting
        chunk_overlap: Overlap between chunks
        max_batch_size: Maximum number of chunks to process in a single batch
        force_update: Force update all files regardless of change detection
        
    Returns:
        bool: True if successful, False otherwise
    """
    return _process_embeddings(
        file_or_folder_path=file_or_folder_path,
        collection_name=collection_name,
        embedding_model=embedding_model,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        max_batch_size=max_batch_size,
        operation_mode="update",
        force_update=force_update
    )


def _process_embeddings(
    file_or_folder_path: str,
    collection_name: str,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    max_batch_size: int = 5461,
    operation_mode: str = "create",
    force_update: bool = False
) -> bool:
    """
    Internal function to process embeddings with different operation modes.
    
    Args:
        file_or_folder_path: Path to file or folder to process
        collection_name: Source identifier (e.g., 'splunk_addons', 'elastic_packages')
        embedding_model: HuggingFace embedding model name
        chunk_size: Size of text chunks for splitting
        chunk_overlap: Overlap between chunks
        max_batch_size: Maximum number of chunks to process in a single batch
        operation_mode: Either "create" or "update"
        force_update: Force update all files regardless of change detection
        
    Returns:
        bool: True if successful, False otherwise
    """
    
    # Supported file extensions
    SUPPORTED_EXTENSIONS = {
        '.yaml', '.yml', '.txt', '.json', '.md', '.conf', '.csv', '.pdf'
    }
    
    def load_yaml_file(file_path: Path) -> List[Document]:
        """Load YAML file and return as Document"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                yaml.safe_load(content)
                return [Document(
                    page_content=content,
                    metadata={
                        'source': file_path.name,
                        'file_type': 'yaml',
                        'full_path': str(file_path)
                    }
                )]
        except Exception as e:
            logging.error(f"Error loading YAML file {file_path}: {e}")
            return []
    
    def load_csv_file(file_path: Path) -> List[Document]:
        """Load CSV file and return as Document"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                rows = list(csv_reader)
                content = "\n".join([",".join(row) for row in rows])
                return [Document(
                    page_content=content,
                    metadata={
                        'source': file_path.name,
                        'file_type': 'csv',
                        'full_path': str(file_path),
                        'rows_count': len(rows)
                    }
                )]
        except Exception as e:
            logging.error(f"Error loading CSV file {file_path}: {e}")
            return []
    
    def load_pdf_file(file_path: Path) -> List[Document]:
        """Load PDF file and return as Document using LangChain's PyPDFLoader"""
        try:
            loader = PyPDFLoader(str(file_path))
            documents = loader.load()
            
            # Update metadata for all pages
            for doc in documents:
                doc.metadata.update({
                    'file_type': 'pdf',
                    'full_path': str(file_path)
                })
            
            return documents
        except Exception as e:
            logging.error(f"Error loading PDF file {file_path}: {e}")
            return []
    
    def load_document(file_path: Path) -> List[Document]:
        """Load a document based on its file type"""
        extension = file_path.suffix.lower()
        
        try:
            if extension in ['.yaml', '.yml']:
                return load_yaml_file(file_path)
            elif extension == '.json':
                loader = JSONLoader(str(file_path), jq_schema='.', text_content=False)
                documents = loader.load()
                for doc in documents:
                    doc.metadata.update({
                        'file_type': 'json',
                        'full_path': str(file_path)
                    })
                return documents
            elif extension == '.csv':
                return load_csv_file(file_path)
            elif extension == '.pdf':
                return load_pdf_file(file_path)
            elif extension in ['.txt', '.md', '.conf']:
                loader = TextLoader(str(file_path), encoding='utf-8')
                documents = loader.load()
                for doc in documents:
                    doc.metadata.update({
                        'file_type': extension[1:],
                        'full_path': str(file_path)
                    })
                return documents
            else:
                logging.warning(f"Unsupported file type: {extension}")
                return []
        except Exception as e:
            logging.error(f"Error loading file {file_path}: {e}")
            return []
    
    def get_files_to_process(path: Path) -> List[Path]:
        """Get list of files to process from path"""
        files = []
        
        if path.is_file():
            if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(path)
            else:
                logging.warning(f"Unsupported file type: {path}")
        elif path.is_dir():
            for file_path in path.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    files.append(file_path)
        else:
            logging.error(f"Path does not exist: {path}")
        
        return files
    
    def process_file_with_ids(file_path: Path, base_path: Path, 
                            file_metadata: FileMetadata, 
                            collection,
                            embeddings,
                            text_splitter: RecursiveCharacterTextSplitter,
                            source: str) -> int:
        """Process a single file and add documents with proper IDs to MongoDB"""
        try:
            # Load documents
            documents = load_document(file_path)
            if not documents:
                return 0
            
            # Split documents into chunks
            chunks = text_splitter.split_documents(documents)
            if not chunks:
                return 0
            
            # Prepare documents for MongoDB insertion
            documents_to_insert = []
            
            for i, chunk in enumerate(chunks):
                # Generate unique ID
                doc_id = generate_document_id(source, file_metadata.relative_path, i)
                
                # Update chunk metadata with file metadata
                chunk.metadata.update(file_metadata.to_dict())
                
                # Create embedding
                embedding = embeddings.embed_query(chunk.page_content)
                
                # Prepare document for MongoDB
                mongo_doc = {
                    "_id": doc_id,
                    "page_content": chunk.page_content,
                    "embedding": embedding,
                    "source": source,
                    "metadata": chunk.metadata
                }
                
                documents_to_insert.append(mongo_doc)
            
            # Insert documents into MongoDB
            if documents_to_insert:
                collection.insert_many(documents_to_insert)
            
            logging.info(f"Added {len(documents_to_insert)} chunks for file: {file_metadata.relative_path}")
            return len(documents_to_insert)
            
        except Exception as e:
            logging.error(f"Error processing file {file_path}: {e}")
            return 0
    
    try:
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        
        # Validate input path
        input_path = Path(file_or_folder_path)
        if not input_path.exists():
            logging.error(f"Path does not exist: {file_or_folder_path}")
            return False
        
        # Determine base path for relative path calculation
        base_path = input_path.parent if input_path.is_file() else input_path
        
        # Initialize components
        embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Get MongoDB collection
        collection = get_rag_collection()
        
        # Map collection_name to source identifier
        source = collection_name
        
        # Get existing file metadata based on operation mode
        existing_metadata = {}
        update_mode = (operation_mode == "update")
        
        if update_mode and not force_update:
            existing_metadata = get_existing_file_metadata(collection, source)
            logging.info(f"Found {len(existing_metadata)} files in existing collection for source: {source}")
        
        # Get files to process
        files_to_process = get_files_to_process(input_path)
        if not files_to_process:
            logging.warning("No files found to process")
            return True
        
        # Track processing statistics
        stats = {
            'total_files': len(files_to_process),
            'processed_files': 0,
            'updated_files': 0,
            'skipped_files': 0,
            'total_chunks': 0,
            'deleted_chunks': 0
        }
        
        # Process each file
        for file_path in files_to_process:

            # Only process directories named 'default' for splunk_addons source
            if source == "splunk_addons" and "default" not in str(file_path):
                continue

            try:
                # Create file metadata
                file_meta = FileMetadata(file_path, base_path)
                rel_path_str = str(file_meta.relative_path)
                
                # Check if file needs processing
                needs_processing = True
                if update_mode and not force_update:
                    if rel_path_str in existing_metadata:
                        if not file_meta.has_changed(existing_metadata[rel_path_str]):
                            logging.info(f"Skipping unchanged file: {rel_path_str}")
                            stats['skipped_files'] += 1
                            needs_processing = False
                
                if needs_processing:
                    # Delete existing chunks for this file if they exist
                    if update_mode:
                        deleted_count = delete_file_chunks(collection, source, rel_path_str)
                        stats['deleted_chunks'] += deleted_count
                        if deleted_count > 0:
                            stats['updated_files'] += 1
                    
                    # Process the file
                    chunk_count = process_file_with_ids(
                        file_path, base_path, file_meta, collection, embeddings, text_splitter, source
                    )
                    
                    if chunk_count > 0:
                        stats['processed_files'] += 1
                        stats['total_chunks'] += chunk_count
                        logging.info(f"Processed file: {rel_path_str} ({chunk_count} chunks)")
                    else:
                        logging.warning(f"No chunks created for file: {rel_path_str}")
            
            except Exception as e:
                logging.error(f"Error processing file {file_path}: {e}")
                continue
        
        # Handle deleted files (files that exist in collection but not on disk)
        if update_mode and existing_metadata:
            current_files = {str(FileMetadata(f, base_path).relative_path) for f in files_to_process}
            deleted_files = set(existing_metadata.keys()) - current_files
            
            for deleted_file in deleted_files:
                deleted_count = delete_file_chunks(collection, source, deleted_file)
                if deleted_count > 0:
                    stats['deleted_chunks'] += deleted_count
                    logging.info(f"Removed chunks for deleted file: {deleted_file} ({deleted_count} chunks)")
        
        # Log operation mode
        logging.info(f"Operation mode: {operation_mode}")
        if operation_mode == "create":
            logging.info("Creating embeddings from scratch")
        else:
            logging.info(f"Updating embeddings (force_update={force_update})")
        
        # Log final statistics
        logging.info("="*50)
        logging.info("PROCESSING SUMMARY")
        logging.info("="*50)
        logging.info(f"Operation: {operation_mode}")
        logging.info(f"Source: {source}")
        logging.info(f"Total files found: {stats['total_files']}")
        logging.info(f"Files processed: {stats['processed_files']}")
        logging.info(f"Files updated: {stats['updated_files']}")
        logging.info(f"Files skipped (unchanged): {stats['skipped_files']}")
        logging.info(f"Total chunks added: {stats['total_chunks']}")
        logging.info(f"Total chunks deleted: {stats['deleted_chunks']}")
        logging.info("="*50)
        
        return True
        
    except Exception as e:
        logging.error(f"Error in _process_embeddings: {e}")
        return False


def delete_collection(source: str) -> bool:
    """
    Delete all documents for a specific source.
    
    Args:
        source: Source identifier (e.g., 'splunk_addons', 'elastic_packages')
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        collection = get_rag_collection()
        result = collection.delete_many({"source": source})
        logging.info(f"Successfully deleted {result.deleted_count} documents for source: {source}")
        return True
    except Exception as e:
        logging.error(f"Error deleting source {source}: {e}")
        return False


def list_collection_files(source: str) -> Dict[str, Dict]:
    """
    List all files for a specific source with their metadata.
    
    Args:
        source: Source identifier
    
    Returns:
        Dict mapping file paths to their metadata
    """
    try:
        collection = get_rag_collection()
        return get_existing_file_metadata(collection, source)
    except Exception as e:
        logging.error(f"Error listing collection files: {e}")
        return {}


def list_sources() -> List[str]:
    """
    List all unique sources in the RAG collection.
    
    Returns:
        List of source names
    """
    try:
        collection = get_rag_collection()
        sources = collection.distinct("source")
        return sources
    except Exception as e:
        logging.error(f"Error listing sources: {e}")
        return []


def delete_file_from_collection(source: str, file_path: str) -> bool:
    """
    Remove a specific file and all its chunks from a source.
    
    Args:
        source: Source identifier
        file_path: Relative path of the file to remove
        
    Returns:
        bool: True if successful
    """
    try:
        collection = get_rag_collection()
        deleted_count = delete_file_chunks(collection, source, file_path)
        logging.info(f"Removed file '{file_path}' from source '{source}' ({deleted_count} chunks)")
        return deleted_count > 0
    except Exception as e:
        logging.error(f"Error removing file from collection: {e}")
        return False


def query_rag(
    source: str, 
    query: str, 
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    filter_metadata: Optional[Dict] = None
):
    """
    Query the RAG system using MongoDB Atlas Hybrid Search.
    
    Hybrid search combines:
    - Vector search (semantic similarity) 
    - Full-text search (keyword matching)
    
    Results are ranked using Reciprocal Rank Fusion (RRF).
    
    Args:
        source: Source identifier to filter results (e.g., 'splunk_addons', 'elastic_packages')
        query: Query string
        embedding_model: HuggingFace embedding model name
        filter_metadata: Optional additional metadata filters
        
    Returns:
        Tuple of (result, status_code, source_documents)
    """
    
    logging.info(f"Querying RAG with source '{source}' and query: {query}")

    try:
        # Initialize embeddings
        embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
        
        # Get MongoDB collection
        collection = get_rag_collection()
        
        # Get LLM configuration from settings
        global_settings = db_connection.query('global_settings', limit=1)
        
        if not global_settings:
            logging.error("No global settings found")
            return "Configuration error: No LLM endpoint configured", 500, []
        
        endpoint_id = global_settings.get("activeLlmEndpoint")
        llm_settings = db_connection.query('llms_settings', filter_dict={"id": endpoint_id}, limit=1)
        
        if not llm_settings:
            logging.error(f"No LLM settings found for endpoint: {endpoint_id}")
            return "Configuration error: Invalid LLM endpoint", 500, []
        
        url = llm_settings.get("url", "").split("/v1")[0] + "/v1"
        model_name = global_settings.get("activeLlm")
        
        # Initialize LLM
        llm = ChatOpenAI(
            base_url=url,
            api_key="EMPTY",
            model=model_name,
            temperature=0.2
        )
        
        # Prepare filter for source
        search_filter = {"source": source}
        if filter_metadata:
            search_filter.update(filter_metadata)
        
        # Create vector store with MongoDB
        vector_store = MongoDBAtlasVectorSearch(
            collection=collection,
            embedding=embeddings,
            index_name="vector_index",
            text_key="page_content",
            embedding_key="embedding"
        )
        
        # Create hybrid search retriever
        # This combines vector search (semantic) with full-text search (keyword matching)
        # using Reciprocal Rank Fusion (RRF) for ranking
        retriever = MongoDBAtlasHybridSearchRetriever(
            vectorstore=vector_store,
            search_index_name="fulltext_index",
            k=TOP_K,
            pre_filter=search_filter,
            # RRF parameters - adjust penalties to tune vector vs fulltext importance
            # Lower penalty = higher importance
            vector_penalty=60.0,      # Penalty for vector search ranking
            fulltext_penalty=60.0,    # Penalty for full-text search ranking
            vector_weight=1.0,        # Weight for vector search scores
            fulltext_weight=1.0,      # Weight for full-text search scores
        )
        
        # Create QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )

        result = qa_chain.invoke({"query": query})

        logging.info(f"Answer: {result['result']}")
        logging.info(f"Source documents:")
        for i, doc in enumerate(result['source_documents']):
            logging.info(f"\nDocument {i+1}:")
            logging.info(f"Content: {doc.page_content[:100]}...")
            if hasattr(doc, 'metadata'):
                logging.info(f"Source: {doc.metadata}")

        return result["result"], 200, result["source_documents"]
    
    except Exception as e:
        logging.error(f"Error querying RAG: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return f"Error: {str(e)}", 500, []
