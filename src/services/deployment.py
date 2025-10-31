"""
Deployment service for SmartSOC application.
"""

from typing import List, Tuple
import subprocess
import json
import os

from .base import BaseService
from config.settings import config


class DeploymentService(BaseService):
    """Service for handling Ansible deployments."""
    
    def __init__(self):
        """Initialize deployment service."""
        super().__init__("deployment")
        self.ansible_config = config.ansible
    
    def deploy_rules(self, rule_ids: List[str], deployment_type: str, siem_type: str) -> Tuple[bool, str]:
        """Deploy rules using Ansible.
        
        Args:
            rule_ids: List of rule IDs to deploy
            deployment_type: Type of deployment (smartlp)
            siem_type: Target SIEM type (splunk, elastic)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Determine playbook path based on deployment type and SIEM
            playbook_path = self._get_playbook_path(deployment_type, siem_type)
            if not playbook_path:
                return False, f"No playbook available for {deployment_type} on {siem_type}"
            
            # Check if playbook exists
            if not os.path.exists(playbook_path):
                return False, f"Playbook not found: {playbook_path}"
            
            self.log_info(f"Deploying {len(rule_ids)} rules using {playbook_path}")
            
            # Run Ansible playbook
            success = self._run_ansible_playbook(playbook_path, rule_ids)
            
            if success:
                message = f"Successfully deployed {len(rule_ids)} rules to {siem_type}"
                self.log_info(message)
                return True, message
            else:
                message = f"Failed to deploy rules to {siem_type}"
                self.log_error(message)
                return False, message
                
        except Exception as e:
            error_msg = f"Deployment error: {str(e)}"
            self.log_error(error_msg, e)
            return False, error_msg
    
    def _get_playbook_path(self, deployment_type: str, siem_type: str) -> str:
        """Get playbook path for deployment type and SIEM.
        
        Args:
            deployment_type: Type of deployment
            siem_type: Target SIEM type
            
        Returns:
            Path to appropriate playbook or empty string if not supported
        """
        playbook_mapping = {
            ("smartlp", "splunk"): "./ansible/9_smartsoc.yml",
            # Add more mappings as needed
        }
        
        return playbook_mapping.get((deployment_type, siem_type), "")
    
    def _run_ansible_playbook(self, playbook_path: str, rule_ids: List[str]) -> bool:
        """Run Ansible playbook.
        
        Args:
            playbook_path: Path to the playbook
            rule_ids: List of rule IDs to deploy
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Set up environment
            env = os.environ.copy()
            env["ANSIBLE_COLLECTIONS_PATH"] = self.ansible_config.collections_path
            
            # Build command
            inventory_path = "./ansible/inventories/emax_test.yml"
            command = ["../bin/ansible-playbook", playbook_path]
            
            if os.path.exists(inventory_path):
                command.extend(["-i", inventory_path])
            
            # Build extra vars
            extra_vars = {
                "entries_id_list": rule_ids
            }
            
            # Add authentication if available
            if self.ansible_config.user:
                extra_vars["ansible_user"] = self.ansible_config.user
            
            if self.ansible_config.ssh_password:
                extra_vars["ansible_password"] = self.ansible_config.ssh_password
            else:
                command.append("--ask-pass")
            
            if self.ansible_config.become_password:
                extra_vars["ansible_become_pass"] = self.ansible_config.become_password
            else:
                command.append("--ask-become-pass")
            
            # Add extra vars and SSH options
            command.extend(["--ssh-extra-args", "-o StrictHostKeyChecking=no"])
            command.extend(["--extra-vars", json.dumps(extra_vars)])
            
            # Execute command
            self.log_info(f"Executing: {' '.join(command[:3])}...")  # Don't log sensitive data
            
            result = subprocess.run(
                command,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            self.log_info("Ansible playbook executed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            self.log_error(f"Ansible playbook failed with return code {e.returncode}")
            if e.stdout:
                self.log_error(f"STDOUT: {e.stdout}")
            if e.stderr:
                self.log_error(f"STDERR: {e.stderr}")
            return False
        except Exception as e:
            self.log_error(f"Error running Ansible playbook", e)
            return False


# Global deployment service instance
deployment_service = DeploymentService()