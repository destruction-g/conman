import os, json
import sys
import socket
import traceback

class Core:
    def __init__(self, configuration):
        self.__configuration = configuration


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
