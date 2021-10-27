import os, yaml, json

PROJECT_DIRECTORY = os.path.abspath(os.path.join(__file__ , "../.."))

class Loader:
    def __init__(self):
        configs_directory, configuration_items_directory, ansible_inventory_file_name, keys_directory = "", "", "", "" 

        try:
            settings_json_file = self.__loadConfigJSON(os.path.join(PROJECT_DIRECTORY, "settings.json"))
            configs_directory = os.path.expandvars(settings_json_file["CONFIGS_DIRECTORY"]) 
            keys_directory = os.path.expandvars(settings_json_file["KEYS_DIRECTORY"])
            ansible_inventory_file_name = os.path.expandvars(settings_json_file["ANSIBLE_INVENTORY_FILE_NAME"])
        except Exception as e:
            configs_directory = os.path.expanduser("~/.config/conman/")
            keys_directory = os.path.join(configs_directory, "files/keys/")
            ansible_inventory_file_name = os.path.join(PROJECT_DIRECTORY, 'inventory/static-inventory')

            settings_json_file = open(os.path.join(PROJECT_DIRECTORY, "settings.json"), "w")
            settings_json_file.write(json.dumps({
                                                "CONFIGS_DIRECTORY": configs_directory,
                                                "ANSIBLE_INVENTORY_FILE_NAME": ansible_inventory_file_name,
                                                "KEYS_DIRECTORY": keys_directory
            }, indent=0, sort_keys=True))
            settings_json_file.close()

        self.__configs_directory = configs_directory
        self.__configuration_items_directory = configuration_items_directory
        self.__ansible_inventory_file_name = ansible_inventory_file_name
        self.__keys_directory = keys_directory

        configuration = {}
        
        # read main configurations "defaults", "sources", "services", "acls"
        try:
            configuration["defaults"] = self.__loadConfigJSON(os.path.join(configs_directory, "defaults.json"))
        except Exception as e:
            print('[Config.__init__] - failed to read default settings from defaults.json: %s' % e)
            raise

        try:
            yaml_file = self.__loadConfigYAML(os.path.join(configs_directory,  "iptables.yaml"))
            for parameter_type in yaml_file:
                configuration[parameter_type] = yaml_file[parameter_type];
        except Exception as e:
            print('[Config.__init__] - failed to read iptables rules from iptables.yml: %s' % e)
            raise

        # read main configuration_items:
        try:
            configuration["configuration_items"] = self.__loadConfigYAML(os.path.join(configs_directory,  "hosts.yaml"))
        except Exception as e:
            print('[Config.__init__] - failed to read configuration items from hosts.yaml: %s' % e)
            raise

        # fill ips
        configuration_items = configuration["configuration_items"]
        for name, host in configuration_items.items():
            if "ip" not in host:
                host["ip"] = socket.gethostbyname(name)
            configuration_items[name].update(host)

        #self.create_inventory_file_for_ansible(configuration)

        self.__configuration = configuration


    def __loadConfigYAML(self, path):
        with open(path, 'r') as f:
            yaml_file = yaml.safe_load(f)
            return  yaml_file


    def __loadConfigJSON(self, path):
        with open(path, 'r') as f:
            json_file = json.load(f)
            return json_file


    def get_configuration(self):
        return self.__configuration


    def create_inventory_file_for_ansible(self, configuration):
        ansible_inventory_dict = {}
        for configuration_item_hostname in configuration["configuration_items"]:
            configuration_item_dict = configuration["configuration_items"][configuration_item_hostname]
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

