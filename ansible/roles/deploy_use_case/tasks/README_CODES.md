### ansible/roles/deploy_use_case/tasks/deploy_use_case.yml
```bash
cat > "/opt/SmartSOC/web/ansible/roles/deploy_use_case/tasks/deploy_use_case.yml" <<"ENDMSG"
---

- include_tasks: "{{ playbook_dir }}/roles/common/tasks/deploy_use_case.yml"
ENDMSG
```
---
### ansible/roles/deploy_use_case/tasks/main.yml
```bash
cat > "/opt/SmartSOC/web/ansible/roles/deploy_use_case/tasks/main.yml" <<"ENDMSG"
---

- name: Deploy use case into search head
  import_tasks: deploy_use_case.yml
ENDMSG
```
---
