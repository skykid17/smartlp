# SmartLP Ansible Deployment

This directory contains Ansible playbooks and tasks for deploying SmartLP log parsing configurations to Splunk.

## Overview

The SmartLP deployment system uses Ansible to manage Splunk configuration files instead of REST API `.refresh()` calls. Configurations are deployed to a single app location (`/etc/apps/smartlp/local/`) for simplified management.

## Architecture

### Deployment Flow

1. **API Request**: User triggers deployment via `/api/smartlp/deploy_config` endpoint
2. **Python Service**: `deploy_config_splunk()` method in `src/services/siem.py` invokes Ansible
3. **Ansible Playbook**: `deploy_smartlp.yml` orchestrates the deployment:
   - Queries MongoDB for log parsing entries by ID
   - Creates/updates props.conf and transforms.conf files
   - Manages configuration merging and duplicate detection
   - Reloads Splunk configuration via CLI
   - Updates MongoDB entry status to "Deployed"

### Configuration Structure

All SmartLP configurations are stored in a single app location:

```
/opt/splunk/etc/apps/smartlp/local/
├── props.conf       # Sourcetype configurations with REPORT directives
└── transforms.conf  # Regex transformations and field extractions
```

## Playbooks

### Main Playbook: `deploy_smartlp.yml`

Deploys SmartLP log parsing configurations to Splunk servers.

**Variables:**
- `entry_ids`: JSON array of entry IDs to deploy (required)
- `splunk_home`: Splunk installation directory (default: `/opt/splunk`)
- `splunk_user`: Splunk service user (default: `splunk`)
- `mongodb_host`: MongoDB host (default: `localhost`)
- `mongodb_db`: MongoDB database name (default: `smartlp`)

**Example Usage:**

```bash
# Deploy specific entries
ansible-playbook deploy_smartlp.yml \
  -i inventories/default.yml \
  -e 'entry_ids=["entry123","entry456"]' \
  -v

# Deploy with custom MongoDB connection
ansible-playbook deploy_smartlp.yml \
  -i inventories/production.yml \
  -e 'entry_ids=["entry789"]' \
  -e mongodb_host=mongo.example.com \
  -e mongodb_db=smartlp_prod
```

### Task File: `tasks/deploy_smartlp_config.yml`

Handles individual entry deployment in a loop. This task:
- Extracts entry fields from MongoDB document
- Generates transform names based on log type and entry ID
- Checks for existing configurations to prevent duplicates
- Creates or updates props.conf stanzas
- Creates or updates transforms.conf stanzas

## Inventory

### Default Inventory: `inventories/default.yml`

Configure your Splunk server information:

```yaml
all:
  children:
    splunk_servers:
      hosts:
        localhost:
          ansible_connection: local
          splunk_home: /opt/splunk
          splunk_user: splunk
          mongodb_host: localhost
```

### Creating Custom Inventories

For different environments (dev, staging, production):

```bash
# Create a new inventory
cp inventories/default.yml inventories/production.yml

# Edit with your production details
nano inventories/production.yml
```

## Group Variables

SmartLP-specific variables are defined in `group_vars/all`:

```yaml
smartlp:
  app_path: "{{ splunk.home }}/etc/apps/smartlp/local"
  mongodb:
    host: "{{ base.mongo_primary_ip | default('localhost') }}"
    port: 27017
    db: "smartlp"
    collection: "logs"
  config:
    props_conf: "{{ splunk.home }}/etc/apps/smartlp/local/props.conf"
    transforms_conf: "{{ splunk.home }}/etc/apps/smartlp/local/transforms.conf"
```

## Configuration Format

### props.conf Example

```ini
# ANSIBLE MANAGED BLOCK - syslog
[syslog]
REPORT-smartlp = linux_auth_entry123

# ANSIBLE MANAGED BLOCK - windows_event
[windows_event]
REPORT-smartlp = win_security_entry456
```

### transforms.conf Example

```ini
# ANSIBLE MANAGED BLOCK - linux_auth_entry123
[linux_auth_entry123]
REGEX = (?<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(?<host>\S+)\s+(?<process>\w+)\[(?<pid>\d+)\]:\s+(?<message>.*)

# ANSIBLE MANAGED BLOCK - win_security_entry456
[win_security_entry456]
REGEX = (?<EventCode>\d{4})\s+(?<Account>\S+)\s+(?<Status>\w+)
```

## Features

### Idempotency

The deployment process is idempotent - running the same playbook multiple times with the same entries will not create duplicates. Existing configurations are updated in place.

### Backup and Rollback

Before making changes, the playbook automatically creates timestamped backups:
- `props.conf.bak.{timestamp}`
- `transforms.conf.bak.{timestamp}`

### Configuration Merging

When deploying new entries:
- If a sourcetype stanza exists, the REPORT directive is updated
- If a transform exists, the REGEX is updated
- New stanzas are added with Ansible-managed markers

### Duplicate Detection

The playbook checks for existing configurations using:
- `grep` to search for existing stanzas
- Conditional task execution based on existence checks
- Ansible markers to track managed blocks

## Troubleshooting

### Common Issues

**Issue**: Ansible playbook not found
```
Solution: Ensure playbook path is correct in siem.py:
playbook_path = "/path/to/smartlp/ansible/deploy_smartlp.yml"
```

**Issue**: Permission denied when writing configs
```
Solution: Verify Splunk user permissions:
sudo chown -R splunk:splunk /opt/splunk/etc/apps/smartlp/
```

**Issue**: MongoDB connection failed
```
Solution: Check MongoDB connectivity and credentials:
- Verify mongo_primary_ip in group_vars/all
- Test connection: mongo --host <ip> --eval "db.stats()"
```

**Issue**: Configuration not applied after deployment
```
Solution: Manually reload Splunk:
/opt/splunk/bin/splunk reload deploy-server -auth admin:password
```

### Debug Mode

Run playbook with increased verbosity:

```bash
# Verbose output
ansible-playbook deploy_smartlp.yml -i inventories/default.yml -e 'entry_ids=["entry123"]' -vv

# Very verbose (shows task details)
ansible-playbook deploy_smartlp.yml -i inventories/default.yml -e 'entry_ids=["entry123"]' -vvv

# Extremely verbose (shows connection debugging)
ansible-playbook deploy_smartlp.yml -i inventories/default.yml -e 'entry_ids=["entry123"]' -vvvv
```

### Checking Deployment Status

1. **Check configuration files:**
```bash
cat /opt/splunk/etc/apps/smartlp/local/props.conf
cat /opt/splunk/etc/apps/smartlp/local/transforms.conf
```

2. **Verify MongoDB status:**
```javascript
use smartlp
db.logs.find({ id: "entry123" }, { status: 1 })
```

3. **Check Splunk btool:**
```bash
/opt/splunk/bin/splunk btool props list --debug
/opt/splunk/bin/splunk btool transforms list --debug
```

## Migration from Old System

The previous deployment approach used:
- Direct file writes from Python
- REST API `.refresh()` calls
- Multiple app locations (deployment-apps)

The new system:
- Uses Ansible for configuration management
- Relies on CLI reload instead of REST API
- Centralizes configs in single app location
- Provides better audit trail and version control

## Security Considerations

1. **Credentials**: Store sensitive data in Ansible Vault
```bash
ansible-vault encrypt_string 'password123' --name 'splunk_admin_password'
```

2. **SSH Keys**: Use key-based authentication for remote hosts
3. **Sudo Access**: Ensure proper privilege escalation settings
4. **File Permissions**: Maintain restrictive permissions on config files

## Best Practices

1. **Version Control**: Keep ansible playbooks in git
2. **Testing**: Test deployments in dev environment first
3. **Backups**: Verify backups are created before deployment
4. **Monitoring**: Monitor deployment logs for errors
5. **Documentation**: Update this README when making changes

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Ansible logs: `/var/log/ansible.log`
3. Review application logs: `docker logs smartlp`
4. Open an issue on GitHub: https://github.com/skykid17/smartlp/issues
