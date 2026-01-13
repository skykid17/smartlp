"""
Settings and environment management for SmartSOC.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from dataclasses import dataclass
from pymongo import MongoClient


@dataclass
class DatabaseSettings:
    """Database settings."""
    mongo_url: str
    db_name: str
    
    # Collections
    knowledge_collection: str
    logs_collection: str
    settings_collection: str


@dataclass
class SplunkSettings:
    """Splunk connection settings."""
    host: str
    port: str
    username: str
    password: str


@dataclass
class ElasticSettings:
    """Elasticsearch connection settings."""
    host: str
    username: str
    password: str
    api_key: str
    cert_path: str
    kibana_url: str
    

@dataclass
class AppSettings:
    """Main application settings."""
    host: str = "0.0.0.0"
    port: int = 8800
    debug: bool = True
    secret_key: Optional[str] = None


class EnvironmentManager:
    """Centralized settings management."""
    
    def __init__(self, env_file: Optional[str] = None):
        """Initialize settings manager.
        
        Args:
            env_file: Path to environment file. If None, uses default .env
        """
        load_dotenv(env_file)
        self._database_settings: Optional[DatabaseSettings] = None
        self._splunk_settings: Optional[SplunkSettings] = None
        self._elastic_settings: Optional[ElasticSettings] = None
        self._app_settings: Optional[AppSettings] = None

    def _mongo_url(self) -> str:
        """Return MongoDB connection string with a safe default."""
        return os.getenv('MONGO_URL') or 'mongodb://admin:password@localhost:27017/?directConnection=true'

    def _settings_collection(self):
        db = MongoClient(self._mongo_url()).get_database("smartlp")
        return db.get_collection("settings")
    
    @property
    def database(self) -> DatabaseSettings:
        """Get database settings."""
        if self._database_settings is None:
            # Prefer explicit environment variable, but fall back to a sensible localhost default
            mongo_url = os.getenv('MONGO_URL') or 'mongodb://admin:password@localhost:27017/?directConnection=true'
            self._database_settings = DatabaseSettings(
                mongo_url=mongo_url,
                db_name="smartlp",
                knowledge_collection="knowledge_base",
                logs_collection="logs",
                settings_collection="settings",
            )
        return self._database_settings
    
    @property
    def splunk(self) -> SplunkSettings:
        """Get Splunk settings."""
        if self._splunk_settings is None:
            settings_collection = self._settings_collection()
            doc = settings_collection.find_one({'category': 'siem_settings', 'id': 'splunk'}) or {}
            self._splunk_settings = SplunkSettings(
                host=str(doc.get('host') or ''),
                port=str(doc.get('port') or '8089'),
                username=str(doc.get('user') or ''),
                password=str(doc.get('password') or ''),
            )
        return self._splunk_settings
    
    @property
    def elastic(self) -> ElasticSettings:
        """Get Elasticsearch settings."""
        if self._elastic_settings is None:
            settings_collection = self._settings_collection()
            doc = settings_collection.find_one({'category': 'siem_settings', 'id': 'elastic'}) or {}
            self._elastic_settings = ElasticSettings(
                host=str(doc.get('host') or ''),
                username=str(doc.get('user') or ''),
                password=str(doc.get('password') or ''),
                api_key=str(doc.get('api_key') or ''),
                cert_path=str(doc.get('cert_path') or ''),
                kibana_url=str(doc.get('kibana_url') or ''),
            )
        return self._elastic_settings
    
    @property
    def app(self) -> AppSettings:
        """Get application settings."""
        if self._app_settings is None:
            self._app_settings = AppSettings(
                host=os.getenv('APP_HOST', '0.0.0.0'),
                port=int(os.getenv('APP_PORT', '8800')),
                debug=os.getenv('APP_DEBUG', 'True').lower() == 'true',
                secret_key=os.getenv('SECRET_KEY'),
            )
        return self._app_settings
    
    def _get_env(self, key: str, default: Optional[str] = None) -> str:
        """Get environment variable with validation.
        
        Args:
            key: Environment variable key
            default: Default value if key not found
            
        Returns:
            Environment variable value
            
        Raises:
            ValueError: If required environment variable is not set
        """
        value = os.getenv(key, default)
        if value is None:
            raise ValueError(f"Required environment variable '{key}' is not set")
        return value


# Global configuration instance
env_manager = EnvironmentManager()