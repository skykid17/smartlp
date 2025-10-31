### ansible/inventories/emax_test.yml
```bash
cat > "/opt/SmartSOC/web/ansible/inventories/emax_test.yml" <<"ENDMSG"
---
all:
 children:
  search_head:
    hosts:
      #site 1 searchhead
      192.168.30.52:
        host_suffix: "CLV030VLSPSCH01"
        host_site: '1'
      192.168.30.53:
        host_suffix: "CLV030VLSPSCH02"
        host_site: '1'
      192.168.30.54:
        host_suffix: "CLV030VLSPSCH03"
        host_site: '1'

  deployment_server:
    hosts:
      192.168.30.51:
        host_suffix: "CLV030VLSPMGT01"
        host_site: '1'

  deployer:
    hosts:
      192.168.30.51:
        host_suffix: "CLV030VLSPMGT01"
        host_site: '1'

  heavy_forwarder:
    hosts:
      192.168.30.62:
        host_suffix: "CLV030VLSPHVF01"
        host_site: '1'
      192.168.30.63:
        host_suffix: "CLV030VLSPHVF02"
        host_site: '1'

ENDMSG
```
---
