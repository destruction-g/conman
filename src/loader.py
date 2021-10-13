import os, json

PROJECT_DIRECTORY = os.path.abspath(os.path.join(__file__ , "../.."))

class Loader:
    def __init__(self):
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

        self.__configs_directory = configs_directory
        self.__configuration_items_directory = configuration_items_directory
        self.__ansible_inventory_file_name = ansible_inventory_file_name
        self.__keys_directory = keys_directory

        configuration = {}
        
        # read main configurations "defaults", "sources", "services", "acls"
        configuraiton_array = ["defaults", "sources", "services", "acls"]
        for parameter_type in configuraiton_array:
            try:
                json_file = json.load(open(os.path.join(configs_directory, parameter_type + ".json")))
                configuration[parameter_type] = json_file
            except Exception as e:
                print('[Config.__init__] - failed to read %s: %s' % (parameter_type, e))
                raise

        # read main configuration_items:
        configuration["configuration_items"] = {}
        for inventory_hostname in os.listdir(configuration_items_directory):
            try:
                json_file = json.load(open(os.path.join(configuration_items_directory, inventory_hostname)))
                configuration["configuration_items"].update({os.path.splitext(inventory_hostname)[0]: json_file})
            except Exception as e:
                print('[Config.__init__] - failed to read configuration item %s: %s' % (inventory_hostname, e))
                raise

        # fill ips
        configuration_items = configuration["configuration_items"]
        for name, host in configuration_items.items():
            if "ip" not in host:
                host["ip"] = socket.gethostbyname(name)
            configuration_items[name].update(host)

        #self.create_inventory_file_for_ansible(configuration)

        self.__configuration = configuration


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

