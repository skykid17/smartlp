### ansible/roles/unparsed_log_transforms/tasks/main.yml
```bash
cat > "/opt/SmartSOC/web/ansible/roles/unparsed_log_transforms/tasks/main.yml" <<"ENDMSG"
---

- name: Update unparsed log transforms in deployment apps
  import_tasks: update_unparsed_log_transforms.yml
ENDMSG
```
---
### ansible/roles/unparsed_log_transforms/tasks/update_unparsed_log_transforms.yml
```bash
cat > "/opt/SmartSOC/web/ansible/roles/unparsed_log_transforms/tasks/update_unparsed_log_transforms.yml" <<"ENDMSG"
---

- include_tasks: "{{ playbook_dir }}/roles/common/tasks/update_unparsed_log_transforms.yml"
ENDMSG
```
---
