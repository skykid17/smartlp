"""
Data models for SmartSOC application.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class RuleStatus(Enum):
    """Enumeration for rule statuses."""
    MATCHED = "Matched"
    UNMATCHED = "Unmatched"
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class SIEMType(Enum):
    """Enumeration for SIEM types."""
    SPLUNK = "splunk"
    ELASTICSEARCH = "elastic"


class LogLevel(Enum):
    """Enumeration for log levels."""
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class LogEntry:
    """Model for log parser entries."""
    id: str
    log: str
    regex: Optional[str] = None
    status: RuleStatus = RuleStatus.UNMATCHED
    timestamp: Optional[datetime] = None
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    user: Optional[str] = None
    process: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'log': self.log,
            'regex': self.regex,
            'status': self.status.value if self.status else None,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'source_ip': self.source_ip,
            'destination_ip': self.destination_ip,
            'user': self.user,
            'process': self.process,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        """Create from dictionary."""
        return cls(
            id=data.get('id', ''),
            log=data.get('log', ''),
            regex=data.get('regex'),
            status=RuleStatus(data.get('status', RuleStatus.UNMATCHED.value)),
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else None,
            source_ip=data.get('source_ip'),
            destination_ip=data.get('destination_ip'),
            user=data.get('user'),
            process=data.get('process'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
        )


@dataclass
class PrefixEntry:
    """Model for log prefix regex entries."""
    id: str
    regex: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'regex': self.regex,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PrefixEntry':
        """Create from dictionary."""
        return cls(
            id=data.get('id', ''),
            regex=data.get('regex', ''),
            description=data.get('description'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
        )


@dataclass
class SigmaRule:
    """Model for Sigma rules."""
    id: str
    title: str
    description: str
    rule_type: str
    level: LogLevel
    tactics: List[str]
    techniques: List[str]
    original_content: str
    splunk_query: Optional[str] = None
    elastic_query: Optional[str] = None
    status: RuleStatus = RuleStatus.PENDING
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'rule_type': self.rule_type,
            'level': self.level.value if self.level else None,
            'tactics': self.tactics,
            'techniques': self.techniques,
            'original_content': self.original_content,
            'splunk_query': self.splunk_query,
            'elastic_query': self.elastic_query,
            'status': self.status.value if self.status else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SigmaRule':
        """Create from dictionary."""
        return cls(
            id=data.get('id', ''),
            title=data.get('title', ''),
            description=data.get('description', ''),
            rule_type=data.get('rule_type', ''),
            level=LogLevel(data.get('level', LogLevel.MEDIUM.value)),
            tactics=data.get('tactics', []),
            techniques=data.get('techniques', []),
            original_content=data.get('original_content', ''),
            splunk_query=data.get('splunk_query'),
            elastic_query=data.get('elastic_query'),
            status=RuleStatus(data.get('status', RuleStatus.PENDING.value)),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
        )


@dataclass
class MitreAttackTechnique:
    """Model for MITRE ATT&CK techniques."""
    technique_id: str
    name: str
    tactic: str
    description: str
    platforms: List[str]
    data_sources: List[str]
    mitigation: Optional[str] = None
    detection: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'technique_id': self.technique_id,
            'name': self.name,
            'tactic': self.tactic,
            'description': self.description,
            'platforms': self.platforms,
            'data_sources': self.data_sources,
            'mitigation': self.mitigation,
            'detection': self.detection,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MitreAttackTechnique':
        """Create from dictionary."""
        return cls(
            technique_id=data.get('technique_id', ''),
            name=data.get('name', ''),
            tactic=data.get('tactic', ''),
            description=data.get('description', ''),
            platforms=data.get('platforms', []),
            data_sources=data.get('data_sources', []),
            mitigation=data.get('mitigation'),
            detection=data.get('detection'),
        )


@dataclass
class SettingsModel:
    """Model for application settings."""
    id: str
    active_siem: SIEMType
    log_ingestion_enabled: bool = True
    max_log_entries: int = 10000
    auto_parse_enabled: bool = True
    notification_enabled: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'active_siem': self.active_siem.value if self.active_siem else None,
            'log_ingestion_enabled': self.log_ingestion_enabled,
            'max_log_entries': self.max_log_entries,
            'auto_parse_enabled': self.auto_parse_enabled,
            'notification_enabled': self.notification_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SettingsModel':
        """Create from dictionary."""
        return cls(
            id=data.get('id', ''),
            active_siem=SIEMType(data.get('active_siem', SIEMType.SPLUNK.value)),
            log_ingestion_enabled=data.get('log_ingestion_enabled', True),
            max_log_entries=data.get('max_log_entries', 10000),
            auto_parse_enabled=data.get('auto_parse_enabled', True),
            notification_enabled=data.get('notification_enabled', True),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
        )


@dataclass
class PaginationResult:
    """Model for paginated results."""
    data: List[Any]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool
    
    @classmethod
    def create(cls, data: List[Any], total: int, page: int, per_page: int) -> 'PaginationResult':
        """Create pagination result.
        
        Args:
            data: List of data items
            total: Total number of items
            page: Current page number
            per_page: Items per page
            
        Returns:
            PaginationResult instance
        """
        total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0
        
        return cls(
            data=data,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'data': self.data,
            'total': self.total,
            'page': self.page,
            'per_page': self.per_page,
            'total_pages': self.total_pages,
            'has_next': self.has_next,
            'has_prev': self.has_prev,
        }