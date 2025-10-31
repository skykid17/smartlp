#!/bin/bash
PYTHONVERSION=3.13.2
MONGOVERSION=8.0.6
MONGOTOOLSVERSION=100.11.0
MONGOIP=192.168.50.1
MONGOSHELLVERSION=2.5.2

dnf groupinstall -y "Development Tools"

# Create user & /opt
mkdir -p /opt/SmartSOC
useradd -M smartsoc
usermod -s /sbin/nologin smartsoc
usermod -d /opt/SmartSOC smartsoc
mkdir -p /opt/SmartSOC/{bin,conf,tmp,pid,web}
mkdir -p /opt/SmartSOC/var/{log,run}
mkdir -p /opt/SmartSOC/var/lib/db

# Pull Code
cd /opt/SmartSOC/web
git init
cat > /opt/SmartSOC/web/.git/config <<"endmsg"
[core]
        repositoryformatversion = 0
        filemode = true
        bare = false
        logallrefupdates = true
[remote "origin"]
        url = https://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@github.com/kyusan93/smartsoc.git
        fetch = +refs/heads/*:refs/remotes/origin/*
[pull]
        rebase = true
[branch "main"]
        remote = origin
        merge = refs/heads/main
endmsg
git pull origin HEAD:main
chown -R smartsoc. /opt/SmartSOC/

# Sample .ENV file (change as necessary)
cat > /opt/SmartSOC/web/.env << "endmsg"
# Elastic Configuration
ELASTIC_HOST='https://localhost:9200'
ELASTIC_USER='user'
ELASTIC_PASSWORD='password'
ELASTIC_API_TOKEN='token'
ELASTIC_CERT_PATH='/path_to_cert'

# Splunk Configuration
SPLUNK_USER='admin'
SPLUNK_PASSWORD='password'
SPLUNK_HOST='localhost'
SPLUNK_PORT=8089

# Ansible Configuration 
ANSIBLE_USER='admin'
ANSIBLE_SSH_PASSWORD='password'
ANSIBLE_BECOME_PASSWORD='password'

# MongoDB Configuration
MONGO_URL='mongodb://localhost:27017/'

# Database Names
MONGO_DB_PARSER=parser_db
MONGO_DB_SETTINGS=settings
MONGO_DB_MITRE=mitre_db
MONGO_DB_MITRE_TECH=mitre_techniques

# Parser Collections
MONGO_COLLECTION_ENTRIES=entries

# Settings Collections
MONGO_COLLECTION_GLOBAL_SETTINGS=global
MONGO_COLLECTION_LLMS_SETTINGS=llms
MONGO_COLLECTION_SIEMS_SETTINGS=siems

# MITRE Collections
MONGO_COLLECTION_SIGMA_RULES=sigma_rules
MONGO_COLLECTION_SPLUNK_RULES=splunk_rules
MONGO_COLLECTION_ELASTIC_RULES=elastic_rules
MONGO_COLLECTION_SECOPS_RULES=secops_rules

# MITRE Techniques Collection
MONGO_COLLECTION_MITRE_TECHNIQUES=techniques
endmsg

# MongoDB
wget -O /opt/SmartSOC/tmp/mongodb-linux-x86_64-rhel93-${MONGOVERSION}.tgz https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-rhel93-${MONGOVERSION}.tgz
tar -xzf /opt/SmartSOC/tmp/mongodb-linux-x86_64-rhel93-${MONGOVERSION}.tgz -C /opt/SmartSOC/
mv /opt/SmartSOC/mongodb-linux-x86_64-rhel93-${MONGOVERSION}/bin/* /opt/SmartSOC/bin
rm -rf /opt/SmartSOC/mongodb-linux-x86_64-rhel93-${MONGOVERSION}

# MongoDB Tools
wget -O /opt/SmartSOC/tmp/mongo_db_tools.tgz https://fastdl.mongodb.org/tools/db/mongodb-database-tools-rhel93-x86_64-${MONGOTOOLSVERSION}.tgz
tar -zxf /opt/SmartSOC/tmp/mongo_db_tools.tgz --strip-components=2 -C /opt/SmartSOC/bin mongodb-database-tools-rhel93-x86_64-${MONGOTOOLSVERSION}/bin/*

# MongoSH
wget -O /opt/SmartSOC/tmp/mongodb-mongosh.rpm https://downloads.mongodb.com/compass/mongodb-mongosh-${MONGOSHELLVERSION}.x86_64.rpm
rpm -ivh /opt/SmartSOC/tmp/mongodb-mongosh.rpm
mv /usr/bin/mongosh /opt/SmartSOC/bin
chown -R smartsoc. /opt/SmartSOC
/opt/SmartSOC/bin/mongosh --host ${MONGOIP} --port 27017

# MongoDB config file
cat > /opt/SmartSOC/conf/mongod.conf << "endmsg"
systemLog:
  destination: file
  logAppend: true
  path: /opt/SmartSOC/var/log/mongodb.log

storage:
  dbPath: /opt/SmartSOC/var/lib/db

processManagement:
  pidFilePath: /opt/SmartSOC/pid/mongod.pid

net:
  port: 27017
  bindIp: 0.0.0.0
  unixDomainSocket:
    pathPrefix: /opt/SmartSOC/tmp
endmsg

# SELinux Security Context
semanage fcontext -a -t mongod_log_t /opt/SmartSOC/var/log/
semanage fcontext -a -t mongod_var_lib_t /opt/SmartSOC/var/lib/db/
chcon -Rv -u system_u -t mongod_log_t /opt/SmartSOC/var/log/
chcon -Rv -u system_u -t mongod_var_lib_t /opt/SmartSOC/var/lib/db/

# Python & Install Dependencies
wget -O /opt/SmartSOC/tmp/Python-${PYTHONVERSION}.tgz https://www.python.org/ftp/python/${PYTHONVERSION}/Python-${PYTHONVERSION}.tgz
tar -xvf /opt/SmartSOC/tmp/Python-${PYTHONVERSION}.tgz -C /opt/SmartSOC/
cd /opt/SmartSOC/Python-${PYTHONVERSION}
make clean
./configure --prefix=/opt/SmartSOC/ --enable-shared --with-ensurepip=install
make -j$(nproc)
make install
echo "/opt/SmartSOC/lib" | sudo tee /etc/ld.so.conf.d/smartsoc.conf
ldconfig
sudo /opt/SmartSOC/bin/python3 -m pip install -r /opt/SmartSOC/web/requirements.txt
chown -R smartsoc. /opt/SmartSOC

# Gunicorn
cat > /opt/SmartSOC/conf/gunicorn.conf.py << "endmsg"
import multiprocessing
bind = "0.0.0.0:8800"
#workers = multiprocessing.cpu_count() * 2 + 1
workers = 2
chdir = "/opt/SmartSOC/web"
pidfile = "/opt/SmartSOC/var/run/gunicorn.pid"
accesslog = "/opt/SmartSOC/var/log/gunicorn.access.log"
errorlog = "/opt/SmartSOC/var/log/gunicorn.error.log"
loglevel = "info"
endmsg

# SmartSOC Daemon Script
cat > /opt/SmartSOC/bin/smartsocd << "endmsg"
#!/bin/bash

SMARTSOC_HOME="/opt/SmartSOC"
MONGO_CONF="$SMARTSOC_HOME/conf/mongod.conf"
GUNICORN_CONF="$SMARTSOC_HOME/conf/gunicorn.conf.py"

start() {
    echo "Starting SmartSOC services..."

    # Start MongoDB (No sudo needed)
    echo "Starting MongoDB..."
    $SMARTSOC_HOME/bin/mongod --config $MONGO_CONF --fork
    if [[ $? -ne 0 ]]; then
        echo "Failed to start MongoDB." >&2
        exit 1
    fi

    # Start Gunicorn (No sudo needed)
    echo "Starting Gunicorn..."
    $SMARTSOC_HOME/bin/gunicorn -c $GUNICORN_CONF app:app
    if [[ $? -ne 0 ]]; then
        echo "Failed to start Gunicorn." >&2
        exit 1
    fi

    echo "SmartSOC started successfully."
}

stop() {
    echo "Stopping SmartSOC services..."
    pkill -f gunicorn
    sleep 2
    pkill -f mongod
    sleep 2
    echo "SmartSOC stopped."
}

restart() {
    stop
    sleep 2
    start
}

status() {
    echo "Checking service status..."
    pgrep -f gunicorn >/dev/null && echo "Gunicorn is running" || echo "Gunicorn is not running"
    pgrep -f mongod >/dev/null && echo "MongoDB is running" || echo "MongoDB is not running"
}

case "$1" in
    start) start ;;
    stop) stop ;;
    restart) restart ;;
    status) status ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac

exit 0
endmsg
chown -R smartsoc. /opt/SmartSOC
chmod +x /opt/SmartSOC/bin/smartsocd

# Create Systemd Service
cat > /etc/systemd/system/SmartSOC.service << "endmsg"
[Unit]
Description=SmartSOC Service
After=network.target

[Service]
User=smartsoc
Group=smartsoc
ExecStart=/opt/SmartSOC/bin/smartsocd start
ExecStop=/opt/SmartSOC/bin/smartsocd stop
Restart=always
Type=simple

[Install]
WantedBy=multi-user.target
endmsg
firewall-cmd --zone=public --permanent --add-port 8800/tcp
firewall-cmd --reload

# MongoDB collections setup
/opt/SmartSOC/bin/mongoimport -d=mitre_techniques -c=techniques --file=/opt/SmartSOC/web/mongo/mitre_techniques.techniques.json --jsonArray
cat > /opt/SmartSOC/conf/mongo_setup.js << "endmsg"
mitre = db.getSiblingDB('mitre_db');
mitre.createCollection('sigma_rules');
mitre.createCollection('elastic_rules');
mitre.createCollection('splunk_rules');
endmsg
/opt/SmartSOC/bin/mongoimport -d=settings -c=global --file=/opt/SmartSOC/web/mongo/settings.global.json --jsonArray
/opt/SmartSOC/bin/mongoimport -d=settings -c=llms --file=/opt/SmartSOC/web/mongo/settings.llms.json --jsonArray
/opt/SmartSOC/bin/mongoimport -d=settings -c=siems --file=/opt/SmartSOC/web/mongo/settings.siems.json --jsonArray

# RAG Setup - Run automated RAG setup
echo "Setting up RAG (Retrieval-Augmented Generation) system..."
cd /opt/SmartSOC/web
sudo -u smartsoc /opt/SmartSOC/bin/python3 rag/setup_rag.py --siem both
if [[ $? -ne 0 ]]; then
    echo "Warning: RAG setup encountered issues. You can run it manually later with:"
    echo "cd /opt/SmartSOC/web && sudo -u smartsoc /opt/SmartSOC/bin/python3 setup_rag.py"
fi

systemctl daemon-reload
systemctl enable SmartSOC
systemctl start SmartSOC
