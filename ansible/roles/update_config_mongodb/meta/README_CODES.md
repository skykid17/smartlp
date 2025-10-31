### ansible/roles/update_config_mongodb/meta/main.yml
```bash
cat > "/opt/SmartSOC/web/ansible/roles/update_config_mongodb/meta/main.yml" <<"ENDMSG"
---

allow_duplicates: yes
dependencies:
   - role: "common"
ENDMSG
```
---
