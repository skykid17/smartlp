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
                config_collection="settings",
            )
        return self._database_config
    
    @property
    def splunk(self) -> SplunkConfig:
        """Get Splunk configuration."""
        if self._splunk_config is None:
            db = MongoClient(os.getenv('MONGO_URL')).get_database("soc_rag_db")
            config_collection = db.get_collection("settings")
            self._splunk_config = SplunkConfig(
                host=config_collection.find_one({'category': 'siem_settings', 'id': 'splunk'})['host'],
                port=config_collection.find_one({'category': 'siem_settings', 'id': 'splunk'})['port'],
                username=config_collection.find_one({'category': 'siem_settings', 'id': 'splunk'})['user'],
                password=config_collection.find_one({'category': 'siem_settings', 'id': 'splunk'})['password'],
            )
        return self._splunk_config
    
    @property
    def elastic(self) -> ElasticConfig:
        """Get Elasticsearch configuration."""
        if self._elastic_config is None:
            db = MongoClient(os.getenv('MONGO_URL')).get_database("soc_rag_db")
            config_collection = db.get_collection("settings")
            self._elastic_config = ElasticConfig(
                host=config_collection.find_one({'category': 'siem_settings', 'id': 'elastic'})['host'],
                username=config_collection.find_one({'category': 'siem_settings', 'id': 'elastic'})['user'],
                password=config_collection.find_one({'category': 'siem_settings', 'id': 'elastic'})['password'],
                cert_path=config_collection.find_one({'category': 'siem_settings', 'id': 'elastic'})['cert_path'],
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
        # Assemble settings data from the `settings` collection so the frontend
        # receives the runtime configuration (global, llm endpoints, and siem configs).
        from pymongo import MongoClient
        import json

        mongo_url = os.getenv('MONGO_URL')
        db_name = self.database.db_name
        result: Dict[str, Any] = {
            'database': {
                'mongo_url': '***' if mongo_url else None,
                'db_name': db_name,
                'knowledge_collection': self.database.knowledge_collection,
                'logs_collection': self.database.logs_collection,
                'config_collection': self.database.config_collection,
            },
            'app': {
                'host': self.app.host,
                'port': self.app.port,
                'debug': self.app.debug,
            },
            'global': {},
            'llms': [],
            'siems': [],
        }

        try:
            client = MongoClient(mongo_url)
            cfg = client.get_database(db_name).get_collection(self.database.config_collection)

            # Global settings (single doc with category 'global_settings')
            global_doc = cfg.find_one({'category': 'global_settings'}) or {}
            # convert values to JSON-safe types (mask sensitive fields)
            gd = json.loads(json.dumps(global_doc, default=str))
            result['global'] = gd

            # LLM endpoints
            llm_docs = list(cfg.find({'category': 'llm_settings'}))
            for d in llm_docs:
                doc = json.loads(json.dumps(d, default=str))
                # mask api_key if present
                if 'api_key' in doc and doc['api_key']:
                    doc['api_key'] = '***'
                result['llms'].append(doc)

            # SIEM configs
            siem_docs = list(cfg.find({'category': 'siem_settings'}))
            for d in siem_docs:
                doc = json.loads(json.dumps(d, default=str))
                if 'password' in doc and doc['password']:
                    doc['password'] = '***'
                if 'api_key' in doc and doc['api_key']:
                    doc['api_key'] = '***'
                result['siems'].append(doc)

        except Exception:
            # If DB access fails, return what we can (caller should handle empty fields)
            pass

        return result


# Global configuration instance
settings = ConfigManager()