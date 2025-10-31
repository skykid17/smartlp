"""
Database connection and basic operations for SmartSOC.
"""

import logging
from typing import Optional, Dict, List, Any, Union
from pymongo import MongoClient, DESCENDING, ASCENDING
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, OperationFailure

from config.settings import config

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Custom exception for database operations."""
    pass


class DatabaseConnection:
    """Manages MongoDB connections and provides basic CRUD operations."""
    
    def __init__(self):
        """Initialize database connection."""
        self._client: Optional[MongoClient] = None
        self._databases: Dict[str, Any] = {}
        self._collections: Dict[str, Collection] = {}
        self._connect()
    
    def _connect(self) -> None:
        """Establish connection to MongoDB."""
        try:
            self._client = MongoClient(config.database.mongo_url)
            # Test connection
            self._client.admin.command('ismaster')
            logger.info("Successfully connected to MongoDB")
            self._initialize_collections()
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise DatabaseError(f"Database connection failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            raise DatabaseError(f"Database initialization error: {e}")
    
    def _initialize_collections(self) -> None:
        """Initialize database collections."""
        try:
            # Parser database
            parser_db = self._client[config.database.parser_db_name]
            self._collections['parser_entries'] = parser_db[config.database.parser_entries_collection]
            self._collections['prefix_entries'] = parser_db['prefix_entries']  # Add prefix collection
            
            # Settings database
            settings_db = self._client[config.database.settings_db_name]
            self._collections['global_settings'] = settings_db[config.database.global_settings_collection]
            self._collections['llms_settings'] = settings_db[config.database.llms_settings_collection]
            self._collections['siems_settings'] = settings_db[config.database.siems_settings_collection]
            
            # MITRE database
            mitre_db = self._client[config.database.mitre_db_name]
            self._collections['sigma_rules'] = mitre_db[config.database.sigma_rules_collection]
            self._collections['splunk_rules'] = mitre_db[config.database.splunk_rules_collection]
            self._collections['elastic_rules'] = mitre_db[config.database.elastic_rules_collection]
            self._collections['secops_rules'] = mitre_db[config.database.secops_rules_collection]
            
            # MITRE Techniques database
            mitre_tech_db = self._client[config.database.mitre_tech_db_name]
            self._collections['mitre_techniques'] = mitre_tech_db[config.database.mitre_techniques_collection]
            
            logger.info("Database collections initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize collections: {e}")
            raise DatabaseError(f"Collection initialization failed: {e}")
    
    def get_collection(self, collection_name: str) -> Collection:
        """Get a collection by name.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            MongoDB collection object
            
        Raises:
            DatabaseError: If collection doesn't exist
        """
        if collection_name not in self._collections:
            raise DatabaseError(f"Collection '{collection_name}' not found")
        return self._collections[collection_name]
    
    def query(self, collection_name: str, filter_dict: Optional[Dict] = None, 
              projection: Optional[Dict] = None, skip: int = 0, limit: int = 0, 
              sort: Optional[List] = None, **kwargs) -> Union[Dict, List]:
        """Execute a query on a collection.
        
        Args:
            collection_name: Name of the collection
            filter_dict: MongoDB filter dictionary
            projection: Fields to include/exclude
            skip: Number of documents to skip
            limit: Maximum number of documents to return (0 = no limit)
            sort: Sort criteria
            **kwargs: Additional query options
            
        Returns:
            Query results (single document if limit=1, cursor otherwise)
        """
        try:
            collection = self.get_collection(collection_name)
            
            if limit == 1:
                return collection.find_one(filter_dict, projection, skip=skip, sort=sort, **kwargs)
            else:
                cursor = collection.find(filter_dict, projection, skip=skip, limit=limit, sort=sort, **kwargs)
                return list(cursor)
        except Exception as e:
            logger.error(f"Query failed on collection '{collection_name}': {e}")
            raise DatabaseError(f"Query operation failed: {e}")
    
    def update_one(self, collection_name: str, filter_dict: Dict, update_dict: Dict, **kwargs) -> bool:
        """Update a single document.
        
        Args:
            collection_name: Name of the collection
            filter_dict: Filter to match documents
            update_dict: Update operations
            **kwargs: Additional update options
            
        Returns:
            True if document was modified, False otherwise
        """
        try:
            collection = self.get_collection(collection_name)
            result = collection.update_one(filter_dict, update_dict, **kwargs)
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Update failed on collection '{collection_name}': {e}")
            raise DatabaseError(f"Update operation failed: {e}")
    
    def update_many(self, collection_name: str, filter_dict: Dict, update_dict: Dict, **kwargs) -> int:
        """Update multiple documents.
        
        Args:
            collection_name: Name of the collection
            filter_dict: Filter to match documents
            update_dict: Update operations
            **kwargs: Additional update options
            
        Returns:
            Number of documents modified
        """
        try:
            collection = self.get_collection(collection_name)
            result = collection.update_many(filter_dict, update_dict, **kwargs)
            return result.modified_count
        except Exception as e:
            logger.error(f"Update many failed on collection '{collection_name}': {e}")
            raise DatabaseError(f"Update many operation failed: {e}")
    
    def insert_one(self, collection_name: str, document: Dict, **kwargs) -> str:
        """Insert a single document.
        
        Args:
            collection_name: Name of the collection
            document: Document to insert
            **kwargs: Additional insert options
            
        Returns:
            ID of inserted document
        """
        try:
            collection = self.get_collection(collection_name)
            result = collection.insert_one(document, **kwargs)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Insert failed on collection '{collection_name}': {e}")
            raise DatabaseError(f"Insert operation failed: {e}")
    
    def delete_one(self, collection_name: str, filter_dict: Dict, **kwargs) -> bool:
        """Delete a single document.
        
        Args:
            collection_name: Name of the collection
            filter_dict: Filter to match document
            **kwargs: Additional delete options
            
        Returns:
            True if document was deleted, False otherwise
        """
        try:
            collection = self.get_collection(collection_name)
            result = collection.delete_one(filter_dict, **kwargs)
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Delete failed on collection '{collection_name}': {e}")
            raise DatabaseError(f"Delete operation failed: {e}")
    
    def delete_many(self, collection_name: str, filter_dict: Dict, **kwargs) -> int:
        """Delete multiple documents.
        
        Args:
            collection_name: Name of the collection
            filter_dict: Filter to match documents
            **kwargs: Additional delete options
            
        Returns:
            Number of documents deleted
        """
        try:
            collection = self.get_collection(collection_name)
            result = collection.delete_many(filter_dict, **kwargs)
            return result.deleted_count
        except Exception as e:
            logger.error(f"Delete many failed on collection '{collection_name}': {e}")
            raise DatabaseError(f"Delete many operation failed: {e}")
    
    def count_documents(self, collection_name: str, filter_dict: Optional[Dict] = None, **kwargs) -> int:
        """Count documents in a collection.
        
        Args:
            collection_name: Name of the collection
            filter_dict: Filter to match documents
            **kwargs: Additional count options
            
        Returns:
            Number of matching documents
        """
        try:
            collection = self.get_collection(collection_name)
            return collection.count_documents(filter_dict or {}, **kwargs)
        except Exception as e:
            logger.error(f"Count failed on collection '{collection_name}': {e}")
            raise DatabaseError(f"Count operation failed: {e}")
    
    def get_distinct_values(self, collection_name: str, field: str, 
                           filter_dict: Optional[Dict] = None, **kwargs) -> List:
        """Get distinct values for a field.
        
        Args:
            collection_name: Name of the collection
            field: Field name to get distinct values for
            filter_dict: Filter to match documents
            **kwargs: Additional distinct options
            
        Returns:
            List of distinct values
        """
        try:
            collection = self.get_collection(collection_name)
            return collection.distinct(field, filter_dict, **kwargs)
        except Exception as e:
            logger.error(f"Distinct failed on collection '{collection_name}': {e}")
            raise DatabaseError(f"Distinct operation failed: {e}")
    
    def close(self) -> None:
        """Close database connection."""
        if self._client:
            self._client.close()
            logger.info("Database connection closed")


# Global database instance
db_connection = DatabaseConnection()

# Backward compatibility - expose constants and functions for existing code
DESCENDING = DESCENDING
ASCENDING = ASCENDING

def db_query(collection, filter_dict=None, projection=None, skip=0, limit=0, sort=None, **kwargs):
    """Backward compatibility wrapper for query operations."""
    # Extract collection name from collection object if needed
    if hasattr(collection, 'name'):
        collection_name = collection.name
    else:
        # Map collection objects to names for backward compatibility
        collection_mapping = {
            'parser_entries': 'parser_entries',
            'global_settings': 'global_settings',
            'llms_settings': 'llms_settings',
            'siems_settings': 'siems_settings',
            'sigma_rules': 'sigma_rules',
            'splunk_rules': 'splunk_rules',
            'elastic_rules': 'elastic_rules',
            'secops_rules': 'secops_rules',
            'mitre_techniques': 'mitre_techniques',
        }
        collection_name = str(collection)
        for key in collection_mapping:
            if key in collection_name:
                collection_name = key
                break
    
    return db_connection.query(collection_name, filter_dict, projection, skip, limit, sort, **kwargs)

def db_update_one(collection, filter_dict, update_dict, **kwargs):
    """Backward compatibility wrapper for update_one operations."""
    collection_name = _get_collection_name(collection)
    return db_connection.update_one(collection_name, filter_dict, update_dict, **kwargs)

def db_update_many(collection, filter_dict, update_dict, **kwargs):
    """Backward compatibility wrapper for update_many operations."""
    collection_name = _get_collection_name(collection)
    return db_connection.update_many(collection_name, filter_dict, update_dict, **kwargs)

def db_insert_one(collection, document, **kwargs):
    """Backward compatibility wrapper for insert_one operations."""
    collection_name = _get_collection_name(collection)
    return db_connection.insert_one(collection_name, document, **kwargs)

def db_delete_one(collection, filter_dict, **kwargs):
    """Backward compatibility wrapper for delete_one operations."""
    collection_name = _get_collection_name(collection)
    return db_connection.delete_one(collection_name, filter_dict, **kwargs)

def db_delete_many(collection, filter_dict, **kwargs):
    """Backward compatibility wrapper for delete_many operations."""
    collection_name = _get_collection_name(collection)
    return db_connection.delete_many(collection_name, filter_dict, **kwargs)

def db_count(collection, filter_dict, **kwargs):
    """Backward compatibility wrapper for count operations."""
    collection_name = _get_collection_name(collection)
    return db_connection.count_documents(collection_name, filter_dict, **kwargs)

def get_unique_values(collection, field, filter_dict=None, **kwargs):
    """Backward compatibility wrapper for distinct operations."""
    collection_name = _get_collection_name(collection)
    return db_connection.get_distinct_values(collection_name, field, filter_dict, **kwargs)

def _get_collection_name(collection):
    """Helper to extract collection name for backward compatibility."""
    if hasattr(collection, 'name'):
        return collection.name
    
    # Map common collection references
    collection_mapping = {
        'mongo_parser_entries': 'parser_entries',
        'mongo_settings_global': 'global_settings',
        'mongo_settings_llms': 'llms_settings',
        'mongo_settings_siems': 'siems_settings',
        'mongo_collection_sigmarules': 'sigma_rules',
        'mongo_collection_splunk': 'splunk_rules',
        'mongo_collection_elastic': 'elastic_rules',
        'mongo_collection_secops': 'secops_rules',
        'mongo_collection_mitretech': 'mitre_techniques',
    }
    
    collection_str = str(collection)
    for key, value in collection_mapping.items():
        if key in collection_str:
            return value
    
    # Default fallback
    return 'parser_entries'

# Expose collections for backward compatibility
mongo_parser_entries = db_connection.get_collection('parser_entries')
mongo_settings_global = db_connection.get_collection('global_settings')
mongo_settings_llms = db_connection.get_collection('llms_settings')
mongo_settings_siems = db_connection.get_collection('siems_settings')
mongo_collection_sigmarules = db_connection.get_collection('sigma_rules')
mongo_collection_splunk = db_connection.get_collection('splunk_rules')
mongo_collection_elastic = db_connection.get_collection('elastic_rules')
mongo_collection_secops = db_connection.get_collection('secops_rules')
mongo_collection_mitretech = db_connection.get_collection('mitre_techniques')