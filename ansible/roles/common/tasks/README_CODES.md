### ansible/roles/common/tasks/configure_search_head_apps.yml
```bash
cat > "/opt/SmartSOC/web/ansible/roles/common/tasks/configure_search_head_apps.yml" <<"ENDMSG"
---

- name: Set the path
  set_fact:
    apps_path: "{{ splunk.home }}/etc/{% if ansible_host in groups['deployer'] and groups['deployer'] | length>0 %}shcluster/{% endif %}apps/"

#- name: Copy tar rpm file to server
#  copy:
#    src: "{{ playbook_dir }}/roles/common/files/installer/tar.rpm"
#    dest: /tmp/tar.rpm

#- name: Install tar
#  become: true
#  yum:
#    name: /tmp/tar.rpm
#    state: present
#  ignore_errors: True

- name: Find all directories
  become: true
  become_user: "{{ splunk.nix.user }}"
  find:
    paths: "{{playbook_dir}}/roles/common/files/apps_search_head/apps/"
    patterns: "*"
    file_type: directory
  register: directory_results

- name: Find all files ending with .tgz
  become: true
  become_user: "{{ splunk.nix.user }}"
  find:
    paths: "{{playbook_dir}}/roles/common/files/apps_search_head/apps/"
    patterns: "*.tgz"
  register: tgzfile_results

- name: Copy directory apps
  become: true
  become_user: "{{ splunk.nix.user }}"
  copy:
    src: "{{ item.path }}"
    dest: "{{ apps_path }}"
    owner: "{{ splunk.nix.user }}"
    group: "{{ splunk.nix.group }}"
    mode: 0700
  loop: "{{ directory_results.files }}"
  register: deploy_apps

- name: Copy tgz apps
  become: true
  become_user: "{{ splunk.nix.user }}"
  copy:
    src: "{{ item.path }}"
    dest: "{{ apps_path }}"
    owner: "{{ splunk.nix.user }}"
    group: "{{ splunk.nix.group }}"
    mode: 0700
    force: yes
  loop: "{{ tgzfile_results.files }}"

- name: Find .tgz
  find:
    paths: "{{ apps_path }}"
    patterns: "*.tgz"
  register: tgz_results

- name: Extract .tgz
  become: true
  become_user: "{{ splunk.nix.user }}"
  unarchive:
    src: "{{ item.path }}"
    dest: "{{ apps_path }}"
    owner: "{{ splunk.nix.user }}"
    group: "{{ splunk.nix.group }}"
    remote_src: true
  loop: "{{ tgz_results.files }}"
  register: deploy_deployer_apps_extracted

- name: Delete .tgz
  become: true
  become_user: "{{ splunk.nix.user }}"
  file:
    path: "{{ item.path }}"
    state: absent
  loop: "{{ tgz_results.files }}"

- name: Apply shcluster bundle
  command: "{{ splunk.home }}/bin/splunk apply shcluster-bundle -target https://{{ groups['search_head'] | first }}:{{ splunk.ports.mgmt }} -auth {{ splunk.admin.username }}:{{ splunk.admin.password }} --answer-yes"
  become: true
  become_user: "{{ splunk.nix.user }}"
  when:
    - deploy_apps is changed or deploy_deployer_apps_extracted is changed
    - "'shcluster' in apps_path"

- include_tasks: "{{ playbook_dir }}/roles/common/tasks/restart_splunk.yml"
  when:
    - deploy_apps is changed or deploy_deployer_apps_extracted is changed
    - "'shcluster' not in apps_path"

ENDMSG
```
---
### ansible/roles/common/tasks/deploy_use_case.yml
```bash
cat > "/opt/SmartSOC/web/ansible/roles/common/tasks/deploy_use_case.yml" <<"ENDMSG"
---

- include_tasks: "{{ playbook_dir }}/roles/common/tasks/extract_mongodb_primary_ip.yml"
  no_log: true

- name: Run the getCollection command
  community.mongodb.mongodb_shell:
    login_host: "{{ mongo_primary_ip }}"
    db: "mitre_db"
    eval: 'db.getCollection("splunk_rules").find({ "sigma_id": { $in: {{ entries_id_list }} } }).toArray()'
  register: mongo_results

- include_tasks: "{{ playbook_dir }}/roles/common/tasks/process_use_case_deployment.yml"
  loop: "{{ mongo_results.transformed_output | list }}"
  when: mongo_results
  no_log: true

- name: Run the update command for mongodb
  community.mongodb.mongodb_shell:
    login_host: "{{ mongo_primary_ip }}"
    db: "mitre_db"
    eval: "db.splunk_rules.updateOne({ _id: ObjectId('{{ inner_item._id['$oid'] }}') }, { $set: { 'deployed': true } })"
  loop: "{{ mongo_results.transformed_output | list }}"
  loop_control:
    loop_var: inner_item
  register: update_mongodb_response

ENDMSG
```
---
### ansible/roles/common/tasks/extract_mongodb_primary_ip.yml
```bash
cat > "/opt/SmartSOC/web/ansible/roles/common/tasks/extract_mongodb_primary_ip.yml" <<"ENDMSG"
---

- name: Get replica set status
  community.mongodb.mongodb_shell:
    login_host: "{{ base.mongo_primary_ip }}"
    db: "admin"
    eval: "JSON.stringify(rs.isMaster())"
  register: mongo_rs_status

- name: Extract primary node hostname
  set_fact:
    mongo_primary: "{{ (mongo_rs_status.transformed_output[0] | from_json | from_json).primary }}"

- name: Extract only IP from primary
  set_fact:
    mongo_primary_ip: "{{ mongo_primary.split(':')[0] }}"

ENDMSG
```
---
### ansible/roles/common/tasks/prepare_unparsed_log_config.yml
```bash
cat > "/opt/SmartSOC/web/ansible/roles/common/tasks/prepare_unparsed_log_config.yml" <<"ENDMSG"
---

- name: Set value from MongoDB query results
  set_fact:
    sh_props_report_transname: "{{ ((item.log_type if item.log_type is defined and item.log_type != '' else 'unknown' ) + '_' + item.id) | regex_replace('[^a-zA-Z0-9]+', '_') }}"
    hf_props_catchall_index_transname: "{{ ((item.log_type if item.log_type is defined and item.log_type != '' else 'unknown' ) + '_route_index_' + item.id) | regex_replace('[^a-zA-Z0-9]+', '_') }}"
    hf_props_catchall_sourcetype_transname: "{{ ((item.log_type if item.log_type is defined and item.log_type != '' else 'unknown' ) + '_route_sourcetype_' + item.id) | regex_replace('[^a-zA-Z0-9]+', '_') }}"

- name: Set SIEM Config
  set_fact:
    siem_config: "### SH props.conf\\n
[{{ item.source_type }}]\\n
REPORT-smartsoc = {{ sh_props_report_transname }}\\n
\\n
### SH transforms.conf\\n
[{{ sh_props_report_transname }}]\\n
REGEX = {{ item.regex }}\\n
\\n
### HF props.conf\\n
[catchall]\\n
TRANSFORMS-catchallindex = {{ hf_props_catchall_index_transname }}\\n
TRANSFORMS-catchallsourcetype = {{ hf_props_catchall_sourcetype_transname }}\\n
\\n
### HF transforms.conf\\n
[{{ hf_props_catchall_index_transname }}]\\n
REGEX = {{ item.regex }}\\n
DEST_KEY = _MetaData:Index\\n
FORMAT = {{ item.index }}\\n
\\n
[{{ hf_props_catchall_sourcetype_transname }}]\\n
REGEX = {{ item.regex }}\\n
DEST_KEY = MetaData:Sourcetype\\n
FORMAT = {{ 'sourcetype::' + item.source_type }}\\n"

- name: Trim empty space for SIEM Config
  set_fact:
    replace_siem_config: "{{ siem_config | regex_replace('\\\\n ', '\\\\n') }}"

- name: Update Record Status and SIEM Config in MongoDB
  community.mongodb.mongodb_shell:
    login_host: "{{ mongo_primary_ip }}"
    db: "parser_db"
    eval: "db.entries.updateOne({ _id: ObjectId('{{ item._id['$oid'] }}') }, { $set: { 'config': '{{ replace_siem_config }}', 'status': 'Generated' } })"

ENDMSG
```
---
### ansible/roles/common/tasks/process_unparsed_log.yml
```bash
cat > "/opt/SmartSOC/web/ansible/roles/common/tasks/process_unparsed_log.yml" <<"ENDMSG"
---

- name: Set default value for variables
  set_fact:
    transform_stanza_catchall_index_exists: false
    transform_stanza_catchall_sourcetype_exists: false
    transform_stanza_force_update: false
    transform_stanza_smartsoc_exists: false
    props_report_catchall_index_value: ''
    props_report_catchall_sourcetype_value: ''
    props_report_smartsoc_value: ''

- name: Set value from MongoDB query results
  set_fact:
    sh_props_report_transname: "{{ ((item.log_type if item.log_type is defined and item.log_type != '' else 'unknown' ) + '_' + item.id) | regex_replace('[^a-zA-Z0-9]+', '_') }}"
    hf_props_catchall_index_transname: "{{ ((item.log_type if item.log_type is defined and item.log_type != '' else 'unknown' ) + '_route_index_' + item.id) | regex_replace('[^a-zA-Z0-9]+', '_') }}"
    hf_props_catchall_sourcetype_transname: "{{ ((item.log_type if item.log_type is defined and item.log_type != '' else 'unknown' ) + '_route_sourcetype_' + item.id) | regex_replace('[^a-zA-Z0-9]+', '_') }}"

- name: Get stats of a file
  become: true
  become_user: "{{ splunk.nix.user }}"
  ansible.builtin.stat:
    path: "{{ splunk.home }}/etc/deployment-apps/ste_hf_smartsoc/local/props.conf"
  register: st_props_conf

- name: Slurp an INI file if exists
  become: true
  become_user: "{{ splunk.nix.user }}"
  ansible.builtin.slurp:
    src: "{{ splunk.home }}/etc/deployment-apps/ste_hf_smartsoc/local/props.conf"
  register: props_conf
  when: st_props_conf.stat.exists

- name: Display the INI file as dictionary if exists
  become: true
  become_user: "{{ splunk.nix.user }}"
  ansible.builtin.debug:
    var: props_conf.content | b64decode | community.general.from_ini | regex_replace("TRANSFORMS-", "TRANSFORMSXXX")
  when: st_props_conf.stat.exists

- name: Set a new dictionary fact with the contents of the INI file if exists
  become: true
  become_user: "{{ splunk.nix.user }}"
  ansible.builtin.set_fact:
    props_dict: >-
      {{
          props_conf.content | b64decode | community.general.from_ini | regex_replace("TRANSFORMS-", "TRANSFORMSXXX")
      }}
  when: st_props_conf.stat.exists

- name: Set a new variable with the TRANSFORMS-catchall value from the INI file if exists
  set_fact:
    props_report_catchall_index_value: "{{ props_dict.catchall | json_query('TRANSFORMSXXXcatchallindex') }}"
    props_report_catchall_sourcetype_value: "{{ props_dict.catchall | json_query('TRANSFORMSXXXcatchallsourcetype') }}"
  when: st_props_conf.stat.exists

- name: set_fact when transform stanza catchallindex in props
  set_fact:
    transform_stanza_catchall_index_exists: true
    transform_stanza_force_update: true
  loop: "{{ props_report_catchall_index_value | replace(' ', '') | split(',') | list }}"
  when:
    - st_props_conf.stat.exists
    - inner_item == hf_props_catchall_index_transname
  loop_control:
    loop_var: inner_item

- name: Append the original TRANSFORMS-catchallindex value if exists
  set_fact:
    props_report_catchall_index_value: "{{ props_report_catchall_index_value + ', ' + hf_props_catchall_index_transname}}"
  when:
    - not transform_stanza_catchall_index_exists
    - props_report_catchall_index_value != ''

- name: Set new TRANSFORMS-catchallindex if not exists
  set_fact:
    props_report_catchall_index_value: "{{ hf_props_catchall_index_transname }}"
  when: props_report_catchall_index_value == ""

- name: Update deployment app in deployment server - props.conf if the stanza catchallindex not exists
  become: true
  become_user: "{{ splunk.nix.user }}"
  ini_file:
    path: "{{ splunk.home }}/etc/deployment-apps/ste_hf_smartsoc/local/props.conf"
    section: "catchall"
    option: "{{ inner_item.key }}"
    value: "{{ inner_item.value }}"
    owner: "{{ splunk.nix.user }}"
    group: "{{ splunk.nix.group }}"
  with_items:
    - {key: "TRANSFORMS-catchallindex", value: "{{ props_report_catchall_index_value }}"}
  register: deploymentapp_props
  when: not transform_stanza_catchall_index_exists
  loop_control:
    loop_var: inner_item

# May have few options, 1 with REGEX only, 1 with REGEX, FORMAT, REPEAT_MATCH
- name: Update deployment app in deployment server - transforms.conf for catchallindex stanza
  become: true
  become_user: "{{ splunk.nix.user }}"
  ini_file:
    path: "{{ splunk.home }}/etc/deployment-apps/ste_hf_smartsoc/local/transforms.conf"
    section: "{{ hf_props_catchall_index_transname }}"
    option: "{{ inner_item.key }}"
    value: "{{ inner_item.value }}"
    owner: "{{ splunk.nix.user }}"
    group: "{{ splunk.nix.group }}"
  with_items:
    - {key: "REGEX", value: "{{ item.regex }}"}
    - {key: "DEST_KEY", value: "_MetaData:Index"}
    - {key: "FORMAT", value: "{{ item.index }}"}
  register: deploymentapp_transforms
  when: transform_stanza_force_update or not transform_stanza_catchall_index_exists
  loop_control:
    loop_var: inner_item

- name: Insert empty line before the new stanza for catchall_index
  become: true
  become_user: "{{ splunk.nix.user }}"
  lineinfile:
    path: "{{ splunk.home }}/etc/deployment-apps/ste_hf_smartsoc/local/transforms.conf"
    insertbefore: "{{ hf_props_catchall_index_transname }}"
    line: "\n"
  when: not transform_stanza_catchall_index_exists

- name: set_fact when transform stanza catchallsourcetype in props
  set_fact:
    transform_stanza_catchall_sourcetype_exists: true
    transform_stanza_force_update: true
  loop: "{{ props_report_catchall_sourcetype_value | replace(' ', '') | split(',') | list }}"
  when:
    - st_props_conf.stat.exists
    - inner_item == hf_props_catchall_sourcetype_transname
  loop_control:
    loop_var: inner_item

- name: Append the original TRANSFORMS-catchallsourcetype value if exists
  set_fact:
    props_report_catchall_sourcetype_value: "{{ props_report_catchall_sourcetype_value + ', ' + hf_props_catchall_sourcetype_transname}}"
  when:
    - not transform_stanza_catchall_sourcetype_exists
    - props_report_catchall_sourcetype_value != ''

- name: Set new TRANSFORMS-catchallsourcetype if not exists
  set_fact:
    props_report_catchall_sourcetype_value: "{{ hf_props_catchall_sourcetype_transname }}"
  when: props_report_catchall_sourcetype_value == ""

- name: Update deployment app in deployment server - props.conf if the stanza catchallsourcetype not exists
  become: true
  become_user: "{{ splunk.nix.user }}"
  ini_file:
    path: "{{ splunk.home }}/etc/deployment-apps/ste_hf_smartsoc/local/props.conf"
    section: "catchall"
    option: "{{ inner_item.key }}"
    value: "{{ inner_item.value }}"
    owner: "{{ splunk.nix.user }}"
    group: "{{ splunk.nix.group }}"
  with_items:
    - {key: "TRANSFORMS-catchallsourcetype", value: "{{ props_report_catchall_sourcetype_value }}"}
  register: deploymentapp_props
  when: not transform_stanza_catchall_sourcetype_exists
  loop_control:
    loop_var: inner_item

# May have few options, 1 with REGEX only, 1 with REGEX, FORMAT, REPEAT_MATCH
- name: Update deployment app in deployment server - transforms.conf for catchallsourcetype stanza
  become: true
  become_user: "{{ splunk.nix.user }}"
  ini_file:
    path: "{{ splunk.home }}/etc/deployment-apps/ste_hf_smartsoc/local/transforms.conf"
    section: "{{ hf_props_catchall_sourcetype_transname }}"
    option: "{{ inner_item.key }}"
    value: "{{ inner_item.value }}"
    owner: "{{ splunk.nix.user }}"
    group: "{{ splunk.nix.group }}"
  with_items:
    - {key: "REGEX", value: "{{ item.regex }}"}
    - {key: "DEST_KEY", value: "MetaData:Sourcetype"}
    - {key: "FORMAT", value: "{{ 'sourcetype::' + item.source_type }}"}
  register: deploymentapp_transforms
  when: transform_stanza_force_update or not transform_stanza_catchall_sourcetype_exists
  loop_control:
    loop_var: inner_item

- name: Insert empty line before the new stanza for catchall_sourcetype
  become: true
  become_user: "{{ splunk.nix.user }}"
  lineinfile:
    path: "{{ splunk.home }}/etc/deployment-apps/ste_hf_smartsoc/local/transforms.conf"
    insertbefore: "{{ hf_props_catchall_sourcetype_transname }}"
    line: "\n"
  when: not transform_stanza_catchall_sourcetype_exists

- name: SH - Get stats of a file
  delegate_to: "{{ groups['search_head'] | first }}"
  become: true
  become_user: "{{ splunk.nix.user }}"
  ansible.builtin.stat:
    path: "{{ splunk.home }}/etc/apps/ste_sh_smartsoc/local/props.conf"
  register: st_sh_props_conf

- name: SH - Slurp an INI file if exists
  delegate_to: "{{ groups['search_head'] | first }}"
  become: true
  become_user: "{{ splunk.nix.user }}"
  ansible.builtin.slurp:
    src: "{{ splunk.home }}/etc/apps/ste_sh_smartsoc/local/props.conf"
  register: sh_props_conf
  when: st_sh_props_conf.stat.exists

- name: SH - Display the INI file as dictionary if exists
  become: true
  become_user: "{{ splunk.nix.user }}"
  ansible.builtin.debug:
    var: sh_props_conf.content | b64decode | community.general.from_ini | regex_replace("REPORT-", "REPORTXXX")
  when: st_sh_props_conf.stat.exists

- name: SH - Set a new dictionary fact with the contents of the INI file if exists
  become: true
  become_user: "{{ splunk.nix.user }}"
  ansible.builtin.set_fact:
    sh_props_dict: >-
      {{
          sh_props_conf.content | b64decode | community.general.from_ini | regex_replace("REPORT-", "REPORTXXX")
      }}
  when: st_sh_props_conf.stat.exists

- name: SH - Set a new variable with the REPORT-smartsoc value from the INI file if exists
  set_fact:
    props_report_smartsoc_value: "{{ sh_props_dict[item.source_type] | json_query('REPORTXXXsmartsoc') }}"
  when:
    - item.source_type in sh_props_dict 
    - st_sh_props_conf.stat.exists

- name: SH - set_fact when transform stanza smartsoc in props
  delegate_to: "{{ groups['search_head'] | first }}"
  set_fact:
    transform_stanza_smartsoc_exists: true
  loop: "{{ props_report_smartsoc_value | replace(' ', '') | split(',') | list }}"
  when:
    - st_sh_props_conf.stat.exists
    - inner_item == sh_props_report_transname
  loop_control:
    loop_var: inner_item

- name: SH - Append the original REPORT-smartsoc value if exists
  set_fact:
    props_report_smartsoc_value: "{{ props_report_smartsoc_value + ', ' + sh_props_report_transname }}"
  when:
    - not transform_stanza_smartsoc_exists
    - props_report_smartsoc_value != ''

- name: SH - Set new REPORT-smartsoc if not exists
  set_fact:
    props_report_smartsoc_value: "{{ sh_props_report_transname }}"
  when: props_report_smartsoc_value == ""

- name: Update props.conf configuration in Splunk SH - creation of stanza
  become: true
  become_user: "{{ splunk.nix.user }}"
  uri:
    url: "https://{{ groups['search_head'] | first }}:8089/servicesNS/nobody/ste_sh_smartsoc/configs/conf-props"
    method: POST
    headers:
      Authorization: "Bearer {{ splunk.web.sh_token }}"
    body:
      name: "{{ item.source_type }}"
      "REPORT-smartsoc": "{{ props_report_smartsoc_value }}"
    body_format: form-urlencoded
    validate_certs: false
    return_content: true
  register: post_restapi_creation_response
  when: not transform_stanza_smartsoc_exists
  ignore_errors: true

- name: Update props.conf configuration in Splunk SH - update of stanza
  become: true
  become_user: "{{ splunk.nix.user }}"
  uri:
    url: "https://{{ groups['search_head'] | first }}:8089/servicesNS/nobody/ste_sh_smartsoc/configs/conf-props/{{ item.source_type }}"
    method: POST
    headers:
      Authorization: "Bearer {{ splunk.web.sh_token }}"
    body:
      "REPORT-smartsoc": "{{ props_report_smartsoc_value }}"
    body_format: form-urlencoded
    validate_certs: false
    return_content: true
  register: post_restapi_update_response
  when:
    - not transform_stanza_smartsoc_exists
    - "'already exists' in post_restapi_creation_response.content"

- name: Update transforms.conf configuration in Splunk SH - creation of stanza
  become: true
  become_user: "{{ splunk.nix.user }}"
  uri:
    url: "https://{{ groups['search_head'] | first }}:8089/servicesNS/nobody/ste_sh_smartsoc/configs/conf-transforms"
    method: POST
    headers:
      Authorization: "Bearer {{ splunk.web.sh_token }}"
    body:
      name: "{{ sh_props_report_transname }}"
      REGEX: "{{ item.regex }}"
    body_format: form-urlencoded
    validate_certs: false
    return_content: true
  register: post_restapi_transforms_creation_response
  ignore_errors: true

- name: Update transforms.conf configuration in Splunk SH - update of stanza
  become: true
  become_user: "{{ splunk.nix.user }}"
  uri:
    url: "https://{{ groups['search_head'] | first }}:8089/servicesNS/nobody/ste_sh_smartsoc/configs/conf-transforms/{{ sh_props_report_transname }}"
    method: POST
    headers:
      Authorization: "Bearer {{ splunk.web.sh_token }}"
    body:
      REGEX: "{{ item.regex }}"
    body_format: form-urlencoded
    validate_certs: false
    return_content: true
  register: post_restapi_transforms_update_response
  when: "'already exists' in post_restapi_transforms_creation_response.content"

- name: set_fact when require reload deploy server
  set_fact:
    reload_deploy_server: true
  when: deploymentapp_props is changed or deploymentapp_transforms is changed

ENDMSG
```
---
### ansible/roles/common/tasks/process_use_case_deployment.yml
```bash
cat > "/opt/SmartSOC/web/ansible/roles/common/tasks/process_use_case_deployment.yml" <<"ENDMSG"
---

- name: Run the getCollection command to get sigma rule
  community.mongodb.mongodb_shell:
    login_host: "{{ mongo_primary_ip }}"
    db: "mitre_db"
    eval: 'db.getCollection("sigma_rules").find({ "id": "{{ item.sigma_id }}" }).toArray()'
  register: inner_mongo_results

- name: set_fact use case severity based on sigma rule level
  set_fact:
    use_case_severity: "{{ os_map[inner_mongo_results.transformed_output[0].level] | default('3') }}"
  vars:
    os_map:
      informational: "1"
      low: "2"
      medium: "3"
      high: "4"
      critical: "5"

- name: Update savedsearches.conf configuration in Splunk SH - creation of stanza
  become: true
  become_user: "{{ splunk.nix.user }}"
  uri:
    url: "https://{{ groups['search_head'] | first }}:8089/servicesNS/nobody/ste_sh_smartsoc/saved/searches"
    method: POST
    headers:
      Authorization: "Bearer {{ splunk.web.sh_token }}"
    body:
      name: "{{ inner_mongo_results.transformed_output[0].title }}"
      description: "{{ inner_mongo_results.transformed_output[0].description }}"
      cron_schedule: "{{ item.cron_schedule }}"
      dispatch.earliest_time: "{{ item.dispatch_earliest_time }}"
      dispatch.latest_time: "{{ item.dispatch_latest_time }}"
      alert.severity: "{{ use_case_severity }}"
      alert_type: "number of events"
      alert.track: "1"
      is_scheduled: "1"
      alert_threshold: "0"
      alert_comparator: "greater than"
      search: "{{ item.rule }}"
    body_format: form-urlencoded
    validate_certs: false
    return_content: true
  register: post_restapi_savedsearches_creation_response
  ignore_errors: true

- name: Replace space with %20 for use case title
  set_fact:
    use_case_title: "{{ inner_mongo_results.transformed_output[0].title | regex_replace(' ', '%20') }}"
  when: "'already exists' in post_restapi_savedsearches_creation_response.content"

- name: Update savedsearches.conf configuration in Splunk SH - update of stanza
  become: true
  become_user: "{{ splunk.nix.user }}"
  uri:
    url: "https://{{ groups['search_head'] | first }}:8089/servicesNS/nobody/ste_sh_smartsoc/saved/searches/{{ use_case_title }}"
    method: POST
    headers:
      Authorization: "Bearer {{ splunk.web.sh_token }}"
    body:
      description: "{{ inner_mongo_results.transformed_output[0].description }}"
      cron_schedule: "{{ item.cron_schedule }}"
      dispatch.earliest_time: "{{ item.dispatch_earliest_time }}"
      dispatch.latest_time: "{{ item.dispatch_latest_time }}"
      alert.severity: "{{ use_case_severity }}"
      alert_type: "number of events"
      alert.track: "1"
      is_scheduled: "1"
      alert_threshold: "0"
      alert_comparator: "greater than"
      search: "{{ item.rule }}"
    body_format: form-urlencoded
    validate_certs: false
    return_content: true
  register: post_restapi_savedsearches_update_response
  when: "'already exists' in post_restapi_savedsearches_creation_response.content"

ENDMSG
```
---
### ansible/roles/common/tasks/reload_deployment_server.yml
```bash
cat > "/opt/SmartSOC/web/ansible/roles/common/tasks/reload_deployment_server.yml" <<"ENDMSG"
---

- name: reload_deployment_server
  become: true
  become_user: "{{ splunk.nix.user }}"
  command: "{{ splunk.home }}/bin/splunk reload deploy-server -auth {{ splunk.admin.username }}:{{ splunk.admin.password }} -timeout 10"
  
ENDMSG
```
---
### ansible/roles/common/tasks/update_deployment_apps.yml
```bash
cat > "/opt/SmartSOC/web/ansible/roles/common/tasks/update_deployment_apps.yml" <<"ENDMSG"
---
    
#Step 1: Get the list of apps in the ansible directory roles/common/files/apps_deployment_server (done)
#Step 2: Get the list of apps in the deployment server /opt/splunk/etc/deployment_apps (done)
#Step 3: Compare the list of apps, obtain the apps that are not inside deployment_apps (done) 
#Step 4: If apps are not inside deployment_apps, copy in to deployment_apps (done)
#Afterwards: edit serverclass.conf, push apps, restart deployment server

#Include checking for overwrite    
- name: Copy apps from ansible tower into deployment server
  become: true
  become_user: "{{ splunk.nix.user }}"
  copy:
    src: "{{playbook_dir}}/roles/common/files/apps_deployment_server/"
    dest: "{{ splunk.home }}/etc/deployment-apps/"
    owner: "{{ splunk.nix.user }}"
    group: "{{ splunk.nix.group }}"
    mode: 0700
    force: no
  register: deploy_apps
  when: "'deployment_server' in group_names"
    
#Reload Deployment Server
- include_tasks: "{{ playbook_dir }}/roles/common/tasks/reload_deployment_server.yml"
  when: deploy_apps is changed and "'deployment_server' in group_names"

#Necessary if want to configure serverclass in the future.  
# - name: Gather all deployment server apps
  # become: true
  # become_user: "{{ splunk.nix.user }}"
  # find:
    # path: "{{ splunk.home }}/etc/deployment-apps"
    # recurse: no
    # file_type: directory
  # register: deployment_apps
  # when: "'deployment_server' in group_names"



    
ENDMSG
```
---
### ansible/roles/common/tasks/update_mongodb_siem_config.yml
```bash
cat > "/opt/SmartSOC/web/ansible/roles/common/tasks/update_mongodb_siem_config.yml" <<"ENDMSG"
---

- include_tasks: "{{ playbook_dir }}/roles/common/tasks/extract_mongodb_primary_ip.yml"
  no_log: true

- name: Run the getCollection command for unparsed log
  community.mongodb.mongodb_shell:
    login_host: "{{ mongo_primary_ip }}"
    db: "parser_db"
    eval: 'db.getCollection("entries").find({ "id": { $in: {{ entries_id_list }} } }).toArray()'
  register: mongo_results

- include_tasks: "{{ playbook_dir }}/roles/common/tasks/prepare_unparsed_log_config.yml"
  loop: "{{ mongo_results.transformed_output | list }}"
  when: mongo_results
  no_log: true

ENDMSG
```
---
### ansible/roles/common/tasks/update_unparsed_log_transforms.yml
```bash
cat > "/opt/SmartSOC/web/ansible/roles/common/tasks/update_unparsed_log_transforms.yml" <<"ENDMSG"
---

- include_tasks: "{{ playbook_dir }}/roles/common/tasks/extract_mongodb_primary_ip.yml"
  no_log: true

- name: Set default value for variables
  set_fact:
    reload_deploy_server: false

- name: Check for existing serverclass.conf
  become: true
  become_user: "{{ splunk.nix.user }}"
  stat:
    path: "{{ splunk.home }}/etc/system/local/serverclass.conf"
  register: serverclass_conf

- name: Define smartsoc serverClass - whitelist
  become: true
  become_user: "{{ splunk.nix.user }}"
  ini_file:
    path: "{{ splunk.home }}/etc/system/local/serverclass.conf"
    section: "serverClass:hf_smartsoc"
    option: "whitelist.{{ item.0 }}"
    value: "{{ item.1 }}"
    owner: "{{ splunk.nix.user }}"
    group: "{{ splunk.nix.group }}"
  with_indexed_items:
    - "{{ groups['heavy_forwarder'] }}"

- name: Define smartsoc:app serverClass
  become: true
  become_user: "{{ splunk.nix.user }}"
  ini_file:
    path: "{{ splunk.home }}/etc/system/local/serverclass.conf"
    section: "serverClass:hf_smartsoc:app:ste_hf_smartsoc"
    option: restartSplunkd
    value: "true"
    owner: "{{ splunk.nix.user }}"
    group: "{{ splunk.nix.group }}"
  register: serverclass_configured

- include_tasks: "{{ playbook_dir }}/roles/common/tasks/reload_deployment_server.yml"
  when: serverclass_configured is changed

- name: Run the getCollection command
  community.mongodb.mongodb_shell:
    login_host: "{{ mongo_primary_ip }}"
    db: "parser_db"
    eval: 'db.getCollection("entries").find({ "id": { $in: {{ entries_id_list }} } }).toArray()'
  register: mongo_results

- include_tasks: "{{ playbook_dir }}/roles/common/tasks/process_unparsed_log.yml"
  loop: "{{ mongo_results.transformed_output | list }}"
  when: mongo_results
  no_log: true
  vars:
    reload_deploy_server: false

# Restart only when Splunk is running and when any of the above have changed
- include_tasks: "{{ playbook_dir }}/roles/common/tasks/reload_deployment_server.yml"
  when: reload_deploy_server

- name: Run the update command for mongodb
  community.mongodb.mongodb_shell:
    login_host: "{{ mongo_primary_ip }}"
    db: "parser_db"
    eval: "db.entries.updateOne({ _id: ObjectId('{{ inner_item._id['$oid'] }}') }, { $set: { 'status': 'Deployed' } })"
  loop: "{{ mongo_results.transformed_output | list }}"
  loop_control:
    loop_var: inner_item
  register: update_mongodb_response
ENDMSG
```
---
