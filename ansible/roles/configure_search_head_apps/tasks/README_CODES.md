### ansible/roles/configure_search_head_apps/tasks/configure_search_head_apps.yml
```bash
cat > "/opt/SmartSOC/web/ansible/roles/configure_search_head_apps/tasks/configure_search_head_apps.yml" <<"ENDMSG"
---

- include_tasks: "{{ playbook_dir }}/roles/common/tasks/configure_search_head_apps.yml"
  when:
    - "ansible_host in groups['deployer'] or (groups['deployer'] | length<1 and ansible_host in groups['search_head'])"
ENDMSG
```
---
### ansible/roles/configure_search_head_apps/tasks/main.yml
```bash
cat > "/opt/SmartSOC/web/ansible/roles/configure_search_head_apps/tasks/main.yml" <<"ENDMSG"
---

- name: Update search head apps
  import_tasks: configure_search_head_apps.yml
ENDMSG
```
---
