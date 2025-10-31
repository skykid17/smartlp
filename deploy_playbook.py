import os
import subprocess
import json
import sys
import dotenv

os.environ["ANSIBLE_COLLECTIONS_PATH"] = "/opt/SmartSOC/lib/python3.13/site-packages/ansible_collections"
dotenv.load_dotenv()

def run_ansible_playbook(PLAYBOOK_PATH, ENTRIES):
    INVENTORY = "./ansible/inventories/emax_test.yml"

    USER = os.getenv('ANSIBLE_USER')
    SSH_PASS = os.getenv('ANSIBLE_SSH_PASSWORD')
    BECOME_PASS = os.getenv('ANSIBLE_BECOME_PASSWORD')

    # === CONSTRUCT COMMAND ===
    command = ["../bin/ansible-playbook", PLAYBOOK_PATH]
    extra_vars = {}

    if INVENTORY:
        command += ["-i", INVENTORY]

    # SSH connection
    if SSH_PASS:
        extra_vars["ansible_user"] = USER
        extra_vars["ansible_password"] = SSH_PASS
    else:
        command += ["--ask-pass"]

    # sudo/become
    if BECOME_PASS:
        extra_vars["ansible_become_pass"] = BECOME_PASS
    else:
        command += ["--ask-become-pass"]

    # other vars
    if extra_vars:
        extra_vars["entries_id_list"] = ENTRIES

    # Add extra-vars if any are defined
    if extra_vars:
        command += ["--ssh-extra-args", "-o StrictHostKeyChecking=no"]
        command += ["--extra-vars", json.dumps(extra_vars)]

    # === RUN COMMAND ===
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print("❌ Playbook failed.")
        sys.exit(e.returncode)

