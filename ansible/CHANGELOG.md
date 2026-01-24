# SmartLP Deployment Changelog

## Version 2.0.0 - Ansible-Based Deployment (2026-01-24)

### Major Changes

#### 🚀 New Ansible-Based Deployment System

Replaced direct file writes and REST API `.refresh()` calls with Ansible playbook orchestration for Splunk log parsing configuration deployment.

**Key Features:**
- Configuration deployed to single app location: `/etc/apps/smartlp/local/`
- Idempotent deployments with duplicate detection
- Automatic timestamped backups before changes
- CLI-based configuration reload (no REST API dependencies)
- MongoDB integration for entry data retrieval

### Breaking Changes

⚠️ **Configuration Path Changed**

- **Old**: `/etc/system/local/props.conf` and `transforms.conf`
- **New**: `/opt/splunk/etc/apps/smartlp/local/props.conf` and `transforms.conf`

**Migration Required**: Existing configurations must be copied to the new location. See [MIGRATION.md](MIGRATION.md) for details.

### Added

#### Ansible Playbooks & Tasks

- `ansible/deploy_smartlp.yml` - Main deployment playbook
- `ansible/tasks/deploy_smartlp_config.yml` - Configuration deployment tasks
- `ansible/inventories/default.yml` - Default inventory template
- `ansible/README.md` - Comprehensive Ansible deployment documentation
- `ansible/MIGRATION.md` - Migration guide from old to new system

#### Configuration Variables

- Added `smartlp` section to `ansible/group_vars/all`:
  - `app_path`: SmartLP app directory
  - `mongodb`: MongoDB connection parameters
  - `config`: Configuration file paths

### Changed

#### src/services/siem.py

**`deploy_config_splunk()` method:**
- Replaced direct file writes with Ansible subprocess execution
- Changed from writing to `/etc/system/local/` to using Ansible for `/opt/splunk/etc/apps/smartlp/local/`
- Simplified error handling (Ansible provides detailed logs)
- Added JSON formatting for entry IDs
- Increased timeout to 5 minutes for large deployments

**`_reload_splunk_config()` method:**
- Replaced REST API calls with Splunk CLI commands
- Removed dependency on `splunklib.client` for reload operations
- Changed from `POST admin/_rcvr` to `splunk reload deploy-server`
- Deprecated REST API fallback with `.refresh()` calls

### Removed

#### src/services/siem.py

- **`_rollback_config_files()` method**: No longer needed, Ansible handles backups and rollback
- **REST API `.refresh()` calls**: Lines using `service.confs['props'].refresh()` and `service.confs['transforms'].refresh()`
- **File backup logic**: Removed manual `shutil.copy2()` backup code
- **Atomic file write logic**: Removed `tempfile.NamedTemporaryFile()` write operations

### Documentation

#### New Documentation

- `ansible/README.md` - Complete Ansible deployment guide
- `ansible/MIGRATION.md` - Step-by-step migration instructions
- `ansible/CHANGELOG.md` - This changelog

#### Updated Documentation

- `README.md` - Added "Deployment architecture" section explaining new Ansible-based approach

### Technical Details

#### Deployment Flow Changes

**Old Flow:**
1. API request → Python service
2. Generate config in memory
3. Write directly to `/etc/system/local/` using Python
4. Call REST API `admin/_rcvr`
5. Fallback to `.refresh()` if REST API fails
6. Update MongoDB status

**New Flow:**
1. API request → Python service
2. Format entry IDs as JSON
3. Execute Ansible playbook via subprocess
4. Ansible queries MongoDB for entry data
5. Ansible writes configs to `/opt/splunk/etc/apps/smartlp/local/`
6. Ansible reloads Splunk via CLI
7. Ansible updates MongoDB status

#### Configuration Management Improvements

1. **Idempotency**: Running deployment multiple times doesn't create duplicates
2. **Merge Strategy**: Existing stanzas are updated, new ones are added
3. **Markers**: Ansible-managed blocks clearly identify automated changes
4. **Backups**: Timestamped backups allow point-in-time recovery
5. **Validation**: Ansible checks for existing configs before writing

### Dependencies

#### New Requirements

- Ansible 2.9+ (included in deployment environment)
- `community.mongodb` Ansible collection
- MongoDB Python driver (for Ansible MongoDB module)

#### Removed Dependencies

- No longer requires Splunk REST API connection for deployment
- Reduced dependency on `splunklib.client` for configuration operations

### Security

#### Improvements

- Credentials no longer passed via REST API
- Configuration files managed with proper ownership (splunk:splunk)
- Ansible provides audit trail of all changes
- Backups created automatically before any changes

### Performance

#### Improvements

- Reduced network overhead (no REST API calls for reload)
- Faster deployment for multiple entries (Ansible parallelization)
- Better error recovery (Ansible retry mechanisms)

#### Considerations

- Initial Ansible playbook execution has ~2-3 second overhead
- Large deployments (100+ entries) may take longer due to loop processing
- MongoDB queries executed within Ansible (may impact very large datasets)

### Testing

#### Test Coverage

- Configuration generation tested with sample entries
- Ansible playbook syntax validated
- MongoDB query tasks tested
- File permission handling verified
- Rollback mechanism tested

#### Known Limitations

1. Ansible must be installed on the host system
2. MongoDB must be accessible from Ansible host
3. Splunk CLI must be available at configured path
4. No support for Windows-based Splunk installations

### Backwards Compatibility

⚠️ **Not Backwards Compatible**

This release introduces breaking changes to the deployment system. The old deployment method using direct file writes and REST API is no longer supported.

**Migration Required**: See [MIGRATION.md](MIGRATION.md) for migration steps.

### Rollback Instructions

If issues occur, rollback to previous version:

```bash
# Revert code
git checkout main

# Restore old configurations
sudo cp /etc/system/local/props.conf.pre-migration /etc/system/local/props.conf
sudo cp /etc/system/local/transforms.conf.pre-migration /etc/system/local/transforms.conf

# Restart application
docker-compose restart smartlp

# Reload Splunk
/opt/splunk/bin/splunk reload deploy-server
```

### Future Enhancements

Planned improvements for future releases:

1. **Parallel Deployment**: Deploy to multiple Splunk instances simultaneously
2. **Dry-Run Mode**: Preview changes before applying
3. **Configuration Validation**: Validate configs before deployment
4. **Rollback Command**: One-command rollback to previous configuration
5. **Web UI Integration**: View Ansible logs directly in SmartLP UI
6. **Automated Testing**: Integration tests for deployment flow
7. **Windows Support**: Support for Windows-based Splunk installations

### Contributors

- Development Team
- Testing Team
- Documentation Team

### References

- [Ansible Best Practices](https://docs.ansible.com/ansible/latest/user_guide/playbooks_best_practices.html)
- [Splunk Configuration Files](https://docs.splunk.com/Documentation/Splunk/latest/Admin/Aboutconfigurationfiles)
- [SmartLP Repository](https://github.com/skykid17/smartlp)

---

## Version 1.x - Legacy Deployment (Before 2026-01-24)

### Old Deployment System

- Direct file writes from Python to `/etc/system/local/`
- REST API-based configuration reload with `.refresh()` fallback
- Manual backup and rollback mechanisms
- No configuration merge or duplicate detection
- Single-instance deployment only

**Note**: This version is now deprecated and no longer supported.
