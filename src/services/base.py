"""
Base service classes for SmartSOC application.
"""

from abc import ABC, abstractmethod
import logging
from typing import Dict, Any, List, Optional, Tuple

from database.connection import db_connection


class BaseService(ABC):
    """Base class for all service classes."""
    
    def __init__(self, service_name: str):
        """Initialize base service.
        
        Args:
            service_name: Name of the service for logging
        """
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)


class CRUDService(BaseService):
    """Base CRUD service class."""
    
    def __init__(self, service_name: str, collection_name: str):
        """Initialize CRUD service.
        
        Args:
            service_name: Name of the service
            collection_name: Name of the database collection
        """
        super().__init__(service_name)
        self.collection_name = collection_name
    
    def create(self, data: Dict[str, Any]) -> str:
        """Create a new record.
        
        Args:
            data: Data to create
            
        Returns:
            ID of created record
            
        Raises:
            ServiceError: If creation fails
        """
        try:
            record_id = db_connection.insert_one(self.collection_name, data)
            self.logger.info("Created record with ID: %s", record_id)
            return record_id
        except Exception as e:
            self.logger.exception("Failed to create record")
            raise ServiceError(f"Creation failed: {e}")
    
    def get_by_id(self, record_id: str, projection: Optional[Dict] = None) -> Optional[Dict]:
        """Get record by ID.
        
        Args:
            record_id: Record ID
            projection: Fields to include/exclude
            
        Returns:
            Record data or None if not found
        """
        try:
            return db_connection.query(
                self.collection_name, 
                {'id': record_id}, 
                projection=projection, 
                limit=1
            )
        except Exception as e:
            self.logger.exception("Failed to get record by ID: %s", record_id)
            return None
    
    def get_all(self, filter_dict: Optional[Dict] = None, 
                projection: Optional[Dict] = None, skip: int = 0, 
                limit: int = 0, sort: Optional[List] = None) -> List[Dict]:
        """Get all records matching criteria.
        
        Args:
            filter_dict: Filter criteria
            projection: Fields to include/exclude
            skip: Number of records to skip
            limit: Maximum number of records
            sort: Sort criteria
            
        Returns:
            List of matching records
        """
        try:
            return db_connection.query(
                self.collection_name, 
                filter_dict, 
                projection=projection,
                skip=skip,
                limit=limit,
                sort=sort
            )
        except Exception as e:
            self.logger.exception("Failed to get records")
            return []
    
    def update(self, record_id: str, update_data: Dict[str, Any]) -> bool:
        """Update record by ID.
        
        Args:
            record_id: Record ID
            update_data: Data to update
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            success = db_connection.update_one(
                self.collection_name,
                {'id': record_id},
                {'$set': update_data}
            )
            if success:
                self.logger.info("Updated record with ID: %s", record_id)
            return success
        except Exception as e:
            self.logger.exception("Failed to update record: %s", record_id)
            return False
    
    def delete(self, record_id: str) -> bool:
        """Delete record by ID.
        
        Args:
            record_id: Record ID
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            success = db_connection.delete_one(
                self.collection_name,
                {'id': record_id}
            )
            if success:
                self.logger.info("Deleted record with ID: %s", record_id)
            return success
        except Exception as e:
            self.logger.exception("Failed to delete record: %s", record_id)
            return False
    
    def count(self, filter_dict: Optional[Dict] = None) -> int:
        """Count records matching criteria.
        
        Args:
            filter_dict: Filter criteria
            
        Returns:
            Number of matching records
        """
        try:
            return db_connection.count_documents(self.collection_name, filter_dict)
        except Exception as e:
            self.logger.exception("Failed to count records")
            return 0
    
    def get_paginated(self, page: int = 1, per_page: int = 20, 
                     filter_dict: Optional[Dict] = None,
                     sort: Optional[List] = None,
                     projection: Optional[Dict] = None) -> Tuple[List[Dict], int]:
        """Get paginated results.
        
        Args:
            page: Page number (1-based)
            per_page: Records per page
            filter_dict: Filter criteria
            sort: Sort criteria
            projection: Fields to include/exclude
            
        Returns:
            Tuple of (records, total_count)
        """
        try:
            skip = (page - 1) * per_page
            records = self.get_all(
                filter_dict=filter_dict,
                projection=projection,
                skip=skip,
                limit=per_page,
                sort=sort
            )
            total = self.count(filter_dict)
            return records, total
        except Exception as e:
            self.logger.exception("Failed to get paginated records")
            return [], 0


class ServiceError(Exception):
    """Custom exception for service operations."""
    pass