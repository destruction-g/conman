import os, json
import sys
import socket
import traceback

class Core:
    def __init__(self, configs_directory, configuration_items_directory, ansible_inventory_file_name, keys_directory):
        self.__configs_directory = configs_directory
        self.__configuration_items_directory = configuration_items_directory
        self.__ansible_inventory_file_name = ansible_inventory_file_name
        self.__keys_directory = keys_directory
        configuration = {}
        
        # read main configurations"defaults", "sources", "services", "acls"
        configuraiton_array = ["defaults", "sources", "services", "acls"]
        for parameter_type in configuraiton_array:
            try:
                json_file = json.load(open(os.path.join(configs_directory, parameter_type + ".json")))
                configuration[parameter_type] = json_file
            except Exception as e:
                print('[Core.__init__] - failed to read %s: %s' % (inventory_hostname, e), traceback.format_exc(), sep="\n")
                sys.exit(1)

        # read main configuration_items:
        configuration["configuration_items"] = {}
        for inventory_hostname in os.listdir(configuration_items_directory):
            try:
                json_file = json.load(open(os.path.join(configuration_items_directory, inventory_hostname)))
                configuration["configuration_items"].update({os.path.splitext(inventory_hostname)[0]: json_file})
            except Exception as e:
                print('[Core.__init__] - failed to read configuration item %s: %s' % (inventory_hostname, e), traceback.format_exc(), sep="\n")
                sys.exit(1)

        # fill ips
        configuration_items = configuration["configuration_items"]
        for name, host in configuration_items.items():
            if "ip" not in host:
                host["ip"] = socket.gethostbyname(name)
            configuration_items[name].update(host)

        self.__configuration = configuration


    def get_configuration(self):
        return self.__configuration


    def get_configuration_items_directory(self):
        return self.__configuration_items_directory


    def get_keys_directory(self):
        return self.__keys_directory


    def generate_configuration_items_dict(self):
        configuration_items_dict = {}
        try:
            configuration_items_dict["data"] = self.__configuration["configuration_items"]
        except Exception as e:
            configuration_items_dict["success"] = False
            configuration_items_dict["reason"] = "Ошибка чтения словаря конфигурационных единиц, " + e
            return configuration_items_dict
        configuration_items_dict["success"] = True
        return configuration_items_dict
    

    def generate_hosts_file_dict(self):
        """Generate data for /etc/hosts file.
        
        Function gets domain name and ip configuration_items.
        Domain names are key of configuration_items dictionary and values by 'alias' property.
        This function returned next dictionary: 
        {'success':boolean, 'data':{":domain_name":"ip"}}
        """

        data = {}
        for name, host in self.__configuration["configuration_items"].items():
            if "ip" not in host:
                continue
            data[name] = host["ip"]
            if "alias" in host and isinstance(host["alias"], list):
                for alias in host["alias"]:
                    if alias in data: 
                        return {"success": False, "reason": 'Several ips (%s , %s) for one %s' % (data[alias], host["ip"], alias)}
                    data[alias] = host["ip"] 

        return {"success": True, "data": data}


    # рефакторинг
    # эта функция создает файл инвентори для ансибла
    def write_static_inventory_file_for_ansible(self):
        ansible_inventory_dict = {}
        for configuration_item_hostname in self.__configuration["configuration_items"]:
            configuration_item_dict = self.__configuration["configuration_items"][configuration_item_hostname]
            for configuration_item_group_name in configuration_item_dict['groups']:
                ansible_inventory_item = configuration_item_hostname
                if "ip" in configuration_item_dict:
                    ansible_inventory_item += " ansible_hostname=" + configuration_item_dict["ip"]
                if "ssh_port" in configuration_item_dict:
                    ansible_inventory_item += " ansible_port=" + configuration_item_dict["ssh_port"]
                if not configuration_item_group_name in ansible_inventory_dict:
                    ansible_inventory_dict[configuration_item_group_name] = []
                ansible_inventory_dict[configuration_item_group_name].append(ansible_inventory_item.rstrip())

        outfile = open(self.__ansible_inventory_file_name, 'w')
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
            for configuration_item_hostname in self.__configuration["configuration_items"]:
                configuration_item_dict = self.__configuration["configuration_items"][configuration_item_hostname]
                if group_name in configuration_item_dict['groups']:
                    acl_source_group_temp_dict['data'].append({"source_address": configuration_item_dict['ip'], "source_type": "group", "source_comment": configuration_item_hostname})
            if not acl_source_group_temp_dict['data']:
                acl_source_group_temp_dict['success'] = False
                acl_source_group_temp_dict['reason'] = 'failed to find configuration item for such group %s' % (group_name) 
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
            if configuration_item_hostname in self.__configuration["configuration_items"]:
                configuration_item_dict = self.__configuration["configuration_items"][configuration_item_hostname]
                acl_source_single_temp_dict['data'] = {"source_address": configuration_item_dict['ip'], "source_type": "item", "source_comment": configuration_item_hostname}
            else:
                acl_source_single_temp_dict['success'] = False
                acl_source_single_temp_dict['reason'] = 'failed to find configuration item for such item %s' % (configuration_item_hostname)
                return acl_source_single_temp_dict
        except Exception as e:
            acl_source_single_temp_dict['success'] = False
            acl_source_single_temp_dict['reason'] = 'Ошибка при парсинге элемента ' + configuration_item_hostname, e
            return acl_source_single_temp_dict
        acl_source_single_temp_dict['success'] = True
        return acl_source_single_temp_dict


    def compile_ansible_acl_element_dict(self, configuration_item_hostname, service_dict, source_dict, full_comment):
        ansible_acl_element_dict = {}
        ansible_acl_element_dict.update({"ip": self.__configuration["configuration_items"][configuration_item_hostname]["ip"]})
        ansible_acl_element_dict.update({"full_comment": full_comment})
        ansible_acl_element_dict.update({key if key.startswith("service_") else "service_" + key: value for key, value in service_dict.items()})
        ansible_acl_element_dict.update({key if key.startswith("source_") else "source_" + key: value for key, value in source_dict.items()})
        return ansible_acl_element_dict


    # рефакторинг
    # эта функция создает отдельный словарь с переменными для подстановки в плейбук common_iptables
    def generate_ansible_iptables_acls_array(self, configuration_item_hostname):
        ansible_iptables_acls_array = []
        if configuration_item_hostname in self.__configuration["configuration_items"]:
            configuration_item_dict = self.__configuration["configuration_items"][configuration_item_hostname]
            acls_array = configuration_item_dict["acls"]
            for acl_name in acls_array:
                acl_payload_dict = self.__configuration["acls"][acl_name]
                for acl_service_name in acl_payload_dict:
                    service_payload_array = self.__configuration['services'][acl_service_name]
                    for service_dict in service_payload_array:
                        source_payload_array = acl_payload_dict[acl_service_name]
                        for acl_source_name in source_payload_array:
                            acl_source_ips_array = self.__configuration['sources'][acl_source_name]
                            for source_dict in acl_source_ips_array:
                                source_type = source_dict["type"]
                                full_comment = acl_service_name
                                if 'comment' in service_dict:
                                    full_comment += " " + service_dict['comment']
                                full_comment += ' for ' + acl_source_name

                                # тут мы разбираем каждый source элемент по типам:
                                if source_type == "address":
                                    if 'comment' in source_dict:
                                        full_comment += " from " + source_dict['comment']
                                    ansible_iptables_acls_array.append(self.compile_ansible_acl_element_dict(configuration_item_hostname, service_dict, source_dict, full_comment))

                                if source_type == "item":
                                    item_result = self.generate_acl_source_single_item(source_dict["item"])
                                    if item_result["success"]:
                                        source_dict = item_result['data']
                                        if 'comment' in source_dict:
                                            full_comment += " from " + source_dict['comment']
                                        ansible_iptables_acls_array.append(self.compile_ansible_acl_element_dict(configuration_item_hostname, service_dict, source_dict, full_comment))
                                    else:
                                        return {"success": False, 'reason': group_result['reason']}
                                        
                                if source_type == "group":
                                    group_result = self.generate_acl_source_group_items(source_dict["group"])
                                    if group_result["success"]:
                                        for source_dict in group_result["data"]:
                                            full_comment_append = full_comment
                                            if 'comment' in source_dict:
                                                full_comment_append += " from " + source_dict['comment']
                                            ansible_iptables_acls_array.append(self.compile_ansible_acl_element_dict(configuration_item_hostname, service_dict, source_dict, full_comment_append))
                                    else:
                                        return {"success": False, 'reason': group_result['reason']}

        if not ansible_iptables_acls_array:
            return {"success": False, 'reason': "empty array"}

        return {"success": True, 'data': ansible_iptables_acls_array}
