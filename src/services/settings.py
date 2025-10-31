"""
Settings management service for SmartSOC application.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from .base import BaseService
from models.core import SettingsModel, SIEMType
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
            settings = self.db.query(
                'global_settings',
                {"id": "global"},
                {"_id": 0, "amendments": 0},
                limit=1
            )
            
            if settings:
                return convert_key_to_camel(settings)
            else:
                # Return default settings if none exist
                return convert_key_to_camel(self._get_default_global_settings())
        except Exception as e:
            self.log_error("Failed to get global settings", e)
            return convert_key_to_camel(self._get_default_global_settings())
    
    def get_siem_settings(self) -> List[Dict[str, Any]]:
        """Get SIEM configuration settings.
        
        Returns:
            List of SIEM settings with camelCase keys
        """
        try:
            siems = list(self.db.query(
                'siems_settings',
                projection={"_id": 0}
            ))
            
            return [convert_key_to_camel(siem) for siem in siems]
        except Exception as e:
            self.log_error("Failed to get SIEM settings", e)
            return []
    
    def get_llm_settings(self) -> List[Dict[str, Any]]:
        """Get LLM endpoint settings.
        
        Returns:
            List of LLM settings with camelCase keys
        """
        try:
            llms = list(self.db.query(
                'llms_settings',
                projection={"_id": 0}
            ))
            
            return [convert_key_to_camel(llm) for llm in llms]
        except Exception as e:
            self.log_error("Failed to get LLM settings", e)
            return []
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all application settings.
        
        Returns:
            All settings grouped by category
        """
        return {
            "settings": self.get_global_settings(),
            "siems": self.get_siem_settings(),
            "llmEndpoints": self.get_llm_settings()
        }
    
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
        """Update application settings.
        
        Args:
            settings_data: Flat settings data from frontend
            
        Returns:
            List of changes made
        """
        changes = []
        
        try:
            self.log_info(f"Updating settings with data: {list(settings_data.keys())}")
            
            # Get current settings for comparison
            current_global = self.get_global_settings()
            current_siems = {siem['id']: siem for siem in self.get_siem_settings()}
            current_llms = {llm['id']: llm for llm in self.get_llm_settings()}
            
            # Prepare global settings update
            global_settings_to_update = {}
            global_fields = [
                'activeSiem', 'activeLlmEndpoint', 'activeLlm', 'ingestFrequency', 
                'similarityThreshold', 'similarityCheck', 'ingestOn', 
                'ingestAlgoVersion', 'fixCount'
            ]
            
            for field in global_fields:
                if field in settings_data:
                    snake_field = convert_key_to_snake({field: settings_data[field]})
                    field_snake = list(snake_field.keys())[0]
                    new_value = snake_field[field_snake]
                    
                    # Compare with current value
                    if current_global.get(field_snake) != new_value:
                        global_settings_to_update[field_snake] = new_value
                        change_desc = self.get_human_friendly_change_description(field, new_value, current_siems, current_llms)
                        changes.append(change_desc)
            
            # Update global settings if there are changes
            if global_settings_to_update:
                global_settings_to_update['id'] = 'global'
                global_settings_to_update['updated_at'] = datetime.now().isoformat()
                
                result = self.db.update_one(
                    'global_settings',
                    {"id": "global"},
                    {"$set": global_settings_to_update}
                )
                
                if result:
                    self.log_info(f"Global settings updated: {list(global_settings_to_update.keys())}")
            
            # Handle SIEM settings updates
            if 'siem' in settings_data:
                siem_id = settings_data['siem']
                siem_updates = {}
                
                # Check for SIEM-specific fields
                siem_fields = ['searchIndex', 'searchEntryCount', 'searchQuery']
                for field in siem_fields:
                    if field in settings_data:
                        snake_field = convert_key_to_snake({field: settings_data[field]})
                        field_snake = list(snake_field.keys())[0]
                        new_value = snake_field[field_snake]
                        
                        # Compare with current value
                        current_siem = current_siems.get(siem_id, {})
                        if current_siem.get(field_snake) != new_value:
                            siem_updates[field_snake] = new_value
                            change_desc = self.get_human_friendly_change_description(field, new_value, current_siems, current_llms)
                            siem_name = current_siems.get(siem_id, {}).get('name', siem_id)
                            changes.append(f"{siem_name} {change_desc}")
                
                # Update SIEM settings if there are changes
                if siem_updates:
                    siem_updates['updated_at'] = datetime.now().isoformat()
                    
                    result = self.db.update_one(
                        'siems_settings',
                        {"id": siem_id},
                        {"$set": siem_updates}
                    )
                    
                    if result:
                        self.log_info(f"SIEM {siem_id} settings updated: {list(siem_updates.keys())}")
            
            # Handle LLM settings updates (including models and URL)
            if 'llmEndpoint' in settings_data:
                llm_id = settings_data['llmEndpoint']
                llm_updates = {}
                
                # Check for LLM URL changes
                if 'llmUrl' in settings_data:
                    new_url = settings_data['llmUrl']
                    current_llm = current_llms.get(llm_id, {})
                    if current_llm.get('url') != new_url:
                        llm_updates['url'] = new_url
                        llm_name = current_llms.get(llm_id, {}).get('name', llm_id)
                        changes.append(f"{llm_name} URL: {new_url}")
                
                # Check for model changes
                if 'models' in settings_data:
                    new_models = settings_data['models']
                    current_llm = current_llms.get(llm_id, {})
                    current_models = current_llm.get('models', [])
                    
                    # Compare model arrays
                    if set(new_models) != set(current_models):
                        llm_updates['models'] = new_models
                        added_models = set(new_models) - set(current_models)
                        removed_models = set(current_models) - set(new_models)
                        
                        llm_name = current_llms.get(llm_id, {}).get('name', llm_id)
                        if added_models:
                            changes.append(f"{llm_name} - Added Models: {', '.join(added_models)}")
                        if removed_models:
                            changes.append(f"{llm_name} - Removed Models: {', '.join(removed_models)}")
                
                # Update LLM settings if there are changes
                if llm_updates:
                    llm_updates['updated_at'] = datetime.now().isoformat()
                    
                    result = self.db.update_one(
                        'llms_settings',
                        {"id": llm_id},
                        {"$set": llm_updates}
                    )
                    
                    if result:
                        self.log_info(f"LLM {llm_id} settings updated: {list(llm_updates.keys())}")
            
            # Handle new LLM endpoints creation/updates
            if 'llmEndpoints' in settings_data:
                new_endpoints = settings_data['llmEndpoints']
                
                for endpoint_id, endpoint_data in new_endpoints.items():
                    current_endpoint = current_llms.get(endpoint_id, {})
                    
                    # Check if this is a new endpoint
                    if not current_endpoint:
                        # Create new endpoint
                        new_endpoint = {
                            'id': endpoint_id,
                            'name': endpoint_data.get('name', endpoint_id),
                            'url': endpoint_data.get('url', ''),
                            'models': endpoint_data.get('models', []),
                            'created_at': datetime.now().isoformat(),
                            'updated_at': datetime.now().isoformat()
                        }
                        
                        result = self.db.insert_one('llms_settings', new_endpoint)
                        if result:
                            changes.append(f"Added new LLM endpoint: {new_endpoint['name']}")
                            self.log_info(f"New LLM endpoint created: {endpoint_id}")
                    else:
                        # Check for changes to existing endpoint
                        endpoint_updates = {}
                        
                        if current_endpoint.get('name') != endpoint_data.get('name'):
                            endpoint_updates['name'] = endpoint_data.get('name')
                            
                        if current_endpoint.get('url') != endpoint_data.get('url'):
                            endpoint_updates['url'] = endpoint_data.get('url')
                            
                        if set(current_endpoint.get('models', [])) != set(endpoint_data.get('models', [])):
                            endpoint_updates['models'] = endpoint_data.get('models', [])
                        
                        if endpoint_updates:
                            endpoint_updates['updated_at'] = datetime.now().isoformat()
                            result = self.db.update_one(
                                'llms_settings',
                                {"id": endpoint_id},
                                {"$set": endpoint_updates}
                            )
                            
                            if result:
                                endpoint_name = endpoint_data.get('name', endpoint_id)
                                changes.append(f"Updated LLM endpoint: {endpoint_name}")
                                self.log_info(f"LLM endpoint updated: {endpoint_id}")
            
            if changes:
                self.log_info(f"Settings updated successfully: {len(changes)} changes made")
            else:
                self.log_info("No settings changes detected")
            
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
        return settings.get('activeSiem')
    
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
            
            result = self.db.update_one(
                'global_settings',
                {"id": "global"},
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