import os, json
import sys
import socket
import traceback

class Core:
    def __init__(self, configuration):
        self.__configuration_items = configuration["configuration_items"]
        self.__acls = configuration["acls"]
        self.__services = configuration["services"]
        self.__sources = configuration["sources"]


    def generate_hosts_file_dict(self):
        """Generate data for /etc/hosts file.
        
        Function gets domain name and ip configuration_items.
        Domain names are key of configuration_items dictionary and values by 'alias' property.
        This function returned next dictionary: 
        {'success':boolean, 'data':{":domain_name":"ip"}}
        """

        data = {}
        for name, host in self.__configuration_items.items():
            if "ip" not in host:
                continue
            data[name] = host["ip"]
            if "alias" in host and isinstance(host["alias"], list):
                for alias in host["alias"]:
                    if alias in data: 
                        return {"success": False, "reason": 'Several ips (%s , %s) for one %s' % (data[alias], host["ip"], alias)}
                    data[alias] = host["ip"] 

        return {"success": True, "data": data}


    def generate_ansible_iptables_acls_array(self, hostname):
        """Generate ansible iptables rules for ansible playbooks.
        
        Function gets data from acls, configuration_items, sources, services.
        And it merges into a usable format for ansible playbook.
        This function returned next dictionary: 
        {'success':boolean, 'data':{'docker':[], 'input':[]}}
        """
        
        docker = {"accept":[], "drop": []}
        _input = {"accept":[], "drop": []}

        if hostname not in self.__configuration_items:
            return {"success": False, "reason": "not found configuration_item by this hostname %s" % hostname}

        docker_destination_ports = set()
        configuration_item = self.__configuration_items[hostname]
        for acl_name in configuration_item["acls"]:
            acl = self.__acls[acl_name]
            for acl_service_name in acl:
                for service in self.__services[acl_service_name]:
                    for acl_source_name in acl[acl_service_name]:
                        for source in self.__sources[acl_source_name]:
                            full_comment = acl_service_name + " " + service["comment"] if "comment" in service else  acl_service_name
                            full_comment += " for " + acl_source_name
                            
                            elements = [] 
                            if source["type"] == "address":
                                full_comment_append = full_comment + " from " + source["comment"] if "comment" in source else full_comment
                                elements.append(self.__compile_ansible_acl_element_dict(hostname, service, source, full_comment_append))
                            if source["type"] == "item":
                                item_result = self.__generate_acl_source_single_item(source["item"])
                                if not item_result["success"]:
                                    return {"success": False, "reason": group_result["reason"]}

                                source = item_result["data"]
                                full_comment_append = full_comment + " from " + source["comment"] if "comment" in source else full_comment
                    
                                elements.append(self.__compile_ansible_acl_element_dict(hostname, service, source, full_comment_append))
                            if source["type"] == "group":
                                group_result = self.__generate_acl_source_group_items(source["group"])
                                if not group_result["success"]:
                                    return {"success": False, "reason": group_reslt["reason"]}
                                for source in group_result["data"]:
                                    full_comment_append = full_comment + " from " + source["comment"] if "comment" in source else full_comment
                                    elements.append(self.__compile_ansible_acl_element_dict(hostname, service, source, full_comment_append))

                            for el in elements: 
                                if "service_in_docker" in el and el["service_in_docker"] is True: 
                                    if "service_destination_port" in el and el["service_destination_port"] not in docker_destination_ports:    
                                        docker_destination_ports.add(el["service_destination_port"])
                                        docker["drop"].append(el)  
                                    docker["accept"].append(el)  
                                else: 
                                    _input["accept"].append(el)

        if not docker["accept"] and not docker["drop"] and not _input["accept"] and not _input["drop"]:
            return {"success": False, "reason": "empty iptables rules"}

        return {"success": True, "data": {"docker": docker, "input": _input}}


    def __generate_acl_source_group_items(self, group_name):
        data = []
        for hostname, item in self.__configuration_items.items():
            if group_name not in item['groups']:
                continue
            if "ip" not in item:
                return {"success": False, "reason": '%s does not include ip field' % (hostname)}
            data.append({"source_address": item['ip'], "source_type": "group", "source_comment": hostname})

        if not data:
            return {"success": False, "reason": 'failed to find configuration item for such group %s' % (group_name)}

        return {"success": True, "data": data}


    def __generate_acl_source_single_item(self, hostname):
        if hostname not in self.__configuration_items:
            return {"success": False, "reason": 'failed to find configuration item for such hostname %s' % (hostname)}

        configuration_item = self.__configuration_items[hostname]
        if "ip" not in configuration_item:  
            return {"success": False, "reason": '%s does not include ip field' % (hostname)}

        return {"success": True, "data": { "source_address": configuration_item['ip'], "source_type": "item", "source_comment": hostname}}
        
    def __compile_ansible_acl_element_dict(self, hostname, service, source, full_comment):
        host = self.__configuration_items[hostname]
        out = {}
        out.update({"ip": host["ip"], "network_interface": host["network_interface"] if "network_interface" in host else "eth0"})
        out.update({"full_comment": full_comment})
        out.update({key if key.startswith("service_") else "service_" + key: value for key, value in service.items()})
        out.update({key if key.startswith("source_") else "source_" + key: value for key, value in source.items()})
        return out
