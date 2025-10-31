### ansible/roles/apps_deployment_server/meta/main.yml
```bash
cat > "/opt/SmartSOC/web/ansible/roles/apps_deployment_server/meta/main.yml" <<"ENDMSG"
---

allow_duplicates: yes
dependencies:
   - role: "common"
ENDMSG
```
---
