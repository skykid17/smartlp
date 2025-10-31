"""
Configuration settings and environment management for SmartSOC.
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    mongo_url: str
    parser_db_name: str
    settings_db_name: str
    mitre_db_name: str
    mitre_tech_db_name: str
    
    # Collections
    parser_entries_collection: str
    global_settings_collection: str
    llms_settings_collection: str
    siems_settings_collection: str
    sigma_rules_collection: str
    splunk_rules_collection: str
    elastic_rules_collection: str
    secops_rules_collection: str
    mitre_techniques_collection: str


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
                parser_db_name=self._get_env('MONGO_DB_PARSER'),
                settings_db_name=self._get_env('MONGO_DB_SETTINGS'),
                mitre_db_name=self._get_env('MONGO_DB_MITRE'),
                mitre_tech_db_name=self._get_env('MONGO_DB_MITRE_TECH'),
                parser_entries_collection=self._get_env('MONGO_COLLECTION_ENTRIES'),
                global_settings_collection=self._get_env('MONGO_COLLECTION_GLOBAL_SETTINGS'),
                llms_settings_collection=self._get_env('MONGO_COLLECTION_LLMS_SETTINGS'),
                siems_settings_collection=self._get_env('MONGO_COLLECTION_SIEMS_SETTINGS'),
                sigma_rules_collection=self._get_env('MONGO_COLLECTION_SIGMA_RULES'),
                splunk_rules_collection=self._get_env('MONGO_COLLECTION_SPLUNK_RULES'),
                elastic_rules_collection=self._get_env('MONGO_COLLECTION_ELASTIC_RULES'),
                secops_rules_collection=self._get_env('MONGO_COLLECTION_SECOPS_RULES'),
                mitre_techniques_collection=self._get_env('MONGO_COLLECTION_MITRE_TECHNIQUES'),
            )
        return self._database_config
    
    @property
    def splunk(self) -> SplunkConfig:
        """Get Splunk configuration."""
        if self._splunk_config is None:
            self._splunk_config = SplunkConfig(
                host=self._get_env('SPLUNK_HOST'),
                port=self._get_env('SPLUNK_PORT'),
                username=self._get_env('SPLUNK_USER'),
                password=self._get_env('SPLUNK_PASSWORD'),
            )
        return self._splunk_config
    
    @property
    def elastic(self) -> ElasticConfig:
        """Get Elasticsearch configuration."""
        if self._elastic_config is None:
            self._elastic_config = ElasticConfig(
                host=self._get_env('ELASTIC_HOST'),
                username=self._get_env('ELASTIC_USER'),
                password=self._get_env('ELASTIC_PASSWORD'),
                cert_path=self._get_env('ELASTIC_CERT_PATH'),
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