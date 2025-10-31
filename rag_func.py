import db
import utility
import os
import sys
import logging
import csv
import json
import hashlib
import datetime
from pathlib import Path
from typing import List, Dict, Set
import yaml
import chromadb
from langchain.chains import RetrievalQA
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_community.document_loaders import JSONLoader, TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

TOP_K = 3

ANONYMIZED_TELEMETRY=False

persistent_client = chromadb.PersistentClient(
    path="./rag/chroma", 
    settings=chromadb.Settings(
        anonymized_telemetry=False,
        allow_reset=True,
        is_persistent=True
    )
)

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

def generate_document_id(relative_path: Path, chunk_index: int) -> str:
    """Generate consistent document ID based on file path and chunk index"""
    return f"{str(relative_path).replace(os.sep, '/')}#{chunk_index}"

def extract_file_path_from_id(doc_id: str) -> str:
    """Extract file path from document ID"""
    return doc_id.split('#')[0]

def get_existing_file_metadata(vectorstore: Chroma, collection_name: str) -> Dict[str, Dict]:
    """Get metadata for all files currently in the collection"""
    try:
        # Get all documents to extract file metadata
        all_docs = vectorstore.get()
        file_metadata = {}
        
        if all_docs and 'metadatas' in all_docs and all_docs['metadatas']:
            for metadata in all_docs['metadatas']:
                if metadata and 'relative_path' in metadata:
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

def delete_file_chunks(vectorstore: Chroma, relative_path: str):
    """Delete all chunks for a specific file"""
    try:
        # Get all document IDs for this file
        file_path_normalized = relative_path.replace(os.sep, '/')
        all_docs = vectorstore.get()
        
        if all_docs and 'ids' in all_docs and all_docs['ids']:
            ids_to_delete = [
                doc_id for doc_id in all_docs['ids'] 
                if doc_id.startswith(f"{file_path_normalized}#")
            ]
            
            if ids_to_delete:
                vectorstore.delete(ids=ids_to_delete)
                logging.info(f"Deleted {len(ids_to_delete)} chunks for file: {relative_path}")
                return len(ids_to_delete)
        
        return 0
    except Exception as e:
        logging.error(f"Error deleting chunks for file {relative_path}: {e}")
        return 0


def create_collection_mapping(collection_name: str) -> Dict[str, List[str]]:
    """
    Create a mapping of file paths to their document IDs in the collection.
    
    Args:
        collection_name: Name of the collection
        
    Returns:
        Dict mapping file paths to lists of document IDs
    """
    try:
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vectorstore = Chroma(
            client=persistent_client,
            embedding_function=embeddings,
            collection_name=collection_name
        )
        
        # Get all documents
        all_docs = vectorstore.get()
        file_to_ids = {}
        
        if all_docs and 'ids' in all_docs and all_docs['ids']:
            for doc_id in all_docs['ids']:
                file_path = extract_file_path_from_id(doc_id)
                if file_path not in file_to_ids:
                    file_to_ids[file_path] = []
                file_to_ids[file_path].append(doc_id)
        
        return file_to_ids
    
    except Exception as e:
        logging.error(f"Error creating collection mapping: {e}")
        return {}

def save_collection_mapping(collection_name: str, 
                          mapping: Dict[str, List[str]], 
                          output_file: str = None) -> bool:
    """
    Save collection mapping to a JSON file.
    
    Args:
        collection_name: Name of the collection
        mapping: File to IDs mapping
        output_file: Output file path (optional)
        
    Returns:
        bool: True if successful
    """
    try:
        if output_file is None:
            output_file = f"./rag/chroma/collection_mapping_{collection_name}.json"
        
        mapping_data = {
            "collection_name": collection_name,
            "generated_at": datetime.datetime.now().isoformat(),
            "total_files": len(mapping),
            "total_chunks": sum(len(ids) for ids in mapping.values()),
            "file_mappings": mapping
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mapping_data, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Collection mapping saved to: {output_file}")
        return True
    
    except Exception as e:
        logging.error(f"Error saving collection mapping: {e}")
        return False

def load_collection_mapping(collection_name: str, 
                          input_file: str = None) -> Dict[str, List[str]]:
    """
    Load collection mapping from a JSON file.
    
    Args:
        collection_name: Name of the collection
        input_file: Input file path (optional)
        
    Returns:
        Dict mapping file paths to lists of document IDs
    """
    try:
        if input_file is None:
            input_file = f"./rag/chroma/collection_mapping_{collection_name}.json"
        
        with open(input_file, 'r', encoding='utf-8') as f:
            mapping_data = json.load(f)
        
        return mapping_data.get("file_mappings", {})
    
    except Exception as e:
        logging.error(f"Error loading collection mapping: {e}")
        return {}

def create_embeddings(
    file_or_folder_path: str,
    collection_name: str,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    max_batch_size: int = 5461
) -> bool:
    """
    Create embeddings for files in a clean collection.
    
    Args:
        file_or_folder_path: Path to file or folder to process
        collection_name: Name of the ChromaDB collection to create
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
        client=persistent_client,
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
        collection_name: Name of the ChromaDB collection to update
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
        client=persistent_client,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        max_batch_size=max_batch_size,
        operation_mode="update",
        force_update=force_update
    )

def delete_collection(
    collection_name: str
) -> bool:
    """
    Delete an entire collection.
    
    Args:
        collection_name: Name of the collection to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vectorstore = Chroma(
            client=persistent_client,
            embedding_function=embeddings,
            collection_name=collection_name
        )
        
        # Delete the collection data        
        vectorstore.delete_collection()
        logging.info(f"Successfully deleted collection: {collection_name}")
        
        # Also remove mapping file if it exists
        mapping_file = f"./rag/collection_mapping_{collection_name}.json"
        if os.path.exists(mapping_file):
            os.remove(mapping_file)
            logging.info(f"Removed mapping file: {mapping_file}")
        
        return True
    
    except Exception as e:
        logging.error(f"Error deleting collection {collection_name}: {e}")
        return False

def _process_embeddings(
    file_or_folder_path: str,
    collection_name: str,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    client: chromadb.PersistentClient = persistent_client,
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
        collection_name: Name of the ChromaDB collection
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
                            vectorstore: Chroma,
                            text_splitter: RecursiveCharacterTextSplitter) -> int:
        """Process a single file and add documents with proper IDs"""
        try:
            # Load documents
            documents = load_document(file_path)
            if not documents:
                return 0
            
            # Split documents into chunks
            chunks = text_splitter.split_documents(documents)
            if not chunks:
                return 0
            
            # Add file metadata to each chunk and assign IDs
            documents_to_add = []
            ids_to_add = []
            
            for i, chunk in enumerate(chunks):
                # Generate unique ID
                doc_id = generate_document_id(file_metadata.relative_path, i)
                
                # Add file metadata to chunk metadata
                chunk.metadata.update(file_metadata.to_dict())
                
                documents_to_add.append(chunk)
                ids_to_add.append(doc_id)
            
            # Add documents to vectorstore with IDs
            vectorstore.add_documents(documents_to_add, ids=ids_to_add)
            
            logging.info(f"Added {len(documents_to_add)} chunks for file: {file_metadata.relative_path}")
            return len(documents_to_add)
            
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
        
        # Initialize vectorstore
        vectorstore = Chroma(
            client=persistent_client,
            embedding_function=embeddings,
            collection_name=collection_name
        )
        
        # Get existing file metadata based on operation mode
        existing_metadata = {}
        update_mode = (operation_mode == "update")
        
        if update_mode and not force_update:
            existing_metadata = get_existing_file_metadata(vectorstore, collection_name)
            logging.info(f"Found {len(existing_metadata)} files in existing collection")
        
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

            # Only process directories named 'default' for splunk_addons collection
            if collection_name == "splunk_addons" and "default" not in str(file_path):
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
                        deleted_count = delete_file_chunks(vectorstore, rel_path_str)
                        stats['deleted_chunks'] += deleted_count
                        if deleted_count > 0:
                            stats['updated_files'] += 1
                    
                    # Process the file
                    chunk_count = process_file_with_ids(
                        file_path, base_path, file_meta, vectorstore, text_splitter
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
                deleted_count = delete_file_chunks(vectorstore, deleted_file)
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
        logging.info(f"Total files found: {stats['total_files']}")
        logging.info(f"Files processed: {stats['processed_files']}")
        logging.info(f"Files updated: {stats['updated_files']}")
        logging.info(f"Files skipped (unchanged): {stats['skipped_files']}")
        logging.info(f"Total chunks added: {stats['total_chunks']}")
        logging.info(f"Total chunks deleted: {stats['deleted_chunks']}")
        logging.info(f"Collection: {collection_name}")
        logging.info("="*50)
        
        # Generate and save collection mapping
        try:
            mapping = create_collection_mapping(collection_name)
            save_collection_mapping(collection_name, mapping)
            logging.info(f"Collection mapping saved for {len(mapping)} files")
        except Exception as e:
            logging.warning(f"Could not generate collection mapping: {e}")
        
        return True
        
    except Exception as e:
        logging.error(f"Error in create_or_update_embeddings: {e}")
        return False

def list_collection_files(collection_name: str) -> Dict[str, Dict]:
    """
    List all files in a collection with their metadata.
    
    Returns:
        Dict mapping file paths to their metadata
    """
    try:
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vectorstore = Chroma(
            client=persistent_client,
            embedding_function=embeddings,
            collection_name=collection_name
        )
        
        return get_existing_file_metadata(vectorstore, collection_name)
    
    except Exception as e:
        logging.error(f"Error listing collection files: {e}")
        return {}

def list_collections() -> List[str]:
    """
    List all collections in the ChromaDB client.
    
    Returns:
        List of collection names
    """
    try:
        return [collection.name for collection in list(persistent_client.list_collections())]
    except Exception as e:
        print(f"Error listing collections: {e}")
        return []

def delete_file_from_collection(collection_name: str, 
                               file_path: str) -> bool:
    """
    Remove a specific file and all its chunks from a collection.
    
    Args:
        collection_name: Name of the collection
        file_path: Relative path of the file to remove
        
    Returns:
        bool: True if successful
    """
    try:
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vectorstore = Chroma(
            client=persistent_client,
            embedding_function=embeddings,
            collection_name=collection_name
        )
        
        deleted_count = delete_file_chunks(vectorstore, file_path)
        logging.info(f"Removed file '{file_path}' from collection '{collection_name}' ({deleted_count} chunks)")
        
        return deleted_count > 0
    
    except Exception as e:
        logging.error(f"Error removing file from collection: {e}")
        return False

def query_rag(collection: str, 
              query: str, 
              embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2", 
              persist_directory: str = "./rag/chroma"):
    
    logging.info(f"Querying RAG collection '{collection}' with query: {query}")

    embeddings = HuggingFaceEmbeddings(model_name=embedding_model)

    vectorstore = Chroma(
        client=persistent_client,
        embedding_function=embeddings,
        collection_name=collection
    )
    endpoint_id = utility.get_settings().get("activeLlmEndpoint")
    url = db.db_query(db.mongo_settings_llms, filter={"id": endpoint_id}, limit=1).get("url")
    url = url.split("/v1")[0] + "/v1"

    llm = ChatOpenAI(
        base_url=url,
        api_key="EMPTY",
        model=utility.get_settings().get("activeLlm"),
        temperature=0.2
    )
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": TOP_K}),
        return_source_documents=True
    )

    result = qa_chain.invoke({"query": query})

    utility.log_message('log', f"Answer: {result['result']}")
    utility.log_message('log', f"Source documents:")
    for i, doc in enumerate(result['source_documents']):
        utility.log_message('log', f"\nDocument {i+1}:")
        utility.log_message('log', f"Content: {doc.page_content[:100]}...")
        if hasattr(doc, 'metadata'):
            utility.log_message('log', f"Source: {doc.metadata}")

    return result["result"], 200, result["source_documents"]


# ============================= Example usage ========================================

#if __name__ == "__main__":
    # Create initial embeddings (clean slate)
    # success = create_embeddings("./rag/repos/splunk_repo", "splunk_addons")

    # Update only changed files (efficient incremental updates)
    # success = update_embeddings("./rag/repos/splunk_repo", "splunk_addons")

    # Force update all files
    # success = update_embeddings("./rag/repos/splunk_repo", "splunk_addons", force_update=True)

    # Delete entire collection
    # success = delete_collection("splunk_addons")

    # List files in collection
    # files = list_collection_files("splunk_addons")
    # for file_path, metadata in files.items():
    #     print(f"File: {file_path}")
    #     print(f"  Last modified: {metadata['modification_time']}")
    #     print(f"  Hash: {metadata['file_hash'][:16]}...")
    #     print(f"  Size: {metadata['file_size']} bytes")

    # Create and save collection mapping
    # mapping = create_collection_mapping("splunk_addons")
    # save_collection_mapping("splunk_addons", mapping)

    # Load existing mapping
    # mapping = load_collection_mapping("splunk_addons")
    # for file_path, doc_ids in mapping.items():
    #     print(f"File: {file_path}")
    #     print(f"  Document IDs: {doc_ids}")

    # Print collection summary to console
    # print_collection_summary("splunk_addons")

    # Remove specific file from collection
    # success = delete_file_from_collection("splunk_addons", "configs/cisco.yaml")

    # query = '''Given a regular expression, replace field names denoted by (?P<fieldname>) with elastic common schema field names. Return the full regular expression with modified field names. The regular expression is: ^<(?P<priority>\d+)>(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(?P<hostname>[\w\-.]+)\s+\d+,(?P<event_time>[\d\/:\s]*),(?P<generated_time>[\d\/:\s]*),(?P<process>\S+),(?P<pid>\d+),(?P<content>.+?)$'''
    # Query the RAG (unchanged)
    # result, status, sources = query_rag("elastic_fields", query)