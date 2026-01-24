# SmartLP Deployment Migration Guide

## Overview

This document describes the migration from the old deployment approach to the new Ansible-based system for SmartLP log parsing configurations.

## What Changed

### Old Deployment Approach

The previous system used:

1. **Direct File Writes**: Python service wrote directly to Splunk configuration files
   - Path: `/etc/system/local/props.conf` and `/etc/system/local/transforms.conf`
   - Used Python's `tempfile` and `os.replace()` for atomic writes
   
2. **REST API Refresh**: Configuration reload used Splunk REST API
   - Primary method: `POST admin/_rcvr`
   - Fallback: `.refresh()` calls on `service.confs['props']` and `service.confs['transforms']`
   
3. **File Backup**: Manual backup using `shutil.copy2()`
   - Backup files: `props.conf.bak` and `transforms.conf.bak`
   - Rollback on failure

### New Deployment Approach

The new system uses:

1. **Ansible Playbooks**: Configuration deployment orchestrated by Ansible
   - Path: `/opt/splunk/etc/apps/smartlp/local/props.conf` and `transforms.conf`
   - Uses Ansible modules (`blockinfile`, `ini_file`, `lineinfile`)
   
2. **CLI Reload**: Configuration reload via Splunk CLI
   - Command: `/opt/splunk/bin/splunk reload deploy-server`
   - No REST API `.refresh()` calls
   
3. **Ansible Backup**: Timestamped backups via Ansible `copy` module
   - Backup files: `props.conf.bak.{epoch}` and `transforms.conf.bak.{epoch}`
   - Better audit trail

## Code Changes

### src/services/siem.py

#### deploy_config_splunk() Method

**Before:**
```python
def deploy_config_splunk(self, entry_ids: List[str]) -> Tuple[bool, str]:
    # Generate configuration
    config_dict = self.create_config_splunk(entry_ids)
    
    # Write files directly using tempfile
    with tempfile.NamedTemporaryFile(...) as tmp_props:
        tmp_props.write(props_content)
        os.replace(tmp_props.name, PROPS_CONF_PATH)
    
    # Reload via REST API
    reload_success = self._reload_splunk_config()
```

**After:**
```python
def deploy_config_splunk(self, entry_ids: List[str]) -> Tuple[bool, str]:
    # Prepare entry IDs as JSON
    entry_ids_list = f'[{entry_ids_json}]'
    
    # Execute Ansible playbook
    ansible_cmd = [
        "ansible-playbook",
        playbook_path,
        "-i", inventory_path,
        "-e", f"entry_ids={entry_ids_list}"
    ]
    
    result = subprocess.run(ansible_cmd, ...)
```

#### _reload_splunk_config() Method

**Before:**
```python
def _reload_splunk_config(self) -> bool:
    # Try REST API first
    self._connection.post('admin/_rcvr', output_mode='json')
    
    # Fallback to .refresh()
    service.confs['props'].refresh()
    service.confs['transforms'].refresh()
```

**After:**
```python
def _reload_splunk_config(self) -> bool:
    # Use Splunk CLI
    reload_cmd = [
        "/opt/splunk/bin/splunk",
        "reload",
        "deploy-server"
    ]
    
    result = subprocess.run(reload_cmd, ...)
```

#### Removed Methods

- `_rollback_config_files()`: No longer needed, Ansible handles rollback

## Configuration Changes

### File Paths

| Component | Old Path | New Path |
|-----------|----------|----------|
| props.conf | `/etc/system/local/props.conf` | `/opt/splunk/etc/apps/smartlp/local/props.conf` |
| transforms.conf | `/etc/system/local/transforms.conf` | `/opt/splunk/etc/apps/smartlp/local/transforms.conf` |

### Configuration Format

The configuration format remains the same, but management is different:

**props.conf:**
```ini
# Old: Manual stanza management
[sourcetype]
REPORT-smartsoc = transform_name

# New: Ansible-managed blocks
# BEGIN ANSIBLE MANAGED BLOCK - sourcetype
[sourcetype]
REPORT-smartlp = transform_name
# END ANSIBLE MANAGED BLOCK - sourcetype
```

**transforms.conf:**
```ini
# Old: Direct write of stanzas
[transform_name]
REGEX = (?<field>pattern)

# New: Ansible-managed blocks
# BEGIN ANSIBLE MANAGED BLOCK - transform_name
[transform_name]
REGEX = (?<field>pattern)
# END ANSIBLE MANAGED BLOCK - transform_name
```

## Migration Steps

### Prerequisites

1. **Install Ansible**: Ensure Ansible is installed on the system
   ```bash
   pip install ansible
   ```

2. **Install Ansible MongoDB Collection**:
   ```bash
   ansible-galaxy collection install community.mongodb
   ```

3. **Configure Inventory**: Update `ansible/inventories/default.yml` with your Splunk server details

4. **Configure Variables**: Update `ansible/group_vars/all` with environment-specific settings

### Step-by-Step Migration

#### 1. Backup Current Configurations

Before migrating, backup your current configuration files:

```bash
# Backup old configs
cp /etc/system/local/props.conf /etc/system/local/props.conf.pre-migration
cp /etc/system/local/transforms.conf /etc/system/local/transforms.conf.pre-migration
```

#### 2. Create SmartLP App Directory

```bash
# Create directory structure
sudo mkdir -p /opt/splunk/etc/apps/smartlp/local
sudo chown -R splunk:splunk /opt/splunk/etc/apps/smartlp
```

#### 3. Migrate Existing Configurations

Copy existing configurations to the new location:

```bash
# Copy existing configs if they exist
if [ -f /etc/system/local/props.conf ]; then
    sudo cp /etc/system/local/props.conf /opt/splunk/etc/apps/smartlp/local/props.conf
fi

if [ -f /etc/system/local/transforms.conf ]; then
    sudo cp /etc/system/local/transforms.conf /opt/splunk/etc/apps/smartlp/local/transforms.conf
fi
```

#### 4. Test Ansible Deployment

Test the new deployment system with a single entry:

```bash
# Navigate to ansible directory
cd /path/to/smartlp/ansible

# Test with dry-run
ansible-playbook deploy_smartlp.yml \
  -i inventories/default.yml \
  -e 'entry_ids=["test_entry"]' \
  --check

# Deploy if dry-run succeeds
ansible-playbook deploy_smartlp.yml \
  -i inventories/default.yml \
  -e 'entry_ids=["test_entry"]' \
  -v
```

#### 5. Update Application Code

The application code has already been updated in this PR. Deploy the new version:

```bash
# Pull latest changes
git pull origin copilot/refactor-splunk-log-parsing

# Restart application
docker-compose restart smartlp
```

#### 6. Verify Deployment

Check that configurations are deployed correctly:

```bash
# Check configuration files
cat /opt/splunk/etc/apps/smartlp/local/props.conf
cat /opt/splunk/etc/apps/smartlp/local/transforms.conf

# Verify Splunk recognizes the configs
/opt/splunk/bin/splunk btool props list | grep smartlp
/opt/splunk/bin/splunk btool transforms list | grep smartlp
```

#### 7. Test End-to-End Flow

1. Log into SmartLP UI
2. Select one or more entries with "Matched" status
3. Click "Deploy to SIEM"
4. Verify deployment success message
5. Check MongoDB status updated to "Deployed"
6. Verify Splunk configuration files updated

## Rollback Plan

If issues occur during migration:

### Quick Rollback

1. **Restore old configurations:**
```bash
sudo cp /etc/system/local/props.conf.pre-migration /etc/system/local/props.conf
sudo cp /etc/system/local/transforms.conf.pre-migration /etc/system/local/transforms.conf
```

2. **Revert application code:**
```bash
git checkout main
docker-compose restart smartlp
```

3. **Reload Splunk:**
```bash
/opt/splunk/bin/splunk reload deploy-server -auth admin:password
```

### Rollback from Ansible Backups

If you need to rollback from Ansible-created backups:

```bash
# List available backups
ls -la /opt/splunk/etc/apps/smartlp/local/*.bak.*

# Restore from specific backup
sudo cp /opt/splunk/etc/apps/smartlp/local/props.conf.bak.1640000000 \
       /opt/splunk/etc/apps/smartlp/local/props.conf

sudo cp /opt/splunk/etc/apps/smartlp/local/transforms.conf.bak.1640000000 \
       /opt/splunk/etc/apps/smartlp/local/transforms.conf

# Reload Splunk
/opt/splunk/bin/splunk reload deploy-server
```

## Troubleshooting

### Common Issues During Migration

#### Issue: Ansible Not Found

**Symptom:**
```
Error deploying Splunk configuration via Ansible
Ansible playbook not found: /path/to/ansible/deploy_smartlp.yml
```

**Solution:**
Verify Ansible is installed and playbook path is correct:
```bash
which ansible-playbook
ls -la /home/runner/work/smartlp/smartlp/ansible/deploy_smartlp.yml
```

#### Issue: Permission Denied

**Symptom:**
```
TASK [Ensure smartlp app directory exists] ******
fatal: [localhost]: FAILED! => {"changed": false, "msg": "Permission denied"}
```

**Solution:**
Ensure proper permissions and become settings:
```bash
sudo chown -R splunk:splunk /opt/splunk/etc/apps/smartlp
```

#### Issue: MongoDB Connection Failed

**Symptom:**
```
TASK [Query MongoDB for log parsing entries] ******
fatal: [localhost]: FAILED! => {"msg": "Failed to connect to MongoDB"}
```

**Solution:**
Verify MongoDB is accessible:
```bash
# Test connection
mongo --host localhost --eval "db.stats()"

# Update group_vars/all with correct MongoDB IP
nano ansible/group_vars/all
```

#### Issue: Configuration Not Applied

**Symptom:**
Deployment succeeds but Splunk doesn't recognize new configurations.

**Solution:**
1. Check btool output:
```bash
/opt/splunk/bin/splunk btool props list --debug
/opt/splunk/bin/splunk btool transforms list --debug
```

2. Manually reload Splunk:
```bash
/opt/splunk/bin/splunk reload deploy-server
```

3. Restart Splunk if necessary:
```bash
/opt/splunk/bin/splunk restart
```

## Benefits of New Approach

1. **Better Separation of Concerns**: Configuration management handled by Ansible, not Python
2. **Audit Trail**: Ansible logs provide detailed deployment history
3. **Idempotency**: Safe to run multiple times without duplicates
4. **Infrastructure as Code**: Configurations managed as code, version controlled
5. **No REST API Dependencies**: Eliminates `.refresh()` calls and REST API issues
6. **Scalability**: Easy to deploy to multiple Splunk servers
7. **Consistency**: Same deployment approach as other infrastructure automation

## Support

For migration issues or questions:

1. Review this migration guide
2. Check the main Ansible README: `ansible/README.md`
3. Review application logs: `docker logs smartlp`
4. Open an issue: https://github.com/skykid17/smartlp/issues

## References

- [Ansible Documentation](https://docs.ansible.com/)
- [Splunk Configuration Files](https://docs.splunk.com/Documentation/Splunk/latest/Admin/Aboutconfigurationfiles)
- [SmartLP Ansible README](README.md)
