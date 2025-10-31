### ansible/roles/update_config_mongodb/tasks/main.yml
```bash
cat > "/opt/SmartSOC/web/ansible/roles/update_config_mongodb/tasks/main.yml" <<"ENDMSG"
---

- name: Prepare and update config in MongoDB
  import_tasks: update_config_mongodb.yml
ENDMSG
```
---
### ansible/roles/update_config_mongodb/tasks/update_config_mongodb.yml
```bash
cat > "/opt/SmartSOC/web/ansible/roles/update_config_mongodb/tasks/update_config_mongodb.yml" <<"ENDMSG"
---

- include_tasks: "{{ playbook_dir }}/roles/common/tasks/update_mongodb_siem_config.yml"
ENDMSG
```
---
