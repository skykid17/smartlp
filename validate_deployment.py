#!/usr/bin/env python3
"""
SmartLP Deployment Validation Script

This script validates that the new Ansible-based deployment system is properly configured.
Run this before attempting your first deployment to catch configuration issues early.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(message):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}\n")

def print_success(message):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_warning(message):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def print_error(message):
    """Print an error message."""
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def check_file_exists(filepath, description):
    """Check if a file exists and is readable."""
    if os.path.exists(filepath):
        if os.access(filepath, os.R_OK):
            print_success(f"{description} exists and is readable: {filepath}")
            return True
        else:
            print_error(f"{description} exists but is not readable: {filepath}")
            return False
    else:
        print_error(f"{description} not found: {filepath}")
        return False

def check_ansible():
    """Check if Ansible is installed and accessible."""
    print_header("Checking Ansible Installation")
    
    try:
        result = subprocess.run(
            ["ansible-playbook", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print_success(f"Ansible is installed: {version_line}")
            return True
        else:
            print_error("Ansible is installed but not working correctly")
            return False
    except FileNotFoundError:
        print_error("Ansible is not installed. Install with: pip install ansible")
        return False
    except Exception as e:
        print_error(f"Error checking Ansible: {str(e)}")
        return False

def check_mongodb_collection():
    """Check if MongoDB collection module is available."""
    print_header("Checking Ansible MongoDB Collection")
    
    try:
        result = subprocess.run(
            ["ansible-galaxy", "collection", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if "community.mongodb" in result.stdout:
            print_success("Ansible MongoDB collection is installed")
            return True
        else:
            print_warning("MongoDB collection not found")
            print_warning("Install with: ansible-galaxy collection install community.mongodb")
            return False
    except Exception as e:
        print_error(f"Error checking MongoDB collection: {str(e)}")
        return False

def check_playbook_files():
    """Check if required playbook files exist."""
    print_header("Checking Ansible Playbook Files")
    
    base_dir = Path(__file__).parent
    ansible_dir = base_dir / "ansible"
    
    files_to_check = [
        (ansible_dir / "deploy_smartlp.yml", "Main deployment playbook"),
        (ansible_dir / "tasks" / "deploy_smartlp_config.yml", "Configuration deployment tasks"),
        (ansible_dir / "inventories" / "default.yml", "Default inventory"),
        (ansible_dir / "group_vars" / "all", "Group variables"),
    ]
    
    all_ok = True
    for filepath, description in files_to_check:
        if not check_file_exists(filepath, description):
            all_ok = False
    
    return all_ok

def check_python_code():
    """Check that the Python service code has been updated."""
    print_header("Checking Python Service Code")
    
    base_dir = Path(__file__).parent
    siem_file = base_dir / "src" / "services" / "siem.py"
    
    if not check_file_exists(siem_file, "SIEM service file"):
        return False
    
    # Read the file and check for old patterns
    try:
        with open(siem_file, 'r') as f:
            content = f.read()
        
        # Check for removed patterns (in actual code, not comments)
        # Parse line by line to exclude comments and docstrings
        lines_with_refresh = []
        in_docstring = False
        docstring_char = None
        
        for line in content.split('\n'):
            # Skip empty lines
            if not line.strip():
                continue
            
            # Track docstring state
            if '"""' in line or "'''" in line:
                # Toggle docstring state
                if '"""' in line:
                    in_docstring = not in_docstring
                elif "'''" in line:
                    in_docstring = not in_docstring
            
            # Skip if in docstring
            if in_docstring:
                continue
                
            # Skip lines that are entirely comments
            if line.strip().startswith('#'):
                continue
            
            # Check if .refresh() is in actual code
            if '.refresh()' in line:
                # Get code before any comment
                code_part = line.split('#')[0]
                if '.refresh()' in code_part:
                    lines_with_refresh.append(line)
        
        if lines_with_refresh:
            print_error("Found .refresh() calls in siem.py (should be removed):")
            for line in lines_with_refresh[:3]:  # Show first 3
                print(f"  {line.strip()}")
            return False
        else:
            print_success("No .refresh() calls found in actual code (only in comments/docs)")
        
        # Check for new patterns
        if 'ansible-playbook' in content:
            print_success("Found Ansible subprocess execution in deploy_config_splunk()")
        else:
            print_warning("Could not find Ansible subprocess execution")
            return False
        
        if '_rollback_config_files' not in content or content.count('_rollback_config_files') == 0:
            print_success("Obsolete _rollback_config_files() method has been removed")
        else:
            print_warning("_rollback_config_files() method may still exist")
        
        return True
        
    except Exception as e:
        print_error(f"Error reading siem.py: {str(e)}")
        return False

def check_documentation():
    """Check if documentation files exist."""
    print_header("Checking Documentation")
    
    base_dir = Path(__file__).parent
    ansible_dir = base_dir / "ansible"
    
    docs_to_check = [
        (ansible_dir / "README.md", "Ansible deployment guide"),
        (ansible_dir / "MIGRATION.md", "Migration guide"),
        (ansible_dir / "CHANGELOG.md", "Changelog"),
    ]
    
    all_ok = True
    for filepath, description in docs_to_check:
        if not check_file_exists(filepath, description):
            all_ok = False
    
    return all_ok

def validate_inventory_format():
    """Validate that the inventory file has correct format."""
    print_header("Validating Inventory Format")
    
    base_dir = Path(__file__).parent
    inventory_file = base_dir / "ansible" / "inventories" / "default.yml"
    
    try:
        import yaml
        
        with open(inventory_file, 'r') as f:
            inventory = yaml.safe_load(f)
        
        # Check basic structure
        if 'all' in inventory:
            print_success("Inventory has 'all' group")
            
            if 'children' in inventory['all']:
                if 'splunk_servers' in inventory['all']['children']:
                    print_success("Inventory has 'splunk_servers' group")
                    return True
                else:
                    print_error("Inventory missing 'splunk_servers' group")
            else:
                print_error("Inventory missing 'children' section")
        else:
            print_error("Inventory missing 'all' group")
        
        return False
        
    except ImportError:
        print_warning("PyYAML not installed, skipping inventory validation")
        print_warning("Install with: pip install pyyaml")
        return True  # Don't fail validation
    except Exception as e:
        print_error(f"Error validating inventory: {str(e)}")
        return False

def main():
    """Run all validation checks."""
    print(f"\n{Colors.BOLD}SmartLP Deployment Validation{Colors.END}")
    print(f"{Colors.BOLD}Version 2.0.0 - Ansible-Based Deployment{Colors.END}\n")
    
    checks = [
        ("Ansible Installation", check_ansible),
        ("MongoDB Collection", check_mongodb_collection),
        ("Playbook Files", check_playbook_files),
        ("Python Code Updates", check_python_code),
        ("Documentation", check_documentation),
        ("Inventory Format", validate_inventory_format),
    ]
    
    results = {}
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print_error(f"Unexpected error in {check_name}: {str(e)}")
            results[check_name] = False
    
    # Print summary
    print_header("Validation Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check_name, result in results.items():
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"{check_name:.<50} {status}")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} checks passed{Colors.END}\n")
    
    if passed == total:
        print_success("All validation checks passed! ✨")
        print_success("Your SmartLP deployment system is ready to use.")
        print(f"\n{Colors.BOLD}Next Steps:{Colors.END}")
        print("1. Configure your inventory: ansible/inventories/default.yml")
        print("2. Update group variables: ansible/group_vars/all")
        print("3. Test deployment with a single entry")
        return 0
    else:
        print_error("Some validation checks failed.")
        print_error("Please address the issues above before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
