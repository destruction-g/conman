#!/usr/bin/python3
from functions import configuration
import sys
import traceback

try:
    action = str(sys.argv[1])
    parameters = True
except Exception as e:
    parameters = False

if parameters:
    configuration = configuration()
    try:
        if action == "write_static_inventory_file_for_ansible":
            configuration.write_static_inventory_file_for_ansible()

        if action == "generate_ansible_iptables_acls_array":
            inventory_hostname = str(sys.argv[2])
            ansible_iptables_acls_array = configuration.generate_ansible_iptables_acls_array(inventory_hostname)
            print(ansible_iptables_acls_array)

        if action == "generate_configuration_items_dict":
            configuration_items_dict = configuration.generate_configuration_items_dict()
            print(configuration_items_dict)

        if action == "generate_hosts_file_dict":
            hosts_file_dict = configuration.generate_hosts_file_dict()
            print(hosts_file_dict)

        if action == "get_configuration_items_directory":
            result = configuration.get_configuration_items_directory()
            if result:
                configuration_items_directory = {"success": True, "data": result}
            else:
                configuration_items_directory = {"success": False, "reason": "empty answer"}
            print(configuration_items_directory)

        if action == "get_keys_directory":
            result = configuration.get_keys_directory()
            if result:
                keys_directory = {"success": True, "data": result}
            else:
                keys_directory = {"success": False, "reason": "empty answer"}
            print(keys_directory)
    except Exception as e:
        print("Exception - ", traceback.format_exc())
        exit(1)

