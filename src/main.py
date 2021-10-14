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
    configuration = loader.get_configuration()
    core = Core(configuration)
    try:
        code = 0
        if action == "print":
            print(configuration)
        elif action == "write_static_inventory_file_for_ansible":
            result = loader.create_inventory_file_for_ansible(configuration)
        elif action == "generate_ansible_iptables_acls_array":
            inventory_hostname = str(sys.argv[2])
            result = core.generate_ansible_iptables_acls_array(inventory_hostname)
            if not result["success"]: 
                code = 2
            print(result)
        elif action == "generate_hosts_file_dict":
            result = core.generate_hosts_file_dict()
            print(result)
        else: 
            code = 1
    except Exception as e:
        print("[main] - unexpected error:", traceback.format_exc(), sep="\n")
        code = 2
        
    return code

if __name__ == "__main__": 
    sys.exit(main())

