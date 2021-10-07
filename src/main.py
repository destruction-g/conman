#!/usr/bin/python3

import os, json
import sys
import traceback

from core import Core

def main(argv=sys.argv):
    if len(sys.argv) <= 1:
        return 1

    PROJECT_DIRECTORY = os.path.abspath(os.path.join(__file__ , "../.."))
    configs_directory, configuration_items_directory, ansible_inventory_file_name, keys_directory = "", "", "", "" 
    try:
        settings_json_file = json.load(open(os.path.join(PROJECT_DIRECTORY, "settings.json")))
        configs_directory = os.path.expandvars(settings_json_file["CONFIGS_DIRECTORY"]) 
        keys_directory = os.path.expandvars(settings_json_file["KEYS_DIRECTORY"])
        configuration_items_directory = os.path.expandvars(settings_json_file["CONFIGURATION_ITEMS_DIRECTORY"])
        ansible_inventory_file_name = os.path.expandvars(settings_json_file["ANSIBLE_INVENTORY_FILE_NAME"])
    except Exception as e:
        configs_directory = os.path.expanduser("~/.config/conman/")
        keys_directory = os.path.join(configs_directory, "files/keys/")
        configuration_items_directory = os.path.join(configs_directory, 'configuration_items/')
        ansible_inventory_file_name = os.path.join(PROJECT_DIRECTORY, 'inventory/static-inventory')

        settings_json_file = open(os.path.join(PROJECT_DIRECTORY, "settings.json"), "w")
        settings_json_file.write(json.dumps({
                                            "CONFIGS_DIRECTORY": configs_directory,
                                            "CONFIGURATION_ITEMS_DIRECTORY": configuration_items_directory,
                                            "ANSIBLE_INVENTORY_FILE_NAME": ansible_inventory_file_name,
                                            "KEYS_DIRECTORY": keys_directory
        }, indent=0, sort_keys=True))
        settings_json_file.close()

    action = str(sys.argv[1])
    core = Core(configs_directory, configuration_items_directory, ansible_inventory_file_name, keys_directory)
    try:
        code = 0
        if action == "print":
            print(core.get_configuration())
        elif action == "write_static_inventory_file_for_ansible":
            result = core.write_static_inventory_file_for_ansible()
        elif action == "generate_ansible_iptables_acls_array":
            inventory_hostname = str(sys.argv[2])
            result = core.generate_ansible_iptables_acls_array(inventory_hostname)
            if not result.success: 
                code = 2
            print(result)
        elif action == "generate_configuration_items_dict":
            result = core.generate_configuration_items_dict()
            print(result)
        elif action == "generate_hosts_file_dict":
            result = core.generate_hosts_file_dict()
            print(result)
        elif action == "get_configuration_items_directory":
            result = core.get_configuration_items_directory()
            if result:
                configuration_items_directory = {"success": True, "data": result}
            else:
                configuration_items_directory = {"success": False, "reason": "empty answer"}
            print(configuration_items_directory)
        elif action == "get_keys_directory":
            result = core.get_keys_directory()
            if result:
                keys_directory = {"success": True, "data": result}
            else:
                keys_directory = {"success": False, "reason": "empty answer"}
            print(keys_directory)
        else: 
            code = 1
    except Exception as e:
        print("[main] - unexpected error:", traceback.format_exc(), sep="\n")
        code = 2
        
    return code

if __name__ == "__main__": 
    sys.exit(main())

