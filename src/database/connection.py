"""Database connection and basic operations for SmartSOC."""

import logging
import threading
import time
from typing import Optional, Dict, List, Any, Union
from pymongo import MongoClient, DESCENDING, ASCENDING
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure

from config.settings import config

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Custom exception for database operations."""
    pass


DEFAULT_MAX_ATTEMPTS = getattr(config.database, "connection_attempts", 3)
DEFAULT_BACKOFF_SECONDS = getattr(config.database, "connection_backoff_seconds", 1.0)
HEALTH_CHECK_INTERVAL = getattr(config.database, "connection_health_interval", 30.0)


class DatabaseConnection:
    """Manages MongoDB connections and provides basic CRUD operations."""

    def __init__(self):
        self._client: Optional[MongoClient] = None
        self._databases: Dict[str, Any] = {}
        self._collections: Dict[str, Collection] = {}
        self._last_health_check: float = 0.0

    def connect(self, max_attempts: int = DEFAULT_MAX_ATTEMPTS,
                backoff_seconds: float = DEFAULT_BACKOFF_SECONDS) -> None:
        """Attempt to establish a connection with retry/backoff."""
        last_error: Optional[Exception] = None
        for attempt in range(1, max_attempts + 1):
            try:
                self._connect_once()
                return
            except DatabaseError as exc:
                last_error = exc
                if attempt == max_attempts:
                    break
                sleep_for = backoff_seconds * attempt
                logger.warning(
                    "MongoDB connection attempt %s/%s failed: %s. Retrying in %.1fs",
                    attempt, max_attempts, exc, sleep_for
                )
                time.sleep(max(sleep_for, 0))

        if last_error:
            raise last_error

    def ensure_connection(self) -> None:
        """Ensure an active connection exists, reconnecting if needed."""
        if self._client is None:
            self.connect()
            return

        if not self.is_healthy():
            logger.warning("MongoDB health check failed; reconnecting")
            self.connect()

    def _connect_once(self) -> None:
        """Establish connection to MongoDB without retries."""
        self.close()
        try:
            self._client = MongoClient(
                config.database.mongo_url,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
            )
            self._client.admin.command('ping')
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
            self._collections['prefix_entries'] = parser_db['prefix_entries']

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
        """Get a collection by name."""
        self.ensure_connection()

        if collection_name not in self._collections:
            raise DatabaseError(f"Collection '{collection_name}' not found")
        return self._collections[collection_name]

    def query(self, collection_name: str, filter_dict: Optional[Dict] = None,
              projection: Optional[Dict] = None, skip: int = 0, limit: int = 0,
              sort: Optional[List] = None, **kwargs) -> Union[Dict, List]:
        """Execute a query on a collection."""
        try:
            collection = self.get_collection(collection_name)

            if limit == 1:
                return collection.find_one(filter_dict, projection, skip=skip, sort=sort, **kwargs)
            cursor = collection.find(filter_dict, projection, skip=skip, limit=limit, sort=sort, **kwargs)
            return list(cursor)
        except Exception as e:
            logger.error(f"Query failed on collection '{collection_name}': {e}")
            raise DatabaseError(f"Query operation failed: {e}")

    def update_one(self, collection_name: str, filter_dict: Dict, update_dict: Dict, **kwargs) -> bool:
        """Update a single document."""
        try:
            collection = self.get_collection(collection_name)
            result = collection.update_one(filter_dict, update_dict, **kwargs)
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Update failed on collection '{collection_name}': {e}")
            raise DatabaseError(f"Update operation failed: {e}")

    def update_many(self, collection_name: str, filter_dict: Dict, update_dict: Dict, **kwargs) -> int:
        """Update multiple documents."""
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

    def is_healthy(self) -> bool:
        """Return True if the current connection responds to ping."""
        if not self._client:
            return False

        now = time.monotonic()
        if now - self._last_health_check < HEALTH_CHECK_INTERVAL:
            return True

        try:
            self._client.admin.command('ping')
            self._last_health_check = now
            return True
        except Exception as exc:
            logger.warning(f"MongoDB health check failed: {exc}")
            return False
    
    def close(self) -> None:
        """Close database connection."""
        if self._client:
            try:
                self._client.close()
            finally:
                self._client = None
                self._collections.clear()
                logger.info("Database connection closed")


# Global database accessor helpers
_connection_lock = threading.Lock()
_db_connection_instance: Optional[DatabaseConnection] = None


def get_db_connection(force_refresh: bool = False) -> DatabaseConnection:
    """Return an initialized DatabaseConnection, lazily creating it."""
    global _db_connection_instance

    with _connection_lock:
        if _db_connection_instance is None:
            _db_connection_instance = DatabaseConnection()

        if force_refresh:
            _db_connection_instance.close()

        _db_connection_instance.ensure_connection()
        return _db_connection_instance


class _DatabaseConnectionProxy:
    """Proxy that defers attribute access until a connection is requested."""

    def __getattr__(self, item):
        return getattr(get_db_connection(), item)

    def __repr__(self) -> str:
        return "<LazyDatabaseConnectionProxy>"


db_connection = _DatabaseConnectionProxy()
