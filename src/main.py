#!/usr/bin/python3

import os, json
import sys
import traceback

from core import Core
from loader import Loader

def main(argv=sys.argv):
    if len(sys.argv) <= 1:
        return 1

    action = str(sys.argv[1])
    loader = Loader();
    core = Core(loader.get_configuration())
    try:
        code = 0
        if action == "print":
            print(core.get_configuration())
        elif action == "write_static_inventory_file_for_ansible":
            result = core.write_static_inventory_file_for_ansible()
        elif action == "generate_ansible_iptables_acls_array":
            inventory_hostname = str(sys.argv[2])
            result = core.generate_ansible_iptables_acls_array(inventory_hostname)
            if not result["success"]: 
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

