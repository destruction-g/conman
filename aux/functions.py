import vars
import os, json
import socket

# рефакторинг
# инициализация конфигурации
PROJECT_DIRECTORY = os.path.abspath(os.path.join(__file__ ,"../.."))
SETTINGS = {}
try:
    settings_json_file = json.load(open(os.path.join(PROJECT_DIRECTORY, "settings.conf")))
    SETTINGS["CONFIGS_DIRECTORY"] = settings_json_file["CONFIGS_DIRECTORY"]
    SETTINGS["KEYS_DIRECTORY"] = settings_json_file["KEYS_DIRECTORY"]
    SETTINGS["CONFIGURATION_ITEMS_DIRECTORY"] = settings_json_file["CONFIGURATION_ITEMS_DIRECTORY"]
    SETTINGS["ANSIBLE_INVENTORY_FILE_NAME"] = settings_json_file["ANSIBLE_INVENTORY_FILE_NAME"]
except Exception as e:
    SETTINGS.update({"CONFIGS_DIRECTORY": os.path.expanduser("~/.config/conman/")})
    SETTINGS.update({"KEYS_DIRECTORY": os.path.join(SETTINGS["CONFIGS_DIRECTORY"], "files/keys/")})
    SETTINGS.update({"CONFIGURATION_ITEMS_DIRECTORY": os.path.join(SETTINGS["CONFIGS_DIRECTORY"], 'configuration_items/')})
    SETTINGS.update({"ANSIBLE_INVENTORY_FILE_NAME": os.path.join(PROJECT_DIRECTORY, 'inventory/static-inventory')})
    settings_json_file = open(os.path.join(PROJECT_DIRECTORY, "settings.conf"), "w")
    settings_json_file.write(json.dumps(SETTINGS, indent=0, sort_keys=True))
    settings_json_file.close()

# рефакторинг
class configuration:
    def __init__(self):
        self.configuration_parameter_types_array = ["defaults", "sources", "services", "acls"]
        self.configuration = {}
        # cоставляем все составляющие конфигурации в единый словарь:
        for parameter_type in self.configuration_parameter_types_array:
            try:
                json_file = json.load(open(os.path.join(SETTINGS["CONFIGS_DIRECTORY"], parameter_type)))
                self.configuration[parameter_type] = json_file
            except Exception as e:
                print("Ошибка при чтении", parameter_type, e)
                exit(1)
        # догружаем в словарь все конфигурационные единицы:
        self.configuration["configuration_items"] = {}
        for inventory_hostname in os.listdir(SETTINGS["CONFIGURATION_ITEMS_DIRECTORY"]):
            try:
                json_file = json.load(open(os.path.join(SETTINGS["CONFIGURATION_ITEMS_DIRECTORY"], inventory_hostname)))
                self.configuration["configuration_items"].update({inventory_hostname: json_file})
            except Exception as e:
                print("Ошибка при чтении конфигурационной единицы", inventory_hostname, e)
                exit(1)
        self.fill_missing_data_to_configuration_items()

    # рефакторинг
    # эта функция дополняет неполные данные в конфигурационной единице, например, ип адрес
    def fill_missing_data_to_configuration_items(self):
        for configuration_item_hostname in self.configuration["configuration_items"]:
            configuration_item_dict = self.configuration["configuration_items"][configuration_item_hostname]
            if "ITEM_IP_ADDRESS" not in configuration_item_dict:
                configuration_item_dict["ITEM_IP_ADDRESS"] = socket.gethostbyname(configuration_item_hostname)
            self.configuration["configuration_items"][configuration_item_hostname].update(configuration_item_dict)

    def get_target_hosts(self):
        out = ["127.0.0.1"];
        if "configuration_items" not in self.configuration:
            return out

        for item in self.configuration["configuration_items"].values():
            print(item)
            if "ITEM_IP_ADDRESS" in item:
                out.append(item["ITEM_IP_ADDRESS"]) 
        
        return out;

    def print(self):
        for element in self.configuration["configuration_items"]:
            print(element,  self.configuration["configuration_items"][element])

    # рефакторинг
    # эта функция выдает массив словаре конфигураций для чистки файла hosts
    def generate_configuration_items_dict(self):
        configuration_items_dict = {}
        try:
            configuration_items_dict["data"] = self.configuration["configuration_items"]
        except Exception as e:
            configuration_items_dict["success"] = False
            configuration_items_dict["reason"] = "Ошибка чтения словаря конфигурационных единиц, " + e
            return configuration_items_dict
        configuration_items_dict["success"] = True
        return configuration_items_dict

    # рефакторинг
    # возвращает путь к конфигурации для подстановки в плейбуки
    def get_configuration_items_directory(self):
        return SETTINGS["CONFIGURATION_ITEMS_DIRECTORY"]

    def get_keys_directory(self):
        return SETTINGS["KEYS_DIRECTORY"]



    # рефакторинг
    # эта функция выдает словарь {имяхоста:ипадрес, имяхоста:ипадрес} для подстановки в файл hosts
    def generate_hosts_file_dict(self):
        hosts_file_dict = {}
        hosts_file_dict["data"] = {}
        try:
            for configuration_item_hostname in self.configuration["configuration_items"]:
                configuration_item_dict = self.configuration["configuration_items"][configuration_item_hostname]
                if "ITEM_IP_ADDRESS" in configuration_item_dict:
                    hosts_file_dict["data"].update({configuration_item_hostname: configuration_item_dict["ITEM_IP_ADDRESS"]})
        except Exception as e:
            hosts_file_dict["success"] = False
            hosts_file_dict["reason"] = "Ошибка чтения словаря на элементе " + configuration_item_hostname + e
        hosts_file_dict["success"] = True
        return hosts_file_dict

    # рефакторинг
    # эта функция создает файл инвентори для ансибла
    def write_static_inventory_file_for_ansible(self):
        ansible_inventory_dict = {}
        for configuration_item_hostname in self.configuration["configuration_items"]:
            configuration_item_dict = self.configuration["configuration_items"][configuration_item_hostname]
            for configuration_item_group_name in configuration_item_dict['ITEM_GROUPS']:
                ansible_inventory_item = configuration_item_hostname
                if "ITEM_IP_ADDRESS" in configuration_item_dict:
                    ansible_inventory_item += " ansible_hostname=" + configuration_item_dict["ITEM_IP_ADDRESS"]
                if "ITEM_SSH_PORT" in configuration_item_dict:
                    ansible_inventory_item += " ansible_port=" + configuration_item_dict["ITEM_SSH_PORT"]
                if not configuration_item_group_name in ansible_inventory_dict:
                    ansible_inventory_dict[configuration_item_group_name] = []
                ansible_inventory_dict[configuration_item_group_name].append(ansible_inventory_item.rstrip())

        outfile = open(SETTINGS["ANSIBLE_INVENTORY_FILE_NAME"], 'w')
        for group in ansible_inventory_dict:
            outfile.write("[" + group + "]" + "\n")
            for ansible_inventory_item in ansible_inventory_dict[group]:
                outfile.write(ansible_inventory_item + "\n")
            outfile.write("\n")
        outfile.close()

    # рефакторинг
    # эта функция создает список отдельных source-элементов входящих в группу для подстановки в acl
    def generate_acl_source_group_items(self, group_name):
        acl_source_group_temp_dict = {}
        try:
            acl_source_group_temp_dict['data'] = []
            for configuration_item_hostname in self.configuration["configuration_items"]:
                configuration_item_dict = self.configuration["configuration_items"][configuration_item_hostname]
                if group_name in configuration_item_dict['ITEM_GROUPS']:
                    acl_source_group_temp_dict['data'].append({"source_address": configuration_item_dict['ITEM_IP_ADDRESS'], "source_type": "group", "source_comment": configuration_item_hostname})
            if not acl_source_group_temp_dict['data']:
                acl_source_group_temp_dict['success'] = False
                acl_source_group_temp_dict['reason'] = 'Не найдено ни одной подходящей конфигурационной единицы'
                return acl_source_group_temp_dict
        except Exception as e:
            acl_source_group_temp_dict['success'] = False
            acl_source_group_temp_dict['reason'] = 'Ошибка при парсинге элемента ' + configuration_item_hostname, e
            return acl_source_group_temp_dict
        acl_source_group_temp_dict['success'] = True
        return acl_source_group_temp_dict

    # рефакторинг
    # эта функция создает отдельный source-элемент для подстановки в acl
    def generate_acl_source_single_item(self, configuration_item_hostname):
        acl_source_single_temp_dict = {}
        try:
            if configuration_item_hostname in self.configuration["configuration_items"]:
                configuration_item_dict = self.configuration["configuration_items"][configuration_item_hostname]
                acl_source_single_temp_dict['data'] = {"source_address": configuration_item_dict['ITEM_IP_ADDRESS'], "source_type": "item", "source_comment": configuration_item_hostname}
            else:
                acl_source_single_temp_dict['success'] = False
                acl_source_single_temp_dict['reason'] = 'Не найдено ни одной подходящей конфигурационной единицы'
                return acl_source_single_temp_dict
        except Exception as e:
            acl_source_single_temp_dict['success'] = False
            acl_source_single_temp_dict['reason'] = 'Ошибка при парсинге элемента ' + configuration_item_hostname, e
            return acl_source_single_temp_dict
        acl_source_single_temp_dict['success'] = True
        return acl_source_single_temp_dict

    def compile_ansible_acl_element_dict(self, configuration_item_hostname, service_dict, source_dict, full_comment):
        ansible_acl_element_dict = {}
        ansible_acl_element_dict.update({"item_ip_address": self.configuration["configuration_items"][configuration_item_hostname]["ITEM_IP_ADDRESS"]})
        ansible_acl_element_dict.update({"full_comment": full_comment})
        ansible_acl_element_dict.update(service_dict)
        ansible_acl_element_dict.update(source_dict)
        return ansible_acl_element_dict


    # рефакторинг
    # эта функция создает отдельный словарь с переменными для подстановки в плейбук common_iptables
    def generate_ansible_iptables_acls_array(self, configuration_item_hostname):
        ansible_iptables_acls_array = []
        if configuration_item_hostname in self.configuration["configuration_items"]:
            configuration_item_dict = self.configuration["configuration_items"][configuration_item_hostname]
            acls_array = configuration_item_dict["ITEM_ACLS"]
            for acl_name in acls_array:
                acl_payload_dict = self.configuration["acls"][acl_name]
                for acl_service_name in acl_payload_dict:
                    service_payload_array = self.configuration['services'][acl_service_name]
                    for service_dict in service_payload_array:
                        source_payload_array = acl_payload_dict[acl_service_name]
                        for acl_source_name in source_payload_array:
                            acl_source_ips_array = self.configuration['sources'][acl_source_name]
                            for source_dict in acl_source_ips_array:
                                source_type = source_dict["source_type"]
                                full_comment = acl_service_name
                                if 'service_comment' in service_dict:
                                    full_comment += " " + service_dict['service_comment']
                                full_comment += ' for ' + acl_source_name

                                # тут мы разбираем каждый source элемент по типам:
                                if source_type == "address":
                                    if 'source_comment' in source_dict:
                                        full_comment += " from " + source_dict['source_comment']
                                    ansible_iptables_acls_array.append(self.compile_ansible_acl_element_dict(configuration_item_hostname, service_dict, source_dict, full_comment))

                                if source_type == "item":
                                    item_result = self.generate_acl_source_single_item(source_dict["source_item"])
                                    if item_result["success"]:
                                        source_dict = item_result['data']
                                        if 'source_comment' in source_dict:
                                            full_comment += " from " + source_dict['source_comment']
                                        ansible_iptables_acls_array.append(self.compile_ansible_acl_element_dict(configuration_item_hostname, service_dict, source_dict, full_comment))
                                    else:
                                        print("Ошибка заполнения элемента source:", item_result['reason'])
                                        exit(1)

                                if source_type == "group":
                                    group_result = self.generate_acl_source_group_items(source_dict["source_group"])
                                    if group_result["success"]:
                                        for source_dict in group_result["data"]:
                                            if 'source_comment' in source_dict:
                                                full_comment_append = full_comment + " from " + source_dict['source_comment']
                                            ansible_iptables_acls_array.append(self.compile_ansible_acl_element_dict(configuration_item_hostname, service_dict, source_dict, full_comment_append))
                                    else:
                                        return {"success": False, 'reason': group_result['reason']}
                                        exit(1)

        if not ansible_iptables_acls_array:
            return {"success": False, 'reason': "Массив пуст"}

        return {"success": True, 'data': ansible_iptables_acls_array}
