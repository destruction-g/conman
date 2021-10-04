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

status_busy "Обновление static inventory"
if (
    python3 ./aux/helper.py write_static_inventory_file_for_ansible >> folding.log 2>> folding.log
    ); then status_done
else
  status_failed
  exit
fi

status_busy "Update local /etc/hosts file"

if (ansible-playbook playbooks/rewrite_hosts_file.yml --extra-vars "host=localhost" >> folding.log 2>> folding.log); then status_done
else
  status_failed
  exit
fi


case "$1" in
    'updatehosts')
        status_busy "Updating /etc/hosts files"
        host=[ -z $ITEM ] && $ITEM || "localhost"
        if (
            ansible-playbook all -i inventory playbooks/rewrite_hosts_file.yml --extra-vars "host=$host" >> folding.log 2>> folding.log
            ); then status_done 
        else
            status_failed
            exit
        fi
        ;;
esac

if [[ $1 == 'guestkeys' ]]
  then
    status_busy "Установка гостевых ключей"
    if (
        if [[ $3 ]]
          then
            FOR_USER=$3
          else
            FOR_USER=root
          fi
        ansible-playbook -i inventory playbooks/deploy_guest_key.yml --extra-vars "host=$ITEM ansible_user=root user=$FOR_USER" #-vvvvv
        ); then status_done
    else
      status_failed
      exit
    fi
fi

if [[ $1 == 'deploykey' ]]
  then
    read -p "    Введите пароль для пользователя root:" -s ANSIBLE_PASSWORD
    status_done
    status_busy "Установка ключа для пользователя root"
    if (
        ansible-playbook -i inventory playbooks/deploy_key.yml --extra-vars "host=$ITEM ansible_user=root user=root ansible_password=$ANSIBLE_PASSWORD" >> folding.log 2>> folding.log
        ); then status_done
    else
      status_failed
      exit
    fi
fi

if [[ $1 == 'deploykeysudo' ]]
  then
    read -p "    Введите имя пользователя (не root):" ANSIBLE_USER
    read -p "    Введите пароль пользователя:" -s ANSIBLE_PASSWORD
    status_done
    read -p "    Введите пароль root:" -s ANSIBLE_BECOME_PASS
    status_done
    status_busy "Установка ключа для пользователя root с помощью sudo"
    # BECOME="become=yes become_method=su become_user=root"
    VARS="host=$ITEM ansible_user=$ANSIBLE_USER user=root ansible_password=$ANSIBLE_PASSWORD ansible_become_pass=$ANSIBLE_BECOME_PASS"
    if (
        ansible-playbook -i inventory playbooks/deploy_key_sudo.yml --extra-vars "$VARS" >> folding.log 2>> folding.log
        ); then status_done
    else
      status_failed
      exit
    fi
fi

if [[ $1 == 'vpnprepare' ]]
  then
    ansible-playbook -i inventory playbooks/vpn.yml --extra-vars "host=$ITEM" #-vvvvv
    exit
fi

if [[ $1 == 'primary' ]]
then
  status_busy "Обазательная базовая настройка сервера"
  if (
      ansible-playbook -i inventory playbooks/primary.yml --extra-vars "host=$ITEM" >> folding.log 2>> folding.log
      ); then status_done
  else
    status_failed
    exit
  fi
fi

if [[ $1 == 'iptables' ]]
then
  status_busy "Применить iptables"
  if (
     ansible-playbook -i inventory playbooks/iptables.yml --extra-vars "host=$ITEM" >> folding.log 2>> folding.log
      ); then status_done
  else
    status_failed
    exit
  fi
fi

if [[ $1 == 'test' ]]
  then
    ansible-playbook -i inventory playbooks/test.yml --extra-vars "host=$ITEM" #-vvvvv
    exit
fi 
