import unittest

from core import Core

class TestCore(unittest.TestCase):
    def setUp(self):
        configuration = {
                "configuration_items": {
                    "serv-1": {
                        "groups": ["internal"],
                        "host_name": "serv-1",
                        "acls": ["default", "debug"],
                        "alias": ["serv-1.test", "serv-1.service"],
                        "ip": "23.88.126.90"
                    },
                    "serv-2":{
                        "groups": ["internal"],
                        "host_name": "serv-2",
                        "acls": ["default", "debug"],
                        "ip": "23.88.127.228" 
                    }  
                },
                "acls": {
                    "default": {
                        "dns-local": ["localhost"],
                        "docker": ["internal"],
                        "ssh": ["all"]
                    },
                    "debug": {
                        "some_service": ["all"]
                    } 
                },
                "services": {
                    "dns-local": [
                        {
                            "destination_port": 53,
                            "destination_ip": "127.0.0.53",
                            "protocol": "tcp",
                            "comment": "dns"
                        },
                        {
                            "destination_port": 53,
                            "destination_ip": "127.0.0.53",
                            "protocol": "udp",
                            "comment": "dns"
                        }
                    ],
                    "ssh": [
                        {
                            "destination_port": 22,
                            "protocol": "tcp"
                        }
                    ],
                     "docker": [
                        {
                            "destination_port": 2377,
                            "protocol": "tcp",
                            "comment": "swarm"
                        },
                        {
                            "destination_port": 2376,
                            "protocol": "tcp",
                            "comment": "tls"
                        },
                        {
                            "destination_port": 4789,
                            "protocol": "udp",
                            "comment": "ingress network"
                        },
                        {
                            "destination_port": 7946,
                            "protocol": "tcp",
                            "comment": "network discovery"
                        },
                        {
                            "destination_port": 7946,
                            "protocol": "udp",
                            "comment": "network discovery"
                        }
                    ],
                    "some_service": [
                        {
                            "destination_port": 6666,
                            "protocol": "tcp",
                            "in_docker": True, 
                            "comment": "yahaaaa, blay!"
                        },
                        {
                            "destination_port": 7777,
                            "protocol": "tcp",
                            "comment": "yahaaaa, blay!"
                        }
                    ]
                },
                "sources": {
                    "all": [
                        {
                            "type": "address",
                            "address": "0.0.0.0/0"
                        }
                    ],
                    "localhost": [
                        {
                            "type": "address",
                            "address": "127.0.0.1"
                        }
                    ],
                    "internal": [
                        {
                            "type": "group",
                            "group": "internal"
                        }
                    ]
                }
        }
        self.core = Core(configuration) 


    def test_get_configuration(self):
        # TODO
        self.assertEqual(1, 1)


    def test_get_configuration_items_directory(self):
        # TODO
        self.assertEqual(1, 1)


    def test_get_keys_directory(self):
        # TODO
        self.assertEqual(1, 1)


    def test_generate_configuration_items_dict(self):
        # TODO
        self.assertEqual(1, 1)
    

    def test_generate_hosts_file_dict(self):
        expect = {
                "success": True,
                "data": {
                    "serv-1": "23.88.126.90", "serv-2": "23.88.127.228", 
                    "serv-1.service": "23.88.126.90", "serv-1.test": "23.88.126.90"
                    }
                } 
        actual = self.core.generate_hosts_file_dict()
        self.assertEqual(actual, expect)
        

    def test_write_static_inventory_file_for_ansible(self):
        # TODO
        self.assertEqual(1, 1)
        

    def test_generate_acl_source_group_items(self):
        # TODO
        self.assertEqual(1, 1)
        

    def test_generate_acl_source_single_item(self):
        # TODO
        self.assertEqual(1, 1)
        

    def test_compile_ansible_acl_element_dict(self):
        # TODO
        self.assertEqual(1, 1)
        

    def test_generate_ansible_iptables_acls_array(self):
        # TODO
        self.assertEqual(1, 1)

if __name__ == "__main__":
  unittest.main()
