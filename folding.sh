#!/bin/bash

RED='\033[0;31m'       #  ${RED}
GREEN='\033[0;32m'     #  ${GREEN}
CYAN='\033[0;36m'      #  ${CYAN}
YELLOW='\033[0;33m'    #  ${YELLOW}
NOCOL=$(tput sgr0)
STATUS_POSITION="\033[60G"

status_busy() {
  echo -ne "    $@ $STATUS_POSITION${CYAN} busy $NOCOL"
  SUCCESS=0
}
status_done() {
  echo -e "$STATUS_POSITION${GREEN} done $NOCOL"
}
status_failed() {
  echo -e "$STATUS_POSITION${RED}failed$NOCOL"
  exit 1
}
status_unknown() {
  echo -e "$STATUS_POSITION${YELLOW}unknown$NOCOL"
}

if [[ $1 == "" ]]
    then
      >&2 echo "updatehosts   - update /etc/hosts file on remote hosts"
      >&2 echo "deploykey 	  - установить ssh ключ для пользователя root"
      >&2 echo "deploykeysudo - установить ssh ключ для пользователя root с помощью sudo"
      >&2 echo "primary		  - Обязательная настройка сервера"
      >&2 echo "iptables	  - Применить правила iptables"
      >&2 echo "vpnprepare	  - Настроить VPN с нуля"
      >&2 echo "guestkeys	  - установить гостевые ключи"
      >&2 echo "test    	  - Плейбук для отладки"
      exit
fi

ITEM=$2

status_busy "Building static inventory"
python3 ./aux/helper.py write_static_inventory_file_for_ansible >> folding.log 2>> folding.log
[ $? -eq 0 ] && status_done || { status_failed; exit 1; }

status_busy "Update local /etc/hosts file"
ansible-playbook playbooks/rewrite_hosts_file.yml --extra-vars "host=localhost" >> folding.log 2>> folding.log
[ $? -eq 0 ] && status_done || { status_failed; exit 1; }

case "$1" in
    'updatehosts')
        [ -z $ITEM ] && HOST="localhost" || HOST=$ITEM
        status_busy "Updating /etc/hosts files"
        ansible-playbook -i inventory playbooks/rewrite_hosts_file.yml --extra-vars "host=$HOST" >> folding.log 2>> folding.log
        [ $? -eq 0 ] && status_done || { status_failed; exit 1; }
        ;;
    'guestkeys')
        status_busy "Installing guest keys"
        [ -z $3 ] && FOR_USER=root || FOR_USER=$3
        ansible-playbook -i inventory playbooks/deploy_guest_key.yml --extra-vars "host=$ITEM ansible_user=root user=$FOR_USER" #-vvvvv
        [ $? -eq 0 ] && status_done || { status_failed; exit 1; }
        ;;
    'deploykey')
        read -p "    Enter password for root user:" -s ANSIBLE_PASSWORD
        status_done 
        status_busy "Installing keys for root user"
        ansible-playbook -i inventory playbooks/deploy_key.yml --extra-vars "host=$ITEM ansible_user=root user=root ansible_password=$ANSIBLE_PASSWORD" >> folding.log 2>> folding.log
        [ $? -eq 0 ] && status_done || { status_failed; exit 1; }
        ;;
    'deploykeysudo')
        read -p "    Enter username (not root):" ANSIBLE_USER
        read -p "    Enter password:" -s ANSIBLE_PASSWORD
        status_done
        read -p "    Enter password for root user:" -s ANSIBLE_BECOME_PASS
        status_done
        status_busy "Installing key for root user with sudo"
        EXTRA_VARS="host=$ITEM ansible_user=$ANSIBLE_USER user=root ansible_password=$ANSIBLE_PASSWORD ansible_become_pass=$ANSIBLE_BECOME_PASS"
        ansible-playbook -i inventory playbooks/deploy_key_sudo.yml --extra-vars "$EXTRA_VARS" >> folding.log 2>> folding.log
        [ $? -eq 0 ] && status_done || { status_failed; exit 1; }
        ;;
    'vpnprepare')
        ansible-playbook -i inventory playbooks/vpn.yml --extra-vars "host=$ITEM" 
        ;;
    'primary')
        status_busy "Required basic setting of server"
        ansible-playbook -i inventory playbooks/primary.yml --extra-vars "host=$ITEM" >> folding.log 2>> folding.log
        [ $? -eq 0 ] && status_done || { status_failed; exit 1; }
        ;;
    'iptables')
        status_busy "Accepting iptables rules"
        ansible-playbook -i inventory playbooks/iptables.yml --extra-vars "host=$ITEM" >> folding.log 2>> folding.log
        [ $? -eq 0 ] && status_done || { status_failed; exit 1; }
        ;;
    'test')
        ansible-playbook -i inventory playbooks/test.yml --extra-vars "host=$ITEM" #-vvvvv
        ;;
esac
