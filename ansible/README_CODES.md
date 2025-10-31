### ansible/9_smartsoc_prepare_config.yml
```bash
cat > "/opt/SmartSOC/web/ansible/9_smartsoc_prepare_config.yml" <<"ENDMSG"

# Deployment Server
- name: Prepare and update config in MongoDB
  hosts: deployment_server
  roles:
    - { role: update_config_mongodb, tags: update_config_mongodb }
ENDMSG
```
---
### ansible/9_smartsoc_smartuc.yml
```bash
cat > "/opt/SmartSOC/web/ansible/9_smartsoc_smartuc.yml" <<"ENDMSG"

# Search Head Apps - To create the smartsoc app for the very first time
- name: Search head apps
  hosts: search_head,deployer
  roles:
    - { role: configure_search_head_apps, tags: configure_search_head_apps }

# Deployment Server
- name: Deploy use case into search head
  hosts: deployment_server
  roles:
    - { role: deploy_use_case, tags: deploy_use_case }


ENDMSG
```
---
### ansible/9_smartsoc.yml
```bash
cat > "/opt/SmartSOC/web/ansible/9_smartsoc.yml" <<"ENDMSG"

# Search Head Apps - To create the smartsoc app for the very first time
- name: Search head apps
  hosts: search_head,deployer
  roles:
    - { role: configure_search_head_apps, tags: configure_search_head_apps }

# Deployment Server - To create the smartsoc app for the very first time
- name: Copy apps from ansible into deployment server
  hosts: deployment_server
  roles:
    - { role: apps_deployment_server, tags: apps_deployment_server }

# Deployment Server
- name: Add unparsed log transforms into deployment server
  hosts: deployment_server
  roles:
    - { role: unparsed_log_transforms, tags: unparsed_log_transforms }

ENDMSG
```
---
