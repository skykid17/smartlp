"""
SIEM connection services for SmartSOC application.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import logging

from elasticsearch import Elasticsearch
import splunklib.client as splunk_client
import splunklib.results as splunk_results

from config.settings import config
from .base import BaseService


class SIEMConnectionError(Exception):
    """Exception for SIEM connection errors."""
    pass


class BaseSIEMService(ABC):
    """Abstract base class for SIEM services."""
    
    def __init__(self, service_name: str):
        """Initialize SIEM service.
        
        Args:
            service_name: Name of the SIEM service
        """
        self.service_name = service_name
        self.logger = logging.getLogger(f"smartsoc.siem.{service_name}")
        self._connection = None
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to SIEM.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test SIEM connection.
        
        Returns:
            True if connection is working, False otherwise
        """
        pass
    
    @abstractmethod
    def search(self, query: str, index: str, max_results: int = 100) -> Tuple[List[Dict], Optional[str]]:
        """Execute search query.
        
        Args:
            query: Search query
            index: Index/sourcetype to search
            max_results: Maximum number of results
            
        Returns:
            Tuple of (results, error_message)
        """
        pass
    
    def disconnect(self) -> None:
        """Disconnect from SIEM."""
        if self._connection:
            try:
                if hasattr(self._connection, 'close'):
                    self._connection.close()
                self._connection = None
                self.logger.info(f"Disconnected from {self.service_name}")
            except Exception as e:
                self.logger.error(f"Error disconnecting from {self.service_name}: {e}")


class SplunkService(BaseSIEMService):
    """Splunk SIEM service."""
    
    def __init__(self):
        """Initialize Splunk service."""
        super().__init__("splunk")
        self.config = config.splunk
    
    def connect(self) -> bool:
        """Connect to Splunk.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self._connection = splunk_client.connect(
                host=self.config.host,
                port=self.config.port,
                username=self.config.username,
                password=self.config.password
            )
            self.logger.info("Successfully connected to Splunk")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Splunk: {e}")
            self._connection = None
            return False
    
    def test_connection(self) -> bool:
        """Test Splunk connection.
        
        Returns:
            True if connection is working, False otherwise
        """
        if not self._connection:
            return self.connect()
        
        try:
            # Test with a simple search
            self._connection.info()
            return True
        except Exception as e:
            self.logger.error(f"Splunk connection test failed: {e}")
            return False
    
    def search(self, query: str, index: str, max_results: int = 100) -> Tuple[List[Dict], Optional[str]]:
        """Execute Splunk search.
        
        Args:
            query: Splunk search query
            index: Splunk index to search
            max_results: Maximum number of results
            
        Returns:
            Tuple of (results, error_message)
        """
        if not self._connection and not self.connect():
            return [], "Failed to connect to Splunk"
        
        try:
            # Construct search query
            search_query = f"search index={index} {query} | head {max_results}"
            
            # Execute search
            job = self._connection.jobs.create(search_query)
            
            # Wait for search to complete
            while not job.is_done():
                pass
            
            # Get results
            results = []
            for result in splunk_results.ResultsReader(job.results()):
                if isinstance(result, dict):
                    results.append(result)
            
            self.logger.info(f"Splunk search returned {len(results)} results")
            return results, None
            
        except Exception as e:
            error_msg = f"Splunk search failed: {e}"
            self.logger.error(error_msg)
            return [], error_msg
    
    def get_indexes(self) -> List[str]:
        """Get list of available Splunk indexes.
        
        Returns:
            List of index names
        """
        if not self._connection and not self.connect():
            return []
        
        try:
            indexes = []
            for index in self._connection.indexes:
                indexes.append(index.name)
            return indexes
        except Exception as e:
            self.logger.error(f"Failed to get Splunk indexes: {e}")
            return []


class ElasticsearchService(BaseSIEMService):
    """Elasticsearch SIEM service."""
    
    def __init__(self):
        """Initialize Elasticsearch service."""
        super().__init__("elasticsearch")
        self.config = config.elastic
        self.ssl_verified = False  # Track whether SSL verification is being used
    
    def connect(self) -> bool:
        """Connect to Elasticsearch.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # First try with certificate verification
            self._connection = Elasticsearch(
                self.config.host,
                ca_certs=self.config.cert_path,
                verify_certs=True,
                basic_auth=(self.config.username, self.config.password)
            )
            
            # Test connection
            if self._connection.ping():
                self.ssl_verified = True
                self.logger.info("Successfully connected to Elasticsearch with certificate verification")
                return True
            else:
                self.logger.warning("Elasticsearch ping failed with certificate verification")
                
        except Exception as e:
            self.logger.warning(f"Certificate verification failed: {e}")
            
        # If certificate verification fails, try without it (for self-signed certificates)
        try:
            self.logger.info("Attempting connection without certificate verification")
            self._connection = Elasticsearch(
                self.config.host,
                verify_certs=False,
                basic_auth=(self.config.username, self.config.password)
            )
            
            # Test connection
            if self._connection.ping():
                self.ssl_verified = False
                self.logger.info("Successfully connected to Elasticsearch without certificate verification")
                return True
            else:
                self.logger.error("Elasticsearch ping failed even without certificate verification")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to connect to Elasticsearch: {e}")
            self._connection = None
            self.ssl_verified = False
            return False
    
    def test_connection(self) -> bool:
        """Test Elasticsearch connection.
        
        Returns:
            True if connection is working, False otherwise
        """
        if not self._connection:
            return self.connect()
        
        try:
            return self._connection.ping()
        except Exception as e:
            self.logger.error(f"Elasticsearch connection test failed: {e}")
            return False
    
    def search(self, query: str, index: str, max_results: int = 100) -> Tuple[List[Dict], Optional[str]]:
        """Execute Elasticsearch search.
        
        Args:
            query: Elasticsearch query (JSON string or dict)
            index: Elasticsearch index pattern
            max_results: Maximum number of results
            
        Returns:
            Tuple of (results, error_message)
        """
        if not self._connection and not self.connect():
            return [], "Failed to connect to Elasticsearch"
        
        try:
            # Parse query if it's a string
            if isinstance(query, str):
                import json
                try:
                    query_dict = json.loads(query)
                except json.JSONDecodeError:
                    # Treat as simple query string
                    query_dict = {
                        "query": {
                            "query_string": {
                                "query": query
                            }
                        }
                    }
            else:
                query_dict = query
            
            # Add size limit
            query_dict["size"] = max_results
            
            # Execute search
            response = self._connection.search(
                index=index,
                body=query_dict
            )
            
            # Extract results
            results = []
            if 'hits' in response and 'hits' in response['hits']:
                for hit in response['hits']['hits']:
                    result = hit.get('_source', {})
                    result.update({
                        '_index': hit.get('_index'),
                        '_id': hit.get('_id'),
                        '_score': hit.get('_score')
                    })
                    results.append(result)
            
            self.logger.info(f"Elasticsearch search returned {len(results)} results")
            return results, None
            
        except Exception as e:
            error_msg = f"Elasticsearch search failed: {e}"
            self.logger.error(error_msg)
            return [], error_msg
    
    def get_indices(self) -> List[str]:
        """Get list of available Elasticsearch indices.
        
        Returns:
            List of index names
        """
        if not self._connection and not self.connect():
            return []
        
        try:
            indices_info = self._connection.cat.indices(format='json')
            return [idx['index'] for idx in indices_info]
        except Exception as e:
            self.logger.error(f"Failed to get Elasticsearch indices: {e}")
            return []


class SIEMServiceFactory:
    """Factory for creating SIEM service instances."""
    
    _services = {
        'splunk': SplunkService,
        'elastic': ElasticsearchService,
        'elasticsearch': ElasticsearchService,
    }
    
    @classmethod
    def create_service(cls, siem_type: str) -> Optional[BaseSIEMService]:
        """Create SIEM service instance.
        
        Args:
            siem_type: Type of SIEM ('splunk', 'elastic', 'elasticsearch')
            
        Returns:
            SIEM service instance or None if type not supported
        """
        service_class = cls._services.get(siem_type.lower())
        if service_class:
            return service_class()
        return None
    
    @classmethod
    def get_service(cls, siem_type: str) -> Optional[BaseSIEMService]:
        """Get SIEM service instance (alias for create_service for backward compatibility).
        
        Args:
            siem_type: Type of SIEM ('splunk', 'elastic', 'elasticsearch')
            
        Returns:
            SIEM service instance or None if type not supported
        """
        return cls.create_service(siem_type)
    
    @classmethod
    def get_supported_siems(cls) -> List[str]:
        """Get list of supported SIEM types.
        
        Returns:
            List of supported SIEM type names
        """
        return list(cls._services.keys())


# Global SIEM service instances
splunk_service = SplunkService()
elasticsearch_service = ElasticsearchService()