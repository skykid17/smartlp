### ansible/group_vars/all
```bash
cat > "/opt/SmartSOC/web/ansible/group_vars/all" <<"ENDMSG"
---

##############################
##  BASE
##############################

sanlist: []

ansible_become_password: 'STEcyberlab12#'

base:
  general:
    password: 'P@ssw0rd12345' #Need to comply to password complexity
  company_name: 'ws'
  fqdn: 'ws.gov.sg'

  prod_inf: 'ens192'

  packages:
    - "net-tools"

  # Ansible Tower Tmp Directory
####!  awx_tmp_dir: '/opt/tmp/'
  awx_tmp_dir: '/tmp/'

  mongo_primary_ip: '192.168.30.93'

##############################
##  SPLUNK
##############################

splunk:
  ports:
    web: '8000'
    nat_web: '443'
    #local_mgmt: '8090'
    mgmt: '8089'
    indexer_receiving: '9997'
    cluster_replication: '9887'
    shcluster_replication: '9777'
    kv_store: '8191'

  package_linux: "splunk-9.4.0-6b4ebe426ca6.x86_64.rpm"
  package_linux_uf: "splunkforwarder-9.3.1-0b8d769cb912.x86_64.rpm"
  package_win_uf: "splunkforwarder-9.3.1-0b8d769cb912-x64-release.msi"
  package_file: "{% if 'universal_forwarder' in group_names %}splunkforwarder-9.1.2-b6b9c8185839.x86_64.rpm{% else %}splunk-9.4.0-6b4ebe426ca6.x86_64.rpm{% endif %}"

  home: "{% if 'universal_forwarder' in group_names %}/opt/splunkforwarder{% else %}/opt/splunk{% endif %}"
  bin: "{% if 'universal_forwarder' in group_names %}/opt/splunkforwarder/bin{% else %}/opt/splunk/bin{% endif %}"
  pid: '/opt/splunk/var/run/splunkd.pid'
  service_name: 'splunk'
  systemd: 'true'

  nix:
    group: "{% if 'universal_forwarder' in group_names %}splunkfwd{% else %}splunk{% endif %}"
    user: "{% if 'universal_forwarder' in group_names %}splunkfwd{% else %}splunk{% endif %}"
    svc_account: 'root'

  admin:
    username: 'spladmin'
    password: "{{ base.general.password }}"

  pass4SymmKey: "{{ base.general.password }}"

  web:
    session_timeout: '10'
    inactivity_timeout: '5'
    login_banner: 'Use of this System is restricted to authorised users only.  User activity may be monitored and/or recorded.  Anyone using this network expressly consents to such monitoring and/or recording.  BE ADVISED: if possible criminal activity is detected, these records, along with certain personal information, may be provided to law enforcement officials.'
    sh_token: 'eyJraWQiOiJzcGx1bmsuc2VjcmV0IiwiYWxnIjoiSFM1MTIiLCJ2ZXIiOiJ2MiIsInR0eXAiOiJzdGF0aWMifQ.eyJpc3MiOiJzcGxhZG1pbiBmcm9tIENMVjAzMFZMU1BTQ0gwMSIsInN1YiI6InNwbGFkbWluIiwiYXVkIjoicmV0cmlldmUgdW5wYXJzZWQgbG9ncyIsImlkcCI6IlNwbHVuayIsImp0aSI6IjhhNzhmYTE5ODkyOGI4MjRmZmVjYWY5NjhiNWQ4MjQxOTc4ZTlkZDlmMGEwMDFmOThjYWMyMGEwNjc1ZjNkNWEiLCJpYXQiOjE3NDA0NzUwMDksImV4cCI6MTc2NzE5Njc0MiwibmJyIjoxNzQwNDc1MDA5fQ.DbCBRxMsGaRAF0pWi3BFesEWOOcu5VkQVrAZpB6er9dME8t4RZRFoHflf-9Jk2zHd6-wTHWQRYmOgnbMmR2INQ'

  search_head_captain_ip: "{% if(groups['search_head'] is defined and groups['search_head']|length) %}{{ groups['search_head']|first }}{% endif%}"
  license_master_ip: "{% if(groups['license_master'] is defined and groups['license_master']|length) %}{{ groups['license_master']|first }}{% endif%}"
  monitoring_console_ip: "{% if(groups['monitoring_console'] is defined and groups['monitoring_console']|length) %}{{ groups['monitoring_console']|first }}{% endif%}"
  deployment_server_ip: "{% if(groups['deployment_server'] is defined and groups['deployment_server']|length) %}{{ groups['deployment_server']|first }}{% endif%}"
  cluster_master_ip: "{% if(groups['cluster_master'] is defined and groups['cluster_master']|length) %}{{ groups['cluster_master']|first }}{% endif%}"

  cert:
    # OU
    organizational_unit_name: 'WS'
    # O
    organization_name: 'WS'
    # L
    locality_name: 'SG'
    # ST
    state_or_province_name: 'SINGAPORE'
    # C
    country_name: 'SG'
    cert_URL: '192.168.2.110/tmp/'

  indexer:
    #vip: '192.168.30.71'
    vip: ''

##############################
##   INDEXES
##############################

  indexes: # THIS WILL BE USED TO CREATE THE INDEXES
    windows:
    linux:
    switches:
      frozenTimePeriodInSecs: '1000'
    web_servers:
      frozenTimePeriodInSecs: '1000'
  storage_information:
    frozenTimePeriodInSecs: '31556952'
    maxTotalDataSizeMB: '100000'
    homePath: 'volume:hot_warm/$_index_name/db'
    coldPath: 'volume:cold/$_index_name/colddb'
    thawedPath: '/$SPLUNK_HOME/thaw/$_index_name/thaweddb'
    summaryHomePath: 'volume:cold/$_index_name/summary'
    tstatsHomePath: 'volume:cold/$_index_name/datamodel_summary'
    coldToFrozenDir: '/$SPLUNK_HOME/archiver/$_index_name/frozen'
    volume:
      hot_warm:
        path: '$SPLUNK_HOME/hot_warm'
        maxVolumeDataSizeMB: '4590000'
      cold:
        path: '$SPLUNK_HOME/cold'
        maxVolumeDataSizeMB: '13680000'


##############################
##   SSL
##############################
  ssl:
    cacert_name: 'CA'
    requireClientCert: 'true'
    sslPassword: "{{ base.general.password }}"
    cipherSuite: 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-SHA384'
    ecdhCurves: 'prime256v1, secp384r1, secp521r1'

##############################
##   CLUSTERING - DO NOT EDIT
##############################

  cluster:
    label: "{{ base.company_name }}_idx_cluster"
    master_url: "{% if(groups['cluster_master'] is defined and groups['cluster_master']|length) %}{{ groups['cluster_master']|first }}{% endif %}"
    replication_factor: "{% if(groups['cluster_master'] is defined and 'cluster_master' in group_names) %}{% if(groups['indexer']|length) > 3 %}3{% elif(groups['indexer']|length) == 2 %}2{% else %}1{% endif %}{% endif %}"
    search_factor: "{% if(groups['cluster_master'] is defined and 'cluster_master' in group_names) %}{% if(groups['indexer']|length) > 3 %}3{% elif(groups['indexer']|length) == 2 %}2{% else %}1{% endif %}{% endif %}"
    site_replication_factor: "{% if(groups['cluster_master'] is defined and 'cluster_master' in group_names) %}{% if(groups['indexer']|length) > 3 %}origin:2,total:3{% elif(groups['indexer']|length) == 2 %}origin:1,total:2{% else %}origin:1,total:1{% endif %}{% endif %}"
    site_search_factor: "{% if(groups['cluster_master'] is defined and 'cluster_master' in group_names) %}{% if(groups['indexer']|length) > 3 %}origin:2,total:3{% elif(groups['indexer']|length) == 2 %}origin:1,total:2{% else %}origin:1,total:1{% endif %}{% endif %}"

##############################
##   SHCLUSTERING - DO NOT EDIT
##############################

  shcluster:
    label: "{{ base.company_name }}_sh_cluster"
    deployer_url: "{% if(groups['deployer'] is defined and groups['deployer']|length) %}{{ groups['deployer']|first }}{% endif %}"
    replication_factor: "{% if(groups['search_head'] is defined and groups['search_head']|length > 2) %}2{% else %}1{% endif %}"

##############################
##   KEEPALIVE
##############################
  keepalived:
    shared_iface: "{{ base.prod_inf }}"
    router_id: '50'
    priority: '100'
    backup_priority: '99'
    auth_pass: "{{ base.general.password }}"
    shared_ip: '192.168.30.61'
    check_process: 'splunkd'

##############################
##   HEC
##############################
  hec:
    configure_on: 'cluster_master' #Values: aio, indexer, cluster_master, heavy forwarder, deployment_server
    disabled: 1
    default_index: 'main'
    allowed_indexes: '*'
    dedicatedIoThreads: 10
    maxSockets: 16160
    maxThreads: 16160
    maxEventSize: '100MB'
    queueSize: '5GB'
    ssl: 'enabled'
    sslPassword: "{{ base.general.password }}"

##############################
##   LDAP
##############################
  ldap:
    - strategyName: 'lab_ldap1'
      parameters:
        - SSLEnabled: '0'
        - host: '1.1.1.1'
        - port: '389'
        - bindDN: 'cn=test,cn=users,dc=hellocompany,dc=com'
        - bindDNpassword: "{{ base.general.password }}"
        - emailAttribute: 'mail'
        - groupBaseDN: 'cn=users,dc=hellocompany,dc=com'
        - groupMappingAttribute: 'dn'
        - groupMemberAttribute: 'member'
        - groupNameAttribute: 'cn'
        - userBaseDN: 'cn=users,dc=hellocompany,dc=com'
        - userNameAttribute: 'samaccountname'
        - realNameAttribute: 'cn'
      roleMap:
        - admin: 'admin'
    - strategyName: 'lab_ldap2'
      parameters:
        - SSLEnabled: '0'
        - host: '2.2.2.2'
        - port: '389'
        - bindDN: 'cn=test,cn=users,dc=hellocompany,dc=com'
        - bindDNpassword: "{{ base.general.password }}"
        - emailAttribute: 'mail'
        - groupBaseDN: 'cn=users,dc=hellocompany,dc=com'
        - groupMappingAttribute: 'dn'
        - groupMemberAttribute: 'member'
        - groupNameAttribute: 'cn'
        - userBaseDN: 'cn=users,dc=hellocompany,dc=com'
        - userNameAttribute: 'samaccountname'
        - realNameAttribute: 'cn'
      roleMap:
        - admin: 'admin'

##############################
##   SAML
##############################
  saml:
    - entityId: 'lab_saml'
      parameters:
        fqdn: 'https://{{ base.fqdn }}'
        idpSLOUrl: 'https://loginfs.hellocompany.com/adfs/ls/?wa=wsignout1.0'
        idpSSOUrl: 'https://loginfs.hellocompany.com/adfs/ls/'
        inboundSignatureAlgorithm: 'RSA-SHA1;RSA-SHA256'
        issuerId: 'http://loginfs.hellocompany.com/adfs/services/trust'
        redirectPort: '443'
        replicateCertificates: 'true'
        signAuthnRequest: 'false'
        signatureAlgorithm: 'RSA-SHA1'
        signedAssertion: 'true'
        sloBinding: 'HTTP-POST'
        ssoBinding: 'HTTP-POST'
        realName: 'http://schemas.microsoft.com/ws/2008/06/identity/claims/name'
        role: 'http://schemas.microsoft.com/ws/2008/06/identity/claims/role'
      roleMap:
        - admin: 'admin'

##############################
##   UF_Windows Configuration
##############################

windows:
  deployment_server: 192.168.56.24
  receiving_indexer: 192.168.56.21
  packagedir: 'E:\splunkforwarder-8.2.1.msi'
  installdir: 'E:\SplunkUniversalForwarder'
  package_file: 'splunkforwarder-8.2.1.msi'
  WINEVENTLOG_APP_ENABLE: 1
  WINEVENTLOG_SEC_ENABLE: 1
  WINEVENTLOG_SYS_ENABLE: 1
  WINEVENTLOG_FWD_ENABLE: 0
  WINEVENTLOG_SET_ENABLE: 0
  LAUNCHSPLUNK: 1

##############################
##   Audit
##############################

audit:
  LMI_IP: '192.168.56.51'

##############################
##   Vault
##############################

#secret_password: "{{ vault_password }}"
ENDMSG
```
---
