"""
Configuration settings and environment management for SmartSOC.
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from dataclasses import dataclass
from pymongo import MongoClient



@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    mongo_url: str
    db_name: str
    
    # Collections
    knowledge_collection: str
    logs_collection: str
    config_collection: str


@dataclass
class SplunkConfig:
    """Splunk connection configuration."""
    host: str
    port: str
    username: str
    password: str


@dataclass
class ElasticConfig:
    """Elasticsearch connection configuration."""
    host: str
    username: str
    password: str
    cert_path: str


@dataclass
class AnsibleConfig:
    """Ansible deployment configuration."""
    user: str
    ssh_password: str
    become_password: str
    collections_path: str


@dataclass
class AppConfig:
    """Main application configuration."""
    host: str = "0.0.0.0"
    port: int = 8800
    debug: bool = True
    secret_key: Optional[str] = None


class ConfigManager:
    """Centralized configuration management."""
    
    def __init__(self, env_file: Optional[str] = None):
        """Initialize configuration manager.
        
        Args:
            env_file: Path to environment file. If None, uses default .env
        """
        load_dotenv(env_file)
        self._database_config: Optional[DatabaseConfig] = None
        self._splunk_config: Optional[SplunkConfig] = None
        self._elastic_config: Optional[ElasticConfig] = None
        self._ansible_config: Optional[AnsibleConfig] = None
        self._app_config: Optional[AppConfig] = None
    
    @property
    def database(self) -> DatabaseConfig:
        """Get database configuration."""
        if self._database_config is None:
            self._database_config = DatabaseConfig(
                mongo_url=self._get_env('MONGO_URL'),
                db_name="soc_rag_db",
                knowledge_collection="knowledge_base",
                logs_collection="logs",
                config_collection="config",
            )
        return self._database_config
    
    @property
    def splunk(self) -> SplunkConfig:
        """Get Splunk configuration."""
        if self._splunk_config is None:
            db = MongoClient(os.getenv('MONGO_URL')).get_database("soc_rag_db")
            config_collection = db.get_collection("config")
            self._splunk_config = SplunkConfig(
                host=config_collection.find_one({'category': 'siem_config', 'id': 'splunk'})['host'],
                port=config_collection.find_one({'category': 'siem_config', 'id': 'splunk'})['port'],
                username=config_collection.find_one({'category': 'siem_config', 'id': 'splunk'})['user'],
                password=config_collection.find_one({'category': 'siem_config', 'id': 'splunk'})['password'],
            )
        return self._splunk_config
    
    @property
    def elastic(self) -> ElasticConfig:
        """Get Elasticsearch configuration."""
        if self._elastic_config is None:
            db = MongoClient(os.getenv('MONGO_URL')).get_database("soc_rag_db")
            config_collection = db.get_collection("config")
            self._elastic_config = ElasticConfig(
                host=config_collection.find_one({'category': 'siem_config', 'id': 'elastic'})['host'],
                username=config_collection.find_one({'category': 'siem_config', 'id': 'elastic'})['user'],
                password=config_collection.find_one({'category': 'siem_config', 'id': 'elastic'})['password'],
                cert_path=config_collection.find_one({'category': 'siem_config', 'id': 'elastic'})['cert_path'],
            )
        return self._elastic_config
    
    @property
    def ansible(self) -> AnsibleConfig:
        """Get Ansible configuration."""
        if self._ansible_config is None:
            self._ansible_config = AnsibleConfig(
                user=self._get_env('ANSIBLE_USER'),
                ssh_password=self._get_env('ANSIBLE_SSH_PASSWORD'),
                become_password=self._get_env('ANSIBLE_BECOME_PASSWORD'),
                collections_path=os.getenv('ANSIBLE_COLLECTIONS_PATH', 
                                         '/opt/SmartSOC/lib/python3.13/site-packages/ansible_collections'),
            )
        return self._ansible_config
    
    @property
    def app(self) -> AppConfig:
        """Get application configuration."""
        if self._app_config is None:
            self._app_config = AppConfig(
                host=os.getenv('APP_HOST', '0.0.0.0'),
                port=int(os.getenv('APP_PORT', '8800')),
                debug=os.getenv('APP_DEBUG', 'True').lower() == 'true',
                secret_key=os.getenv('SECRET_KEY'),
            )
        return self._app_config
    
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
    
    def get_env_dict(self) -> Dict[str, Any]:
        """Get all configuration as a dictionary for debugging."""
        return {
            'database': {
                'mongo_url': '***' if self.database.mongo_url else None,
                'parser_db_name': self.database.parser_db_name,
                'settings_db_name': self.database.settings_db_name,
                'mitre_db_name': self.database.mitre_db_name,
            },
            'splunk': {
                'host': self.splunk.host,
                'port': self.splunk.port,
                'username': self.splunk.username,
                'password': '***' if self.splunk.password else None,
            },
            'elastic': {
                'host': self.elastic.host,
                'username': self.elastic.username,
                'password': '***' if self.elastic.password else None,
            },
            'app': {
                'host': self.app.host,
                'port': self.app.port,
                'debug': self.app.debug,
            }
        }


# Global configuration instance
config = ConfigManager()