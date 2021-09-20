import os

project_directory = os.path.abspath(os.path.join(__file__ ,"../.."))
configs_directory = os.path.join(project_directory, "configs/")
configuration_items_directory = os.path.join(configs_directory, 'configuration_items/')
inventory_file_name = os.path.join(project_directory, 'inventory/static-inventory')
