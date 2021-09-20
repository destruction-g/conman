#!/bin/bash
# use: replace_keys.sh username

RED='\033[0;31m'       #  ${RED}      # красный цвет знаков
GREEN='\033[0;32m'     #  ${GREEN}    # зелёный цвет знаков
CYAN='\033[0;36m'       #  ${CYAN}      # цвет морской волны знаков
YELLOW='\033[0;33m'     #  ${YELLOW}    # желтый цвет знаков
NOCOL=$(tput sgr0)
STATUS_POSITION="\033[60G"


USER=$1
CURRENT_FOLDER="./files/keys/$USER/current"
TEMPORARY_FOLDER="./files/keys/$USER/new"
ARCHIVE_FOLDER="./files/keys/$USER/archive/`date '+%Y-%m-%d_%H-%M-%S'`"
TOTALSTEPS=12
CURSTEP=0

inc_step() {
  CURSTEP=$(($CURSTEP + 1))
}

status_busy() {
  echo -ne "  $CURSTEP/$TOTALSTEPS  :  $@ $STATUS_POSITION${CYAN} busy $NOCOL"
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

replace_begin() {
    while true; do
      echo  -e "${YELLOW}Замена ключей: СГЕНЕРИРОВАТЬ НОВЫЙ КЛЮЧ?$NOCOL"
        read -p "Y/N: " yn
        case $yn in
            [Yy]* ) break;;
            [Nn]* ) exit;;
            * ) echo "Необходимо ввести Y или N.";;
        esac
    done

    echo  -e "${YELLOW}Замена ключей: НАЧАЛО$NOCOL"

    inc_step
    status_busy "Создать временную папку для ключей"
    if (
        [ ! -e $TEMPORARY_FOLDER ] || rm -rf $TEMPORARY_FOLDER && \
        mkdir -p $TEMPORARY_FOLDER >> runonnewhost.log 2>>runonnewhost.log
        ); then status_done
    else
        status_failed
    fi

    inc_step
    status_busy "Сгенерировать ключи для пользователя $USER"
    echo -n Пожалуйста, введите пароль для закрытого ключа:
    read -s key_password
    if test -e "$TEMPORARY_FOLDER/id_rsa" || ssh-keygen -C "Created via ansible at `date '+%Y-%m-%d %H:%M:%S'`" -b 2048 -t rsa -f "./files/keys/$USER/new/id_rsa" -q -N $key_password >> runonnewhost.log 2>>runonnewhost.log; then
        status_done;
    else
        status_failed;
    fi

    inc_step
    status_busy "Утвердить начало процесса замены"
    if (
        cat ./configs/key_replace_stats > /tmp/key_replace_stats_tmp && \
        cat /tmp/key_replace_stats_tmp | jq '.key_replace_completed = 0' > ./configs/key_replace_stats && \
        rm /tmp/key_replace_stats_tmp
        ); then
        status_done
    else
        status_failed
    fi
    KEY_GENERATION_COMPLETED=`jq '.key_install_completed' < ./configs/key_replace_stats`
}

set_generation_complete() {
  CURSTEP=3
  inc_step
  status_busy "set ГЕНЕРАЦИЯ ЗАВЕРШЕНА"
  if (
      cat ./configs/key_replace_stats > /tmp/key_replace_stats_tmp && \
      cat /tmp/key_replace_stats_tmp | jq '.key_generation_completed = 1' > ./configs/key_replace_stats && \
      rm /tmp/key_replace_stats_tmp
      ); then
      status_done
  else
      status_failed
  fi
}

set_installation_complete() {
  CURSTEP=5
  inc_step
  status_busy "set УСТАНОВКА ЗАВЕРШЕНА"
  if (
      cat ./configs/key_replace_stats > /tmp/key_replace_stats_tmp && \
      cat /tmp/key_replace_stats_tmp | jq '.key_install_completed = 1' > ./configs/key_replace_stats && \
      rm /tmp/key_replace_stats_tmp
      ); then
      status_done
  else
      status_failed
  fi
}

set_replace_complete() {
  CURSTEP=7
  inc_step
  status_busy "set ЗАМЕНА ЗАВЕРШЕНА"
  if (
      cat ./configs/key_replace_stats > /tmp/key_replace_stats_tmp && \
      cat /tmp/key_replace_stats_tmp | jq '.key_replace_completed = 1' > ./configs/key_replace_stats && \
      rm /tmp/key_replace_stats_tmp
      ); then
      status_done
  else
      status_failed
  fi
}

get_status() {
    KEY_GENERATION_COMPLETED=`jq '."key_generation_completed"' < ~/.config/conman/key_replace_stats`
    KEY_INSTALL_COMPLETED=`jq '.key_install_completed' < ~/.config/conman/key_replace_stats`
    KEY_REPLACE_COMPLETED=`jq '.key_replace_completed' < ~/.config/conman/key_replace_stats`
}

install_continue() {
CURSTEP=4
inc_step
    echo  -e "${YELLOW}Замена ключей: ЦИКЛ УСТАНОВКИ$NOCOL"
    status_busy "Добавление нового ключа для пользователя $USER"
    if (
        ansible-playbook -i inventory playbooks/replace_deploy_key.yml --extra-vars "user=$USER host=linux" >> runonnewhost.log 2>> runonnewhost.log
        ); then
        status_done
    else
        status_unknown
    fi
}

generate_complete_choise() {
    while true; do
      echo  -e "${YELLOW}Замена ключей: ЗАВЕРШИТЬ ЦИКЛ ГЕНЕРАЦИИ?$NOCOL"
        read -p "Y/N: " yn
        case $yn in
            [Yy]* ) break;;
            [Nn]* ) exit;;
            * ) echo "Необходимо ввести Y или N.";;
        esac
    done
}

install_complete_choise() {
    while true; do
      echo  -e "${YELLOW}Замена ключей: ЗАВЕРШИТЬ ЦИКЛ УСТАНОВКИ?$NOCOL"
        read -p "Y/N: " yn
        case $yn in
            [Yy]* ) break;;
            [Nn]* ) exit;;
            * ) echo "Необходимо ввести Y или N.";;
        esac
    done
}

remove_complete_choise() {
    while true; do
      echo  -e "${YELLOW}Замена ключей: ЗАВЕРШИТЬ ЦИКЛ УДАЛЕНИЯ?$NOCOL"
        read -p "Y/N: " yn
        case $yn in
            [Yy]* ) break;;
            [Nn]* ) exit;;
            * ) echo "Необходимо ввести Y или N.";;
        esac
    done
}

remove_continue() {
    CURSTEP=6
    inc_step
    status_busy "Удаление старого ключа для пользователя $USER"
    if (
        ansible-playbook -i inventory playbooks/replace_remove_key.yml --extra-vars "user=$USER host=linux" >> runonnewhost.log 2>> runonnewhost.log
        ); then
        status_done
    else
        status_unknown
    fi
}

replace_finish() {
    inc_step
    status_busy "Завершить цикл установки ключа"
    if (
        cat ./configs/key_replace_stats > /tmp/key_replace_stats_tmp && \
        cat /tmp/key_replace_stats_tmp | jq '.key_install_completed = 1' > ./configs/key_replace_stats && \
        rm /tmp/key_replace_stats_tmp
        ); then
        status_done
    else
        status_failed
    fi

    inc_step
    status_busy "Переместить старые ключи в архив"
    if (
        mkdir -p $ARCHIVE_FOLDER && mv -u $CURRENT_FOLDER/* $ARCHIVE_FOLDER
        ); then
        status_done
    else
        status_failed
    fi

    inc_step
    status_busy "Переместить новые ключи в рабочее место"
    if (
        mv $TEMPORARY_FOLDER/* $CURRENT_FOLDER
        ); then
        status_done
    else
        status_failed
    fi

    inc_step
    status_busy "Завершить процесс замены ключей"
    if (
        cat ./configs/key_replace_stats > /tmp/key_replace_stats_tmp && \
        cat /tmp/key_replace_stats_tmp | jq '.key_replace_completed = 1' > ./configs/key_replace_stats && \
        rm /tmp/key_replace_stats_tmp
        ); then
        status_done
    else
        status_failed
    fi
}

################################################################################

if [ "$USER" == "" ]; then
    echo -e "Ошибка: не указано имя пользователя."
    echo -e "Использовать так: replace_keys.sh ${YELLOW}username$NOCOL"
    echo
    exit 1
fi

get_status

if [ "$KEY_GENERATION_COMPLETED" == 0 ]; then
  replace_begin
  generate_complete_choise
  set_generation_complete
fi

get_status

if [ "$KEY_INSTALL_COMPLETED" == 0 ]; then
  install_continue
  install_complete_choise
  set_installation_complete
fi

get_status

if [ "$KEY_REPLACE_COMPLETED" == 0 ]; then
  remove_continue
  remove_complete_choise
  set_replace_complete
  replace_finish
fi

echo
echo "	All tasks completed successfully"
echo "Have a nice day!"
