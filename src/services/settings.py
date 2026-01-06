"""
Settings management service for SmartSOC application.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from .base import BaseService
from models.core import SIEMType
from database.connection import db_connection
from utils.formatters import convert_key_to_camel, convert_key_to_snake


class SettingsService(BaseService):
    """Service for managing application settings."""
    
    def __init__(self):
        """Initialize settings service."""
        super().__init__("settings")
    
    def get_global_settings(self) -> Dict[str, Any]:
        """Get global application settings.
        
        Returns:
            Global settings as dictionary with camelCase keys
        """
        try:
            settings = db_connection.query(
                'settings',
                {"category": "global_settings"},
                {"_id": 0, "amendments": 0},
                limit=1
            )
            
            if settings:
                return settings
            else:
                # Return default settings if none exist
                return self._get_default_global_settings()
        except Exception as e:
            self.log_error("Failed to get global settings", e)
            return self._get_default_global_settings()
    
    def get_siem_settings(self) -> List[Dict[str, Any]]:
        """Get SIEM configuration settings.
        
        Returns:
            List of SIEM settings with camelCase keys
        """
        try:
            siems = list(db_connection.query(
                'settings',
                {"category": "siem_settings"},
                projection={"_id": 0}
            ))
            
            return siems
        except Exception as e:
            self.log_error("Failed to get SIEM settings", e)
            return []
    
    def get_llm_endpoints(self):
        return list(db_connection.query(
            'settings',
            {"category": "llm_endpoint"},
            projection={"_id": 0}
        ))
    
    def get_llm_models(self):
        return list(db_connection.query(
            'settings',
            {"category": "llm_model"},
            projection={"_id": 0}
        ))

    def get_active_llm(self):
        """Returns:
        {
            "model": {...},
            "endpoint": {url, api_key, ...}
        }
        """
        try:
            global_settings = self.get_global_settings()
            active_model_id = global_settings.get("active_llm_model_id")

            if not active_model_id:
                self.log_warning("No active LLM model configured")
                return None
            
            # Fetch model
            model = db_connection.find_one(
                'settings',
                {"category": "llm_model", "id": active_model_id},
                projection={"_id": 0}
            )

            if not model:
                self.log_warning(f"Active LLM model '{active_model_id}' not found")
                return None
            
            endpoint_id = model.get("endpoint_id")

            if not endpoint_id:
                self.log_warning(f"Model '{active_model_id}' missing endpoint_id")
                return None
            
            # Fetch endpoint
            endpoint = db_connection.find_one(
                'settings',
                {"category": "llm_endpoint", "id": endpoint_id},
                projection={"_id": 0}
            )

            if not endpoint:
                self.log_warning(f"Endpoint '{endpoint_id}' not found for model '{active_model_id}'")
                return None
            
            return {
                "model": model,
                "endpoint": endpoint
            }

        except Exception as e:
            self.log_error("Error resolving active LLM", e)
            return None


    def get_prompts_settings(self, key) -> Any:
        """Return the value of a specific prompt field from settings (id='prompts')."""
        try:
            doc = db_connection.query(
                'settings',
                {"id": "prompts"},
                projection={"_id": 0, key: 1},
                limit=1
            )

            if not doc:
                return None

            # Return the actual value, not the whole document
            return doc.get(key)

        except Exception as e:
            self.log_error("Failed to get prompts doc", e)
            return None

    def get_all_settings(self) -> Dict[str, Any]:
        """Get all application settings (for frontend).
        
        Returns:
            All settings grouped by category, with LLM endpoints nested with their models
        """
        try:
            # Fetch raw backend settings
            global_settings = self.get_global_settings() or {}
            siems = self.get_siem_settings() or []
            endpoints = self.get_llm_endpoints() or []
            models = self.get_llm_models() or []

            # Map models by endpoint_id for easy nesting
            models_by_endpoint = {}
            for m in models:
                endpoint_id = m.get("endpoint_id")
                if endpoint_id not in models_by_endpoint:
                    models_by_endpoint[endpoint_id] = []
                models_by_endpoint[endpoint_id].append({
                    "id": m.get("id"),
                    "displayName": m.get("display_name"),
                    "modelName": m.get("model_name"),
                    "provider": m.get("provider")
                })

            # Build endpoints with nested models
            endpoints_nested = []
            for e in endpoints:
                endpoint_models = models_by_endpoint.get(e.get("id"), [])
                endpoints_nested.append({
                    "id": e.get("id"),
                    "name": e.get("name"),
                    "url": e.get("url"),
                    "apiKey": e.get("api_key"),
                    "updatedAt": e.get("updated_at"),
                    "models": endpoint_models
                })

            return {
                "globalSettings": convert_key_to_camel(global_settings) if isinstance(global_settings, dict) else {},
                "siems": [convert_key_to_camel(s) for s in siems],
                "llmEndpoints": endpoints_nested
            }

        except Exception as e:
            self.log_error("Failed to prepare frontend settings response", e)
            return {"globalSettings": {}, "siems": [], "llmEndpoints": []}

    
    def get_human_friendly_change_description(self, field: str, new_value: Any, current_siems: Dict = None, current_llms: Dict = None) -> str:
        """Generate human-friendly change descriptions.
        
        Args:
            field: The field name
            new_value: The new value
            current_siems: Dictionary of SIEM configurations for lookups
            current_llms: Dictionary of LLM configurations for lookups
            
        Returns:
            Human-friendly change description
        """
        field_names = {
            'activeSiem': 'Active SIEM',
            'activeLlmEndpoint': 'Active LLM Endpoint', 
            'activeLlm': 'Active LLM Model',
            'ingestFrequency': 'Ingestion Frequency',
            'similarityThreshold': 'Similarity Threshold',
            'similarityCheck': 'Similarity Check',
            'ingestOn': 'Log Ingestion',
            'ingestAlgoVersion': 'Parsing Algorithm Version',
            'fixCount': 'Regex Fix Count',
            'searchIndex': 'Search Index',
            'searchEntryCount': 'Search Entry Count', 
            'searchQuery': 'Search Query'
        }
        
        display_name = field_names.get(field, field)
        
        # Handle special cases for better descriptions
        if field in ['ingestOn', 'similarityCheck']:
            status = 'Enabled' if new_value else 'Disabled'
            return f"{display_name}: {status}"
        elif field == 'activeSiem' and current_siems:
            siem_name = current_siems.get(new_value, {}).get('name', new_value)
            return f"{display_name}: {siem_name}"
        elif field == 'activeLlmEndpoint' and current_llms:
            llm_name = current_llms.get(new_value, {}).get('name', new_value)
            return f"{display_name}: {llm_name}"
        elif field == 'ingestFrequency':
            return f"{display_name}: Every {new_value} minutes"
        elif field == 'ingestAlgoVersion':
            return f"{display_name}: Version {new_value.replace('v', '')}"
        else:
            return f"{display_name}: {new_value}"

    def update_settings(self, settings_data: Dict[str, Any]) -> List[str]:
        """Update application settings with the new llm_endpoint / llm_model schema."""
        changes = []

        try:
            # --- Load current settings ---
            current_global = self.get_global_settings() or {}
            current_siems = {s['id']: s for s in self.get_siem_settings() or []}
            current_endpoints = {e['id']: e for e in self.get_llm_endpoints() or []}
            current_models = {m['id']: m for m in self.get_llm_models() or []}

            # Convert to snake_case for comparison
            current_global_snake = convert_key_to_snake(current_global)
            current_siems_snake = {s['id']: convert_key_to_snake(s) for s in current_siems.values()}
            current_endpoints_snake = {e['id']: convert_key_to_snake(e) for e in current_endpoints.values()}
            current_models_snake = {m['id']: convert_key_to_snake(m) for m in current_models.values()}

            # --- Update global settings ---
            global_fields = [
                'activeSiem', 'activeLlmModelId', 'ingestFrequency',
                'similarityThreshold', 'similarityCheck', 'ingestOn',
                'ingestAlgoVersion', 'fixCount'
            ]
            global_updates = {}
            for field in global_fields:
                if field in settings_data:
                    key_snake, new_value = list(convert_key_to_snake({field: settings_data[field]}).items())[0]
                    if current_global_snake.get(key_snake) != new_value:
                        global_updates[key_snake] = new_value
                        changes.append(f"Global setting '{field}' updated to '{new_value}'")
            if global_updates:
                global_updates['updated_at'] = datetime.now().isoformat()
                db_connection.update_one('settings', {"id": "global"}, {"$set": global_updates})

            # --- Update SIEM settings ---
            if 'siem' in settings_data:
                siem_id = settings_data['siem']
                siem_updates = {}
                siem_fields = ['searchIndex', 'searchEntryCount', 'searchQuery']
                for field in siem_fields:
                    if field in settings_data:
                        key_snake, new_value = list(convert_key_to_snake({field: settings_data[field]}).items())[0]
                        current_siem = current_siems_snake.get(siem_id, {})
                        if current_siem.get(key_snake) != new_value:
                            siem_updates[key_snake] = new_value
                            siem_name = current_siems.get(siem_id, {}).get('name', siem_id)
                            changes.append(f"{siem_name} {field} updated to {new_value}")
                if siem_updates:
                    siem_updates['updated_at'] = datetime.now().isoformat()
                    db_connection.update_one(
                        'settings', {"category": "siem_settings", "id": siem_id}, {"$set": siem_updates}
                    )

            # --- Update / create LLM endpoints ---
            if 'llmEndpoints' in settings_data:
                for endpoint_id, endpoint_data in settings_data['llmEndpoints'].items():
                    current_endpoint = current_endpoints.get(endpoint_id)

                    # Delete endpoint
                    if endpoint_data is None or (isinstance(endpoint_data, dict) and endpoint_data.get('_delete')):
                        db_connection.delete_one('settings', {"category": "llm_endpoint", "id": endpoint_id})
                        changes.append(f"Deleted LLM endpoint: {endpoint_id}")
                        continue

                    # Create new endpoint
                    if not current_endpoint:
                        new_endpoint = {
                            'id': endpoint_id,
                            'name': endpoint_data.get('name', endpoint_id),
                            'url': endpoint_data.get('url', ''),
                            'api_key': endpoint_data.get('api_key') or endpoint_data.get('apiKey') or '',
                            'category': 'llm_endpoint',
                            'created_at': datetime.now().isoformat(),
                            'updated_at': datetime.now().isoformat()
                        }
                        db_connection.insert_one('settings', new_endpoint)
                        changes.append(f"Added new LLM endpoint: {new_endpoint['name']}")
                        continue

                    # Update existing endpoint
                    endpoint_updates = {}
                    for key in ['name', 'url', 'api_key']:
                        incoming_val = endpoint_data.get(key) or (endpoint_data.get('apiKey') if key == 'api_key' else None)
                        if incoming_val is not None and current_endpoint.get(key) != incoming_val:
                            endpoint_updates[key] = incoming_val

                    if endpoint_updates:
                        endpoint_updates['updated_at'] = datetime.now().isoformat()
                        db_connection.update_one(
                            'settings', {"category": "llm_endpoint", "id": endpoint_id}, {"$set": endpoint_updates}
                        )
                        changes.append(f"Updated LLM endpoint: {endpoint_id}")

            # --- Update / create LLM models ---
            if 'llmModels' in settings_data:
                for model_id, model_data in settings_data['llmModels'].items():
                    current_model = current_models.get(model_id)

                    # Delete model
                    if model_data is None or (isinstance(model_data, dict) and model_data.get('_delete')):
                        db_connection.delete_one('settings', {"category": "llm_model", "id": model_id})
                        changes.append(f"Deleted LLM model: {model_id}")
                        continue

                    # Create new model
                    if not current_model:
                        new_model = {
                            'id': model_id,
                            'model_name': model_data['model_name'],
                            'display_name': model_data.get('display_name', model_data['model_name']),
                            'endpoint_id': model_data['endpoint_id'],
                            'provider': model_data.get('provider', ''),
                            'category': 'llm_model',
                            'created_at': datetime.now().isoformat(),
                            'updated_at': datetime.now().isoformat()
                        }
                        db_connection.insert_one('settings', new_model)
                        changes.append(f"Added new LLM model: {new_model['display_name']}")
                        continue

                    # Update existing model
                    model_updates = {}
                    for key in ['model_name', 'display_name', 'endpoint_id', 'provider']:
                        incoming_val = model_data.get(key)
                        if incoming_val is not None and current_model.get(key) != incoming_val:
                            model_updates[key] = incoming_val

                    if model_updates:
                        model_updates['updated_at'] = datetime.now().isoformat()
                        db_connection.update_one(
                            'settings', {"category": "llm_model", "id": model_id}, {"$set": model_updates}
                        )
                        changes.append(f"Updated LLM model: {model_id}")

            return changes

        except Exception as e:
            self.log_error("Failed to update settings", e)
            return [f"Error updating settings: {str(e)}"]
    
    def get_active_siem(self) -> Optional[str]:
        """Get the active SIEM type.
        
        Returns:
            Active SIEM type or None if not configured
        """
        settings = self.get_global_settings()
        # Backend stores snake_case; be defensive and accept either
        return settings.get('active_siem') or settings.get('activeSiem')
    
    def set_active_siem(self, siem_type: str) -> bool:
        """Set the active SIEM type.
        
        Args:
            siem_type: SIEM type to set as active
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate SIEM type
            if siem_type not in [siem.value for siem in SIEMType]:
                self.log_error(f"Invalid SIEM type: {siem_type}")
                return False
            
            result = db_connection.update_one(
                'settings',
                {"category": "global_settings", "id": "global"},
                {"$set": {
                    "active_siem": siem_type,
                    "updated_at": datetime.now().isoformat()
                }}
            )
            
            if result:
                self.log_info(f"Active SIEM set to: {siem_type}")
                return True
            else:
                self.log_error(f"Failed to set active SIEM to: {siem_type}")
                return False
                
        except Exception as e:
            self.log_error(f"Error setting active SIEM to {siem_type}", e)
            return False
    
    def _get_default_global_settings(self) -> Dict[str, Any]:
        """Get default global settings.
        
        Returns:
            Default global settings
        """
        return {
            "id": "global",
            "active_siem": "splunk",
            "ingest_on": True,
            "ingest_frequency": 30,
            "similarity_check": False,
            "similarity_threshold": 0.8,
            "fix_count": 3,
            "ingest_algo_version": "v1",
            "active_llm_endpoint": "openai",
            "active_llm": "gpt-3.5-turbo",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }


# Global settings service instance
settings_service = SettingsService()