### ansible/roles/apps_deployment_server/tasks/main.yml
```bash
cat > "/opt/SmartSOC/web/ansible/roles/apps_deployment_server/tasks/main.yml" <<"ENDMSG"
---

- name: Update deployment apps
  import_tasks: update_deployment_apps.yml
ENDMSG
```
---
### ansible/roles/apps_deployment_server/tasks/update_deployment_apps.yml
```bash
cat > "/opt/SmartSOC/web/ansible/roles/apps_deployment_server/tasks/update_deployment_apps.yml" <<"ENDMSG"
---

- include_tasks: "{{ playbook_dir }}/roles/common/tasks/update_deployment_apps.yml"
ENDMSG
```
---
