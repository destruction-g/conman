# conman
**conman** - это тулза с набором плейбуков ```ansible``` для удаленной настройки тачек. 


## Installation 
``` git clone https://github.com/destruction-g/conman```  
``` cd conman ```  
edit **settings.json** with your favorite editor  


## Usage
Запустить тулзу ```./folding.sh [command] [configuration_items]```  
Логи ```./folding.log```


## Settings
Глобальные настройки тулзы ```settings.json```.
``` 
{
    "ANSIBLE_INVENTORY_FILE_NAME": "${HOME}/src/github/destruction-g/conman/conman/inventory/static-inventory",
    "CONFIGS_DIRECTORY": "${HOME}/src/github/destruction-g/conman/.config/conman/",
    "CONFIGURATION_ITEMS_DIRECTORY": "${HOME}/src/github/destruction-g/conman/.config/conman/configuration_items/",
    "KEYS_DIRECTORY": "${HOME}/src/github/destruction-g/conman/.config/conman/files/keys/"
}
```


## Configuration
Конфигурация тулзы расположена домашней директории, указанной в **settings.json** ```CONFIGS_DIRECTORY```.
```
├── acls.json
├── configuration_items
│   ├── domain0.com.json
│   ├── domain1.com.json
│   └── domain2.com.json 
├── defaults
├── files
│   └── keys
│       ├── docker
│       │   └── current
│       ├── guest_keys
│       │   └── username
│       │       └── id_rsa.pub
│       └── root
│           ├── archive
│           ├── current
│           │   ├── id_rsa
│           │   └── id_rsa.pub
│           └── new
├── key_replace_stats.json
├── services.json
└── sources.json
```


#### defaults.json
Файл содержит значения полей по-умолчанию для **configuration_items**.
```
{
    "PROXMOX_USER" : "root@pam",   // не используется
    "PROXMOX_PASSWORD" : "123",	   // не используется
    "ITEM_SSH_PORT" : "22",        // порт для подключения к серверу по ssh
    "VPN_TYPE": "pptp",            // дефолтный тип подлючения для vpn
    "ITEM_HOST_TYPE": "null",	   // не используется
    "ITEM_SSH_KEY_EXCLUSIVE": "1", // по-умолчанию открытый ключ устанавливать эксклюзивно (все другие удаляются)
    "ITEM_GUEST_KEYS": []          // список гостевых ключей по-умолчанию пуст
}
```


#### configuration_items
Дириктория содержит файлы с описанием сервера, к которому применяются настройки(*имя файла - dns имя сервера*). Конфигурационные параметры объявленные в этих файлах переопределяют значения по-умолчанию.
``` 
{
    "ITEM_GROUPS": ["linux"],         // список групп, используется при генерации static inventory, необязательное поле (пока не используется)
    "ITEM_HOST_NAME": "ansible",      // название хоста, внутри сервера, обязательное поле
    "ITEM_ACLS": ["management"],      // список ALC для данного сервера, обязательное поле
    "ITEM_GUEST_KEYS": ["inkadavr"],  // список гостевых ключей, необязательное поле
    "ITEM_IP_ADDRESS": "192.168.29.3" // ip адрес сервера, используется в случае если dns имени сервера не существует, необязательное поле
}
```
*На основе данных файлов в последствии создается ```inventory``` файл для ```ansible```.*


### acls.json
Файл, в краткой форме описывает правила для файрвола
``` 
{
    "acl_name": {
        "service_name": ["source1", "source2"]
    }
}
```


#### services.json
Файл содержит описание сервисов.
``` 
{
  "service_name": [
    {
      "service_destination_port": 443,      // используется, если необходимо уточнить порт службы, необязательное поле
      "service_protocol": "tcp",            // название протокола, обазательное поле
      "service_comment": "https",           // если порт только один - можно не использоать, необязательное поле
      "service_destination_ip": "127.0.0.1" // используется если необходимо ип адрес на котором должна слушать служба, необязательно поле
    }
  ]
}
```

#### sources.json
Файл содержит описание источников.
``` 
{
  "source_name": [
    {
        "source_type": "address|group|item", // обязательное поле, возможные значения:
                                             // address - в этом режиме указывается напрямую ип адрес или подсеть
                                             // group - в этом режиме указывается группа из inventory
                                             // item - в этом режиме указывается inventory_hostname
	    
        // поля для режима address:
        "source_ip": "192.168.79.101",	 // ип адрес источника, обазательное поле (режим address)
        "source_comment": "proxmoxdub01" // если источник только один - можно не использоать, необязательное поле
        
        // поля для режима group:
        "source_group": "proxmoxdub", // указывается группа из inventory, все хосты из этой группы попадут в acl, обязательное поле
		
        // поля для режима item:
        "source_name": "zabbix", // указывается inventory_hostname
    }
  ]
}
```
*В комментарий для каждого из хостов в режимах ```item``` и ```group``` будут браться значения ```inventory_hostname```*


#### key_replace_stats.json
Файл хранит состояния этапов процедуры *замены ключей*  
``` 
{
  "key_generation_completed": 1, // первый этап завершен
  "key_install_completed": 1,    // второй этап завершен
  "key_replace_completed": 1     // третий этап завершен
}
```
Чтобы иницировать процедуру замены ключа, все значения необходимо установить в 0.

*Замена ключей* происходит в несколько этапов:
1. Генерация нового ключа в директорию ```new```.
1. Установка нового ключа на всех серверах.
   > Предусмотрена возможность запускать этот этап сколько угодно раз(работает идемпотентно), поскольку возможны ситуации, когда ключ не установится на все машины сразу.  
   В зависимости от значения ```ITEM_SSH_KEY_EXCLUSIVE``` устанавливается либо аддитивно, либо эксклюзивно (удаляет все другие ключи)
1. Удаление старого ключа.  
   > На этом этапе подлкючение к серверам происходит уже с использованием нового ключа, установленного
на предыдущем этапе. Можно запускать сколько угодно раз, работает идемпотентно.
1. Завершание.
   > Перемещает новый ключ в директорию ```current```, а старый перемещает в архив.


