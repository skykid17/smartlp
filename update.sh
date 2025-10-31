usage() {
  echo "-g is for github pull"
  echo "-p is for package update on requirements.txt"
}

if [[ "$#" -eq 0 ]]; then
  echo "Script requires at least one flag"
  usage
  exit 1
fi

cd /opt/SmartSOC/web || { echo "Please run as root." 1>&2 ; exit 1; }
while getopts "hgp" flag; do
  case $flag in
    h)
      usage
      exit 0 
    ;;
    g)
      echo "Pulling Update from Github"
      git pull origin HEAD:main
    ;;
    p)
      echo "Updating based on requirements.txt"
      /opt/SmartSOC/bin/python3.13 -m pip install -U -r ./requirements.txt 
    ;;
    *)
      echo "Only supports -g or -p"
      usage
      exit 1
    ;;
  esac
done
chown -R smartsoc. /opt/SmartSOC/
echo "Restarting SmartSOC Service."
systemctl restart SmartSOC
systemctl status SmartSOC
