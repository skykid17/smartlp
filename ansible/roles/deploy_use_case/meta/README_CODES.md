### ansible/roles/deploy_use_case/meta/main.yml
```bash
cat > "/opt/SmartSOC/web/ansible/roles/deploy_use_case/meta/main.yml" <<"ENDMSG"
---

allow_duplicates: yes
dependencies:
   - role: "common"
ENDMSG
```
---
