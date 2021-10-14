import unittest

from core import Core

class TestCore(unittest.TestCase):

    maxDiff = None

    def setUp(self):
        configuration = {
            "defaults":{
                "PROXMOX_USER":"root@pam",
                "PROXMOX_PASSWORD":"123",
                "ITEM_SSH_PORT":"22",
                "VPN_TYPE":"pptp",
                "ITEM_DEFAULT_ETH":"eth0",
                "ITEM_HOST_TYPE":"null",
                "ITEM_SSH_KEY_EXCLUSIVE":"1",
                "ITEM_GUEST_KEYS":[
                    
                ],
                "acls":[
                    "default"
                ],
                "ITEM_FORWARD_POLICY_DROP":0
            },
            "sources":{
                "all":[
                    {
                        "type":"address",
                        "address":"0.0.0.0/0"
                    }
                ],
                "localhost":[
                    {
                        "type":"address",
                        "address":"127.0.0.1"
                    }
                ],
                "internal":[
                    {
                        "type":"group",
                        "group":"internal"
                    }
                ]
            },
            "services":{
                "dns-local":[
                    {
                        "destination_port":53,
                        "destination_ip":"127.0.0.53",
                        "protocol":"tcp",
                        "comment":"dns"
                    },
                    {
                        "destination_port":53,
                        "destination_ip":"127.0.0.53",
                        "protocol":"udp",
                        "comment":"dns"
                    }
                ],
                "ssh":[
                    {
                        "destination_port":22,
                        "protocol":"tcp"
                    }
                ],
                "docker":[
                    {
                        "destination_port":2377,
                        "protocol":"tcp",
                        "comment":"swarm"
                    },
                    {
                        "destination_port":2376,
                        "protocol":"tcp",
                        "comment":"tls"
                    },
                    {
                        "destination_port":4789,
                        "protocol":"udp",
                        "comment":"ingress network"
                    },
                    {
                        "destination_port":7946,
                        "protocol":"tcp",
                        "comment":"network discovery"
                    },
                    {
                        "destination_port":7946,
                        "protocol":"udp",
                        "comment":"network discovery"
                    }
                ],
                "some_service":[
                    {
                        "destination_port":6666,
                        "protocol":"tcp",
                        "in_docker":True,
                        "comment":"yahaaaa, blay!"
                    },
                    {
                        "destination_port":7777,
                        "protocol":"tcp",
                        "in_docker":True,
                        "comment":"yahaaaa, blay!"
                    },
                    {
                        "destination_port":8888,
                        "protocol":"tcp",
                        "in_docker":True,
                        "comment":"yahaaaa, blay!"
                    }
                ]
            },
            "acls":{
                "default":{
                    "dns-local":[
                        "localhost"
                    ],
                    "docker":[
                        "internal"
                    ],
                    "some_service":[
                        "internal"
                    ],
                    "ssh":[
                        "all"
                    ]
                },
                "debug":{
                    "some_service":[
                        "all"
                    ]
                }
            },
            "configuration_items":{
                "serv-1":{
                    "groups":[
                        "internal"
                    ],
                    "host_name":"serv-1",
                    "acls":[
                        "default",
                        "debug"
                    ],
                    "ip":"23.88.127.228",
                    "alias": ["serv-1.test", "serv-1.service"]
                },
                "serv-2":{
                    "groups":[
                        "internal"
                    ],
                    "host_name":"serv-2",
                    "acls":[
                        "default"
                    ],
                    "ip":"78.47.84.140"
                }
            }
        }
        self.core = Core(configuration) 


    def test_generate_hosts_file_dict(self):
        expect = {
                "success": True,
                "data": {
                        "serv-1": "23.88.127.228", "serv-2": "78.47.84.140", 
                        "serv-1.service": "23.88.127.228", "serv-1.test": "23.88.127.228"
                    }
        } 
        actual = self.core.generate_hosts_file_dict()
        self.assertEqual(actual, expect)
        

    def test_generate_ansible_iptables_acls_array(self):
        expect = {
            "success":True,
            "data":{
                "docker": [],
                "input": [
                   {
                      "ip":"23.88.127.228",
                      "full_comment":"dns-local dns for localhost",
                      "service_destination_port":53,
                      "service_destination_ip":"127.0.0.53",
                      "service_protocol":"tcp",
                      "service_comment":"dns",
                      "source_type":"address",
                      "source_address":"127.0.0.1"
                   },
                   {
                      "ip":"23.88.127.228",
                      "full_comment":"dns-local dns for localhost",
                      "service_destination_port":53,
                      "service_destination_ip":"127.0.0.53",
                      "service_protocol":"udp",
                      "service_comment":"dns",
                      "source_type":"address",
                      "source_address":"127.0.0.1"
                   },
                   {
                      "ip":"23.88.127.228",
                      "full_comment":"docker swarm for internal",
                      "service_destination_port":2377,
                      "service_protocol":"tcp",
                      "service_comment":"swarm",
                      "source_address":"23.88.127.228",
                      "source_type":"group",
                      "source_comment":"serv-1"
                   },
                   {
                      "ip":"23.88.127.228",
                      "full_comment":"docker swarm for internal",
                      "service_destination_port":2377,
                      "service_protocol":"tcp",
                      "service_comment":"swarm",
                      "source_address":"78.47.84.140",
                      "source_type":"group",
                      "source_comment":"serv-2"
                   },
                   {
                      "ip":"23.88.127.228",
                      "full_comment":"docker tls for internal",
                      "service_destination_port":2376,
                      "service_protocol":"tcp",
                      "service_comment":"tls",
                      "source_address":"23.88.127.228",
                      "source_type":"group",
                      "source_comment":"serv-1"
                   },
                   {
                      "ip":"23.88.127.228",
                      "full_comment":"docker tls for internal",
                      "service_destination_port":2376,
                      "service_protocol":"tcp",
                      "service_comment":"tls",
                      "source_address":"78.47.84.140",
                      "source_type":"group",
                      "source_comment":"serv-2"
                   },
                   {
                      "ip":"23.88.127.228",
                      "full_comment":"docker ingress network for internal",
                      "service_destination_port":4789,
                      "service_protocol":"udp",
                      "service_comment":"ingress network",
                      "source_address":"23.88.127.228",
                      "source_type":"group",
                      "source_comment":"serv-1"
                   },
                   {
                      "ip":"23.88.127.228",
                      "full_comment":"docker ingress network for internal",
                      "service_destination_port":4789,
                      "service_protocol":"udp",
                      "service_comment":"ingress network",
                      "source_address":"78.47.84.140",
                      "source_type":"group",
                      "source_comment":"serv-2"
                   },
                   {
                      "ip":"23.88.127.228",
                      "full_comment":"docker network discovery for internal",
                      "service_destination_port":7946,
                      "service_protocol":"tcp",
                      "service_comment":"network discovery",
                      "source_address":"23.88.127.228",
                      "source_type":"group",
                      "source_comment":"serv-1"
                   },
                   {
                      "ip":"23.88.127.228",
                      "full_comment":"docker network discovery for internal",
                      "service_destination_port":7946,
                      "service_protocol":"tcp",
                      "service_comment":"network discovery",
                      "source_address":"78.47.84.140",
                      "source_type":"group",
                      "source_comment":"serv-2"
                   },
                   {
                      "ip":"23.88.127.228",
                      "full_comment":"docker network discovery for internal",
                      "service_destination_port":7946,
                      "service_protocol":"udp",
                      "service_comment":"network discovery",
                      "source_address":"23.88.127.228",
                      "source_type":"group",
                      "source_comment":"serv-1"
                   },
                   {
                      "ip":"23.88.127.228",
                      "full_comment":"docker network discovery for internal",
                      "service_destination_port":7946,
                      "service_protocol":"udp",
                      "service_comment":"network discovery",
                      "source_address":"78.47.84.140",
                      "source_type":"group",
                      "source_comment":"serv-2"
                   },
                   {
                      "ip":"23.88.127.228",
                      "full_comment":"some_service yahaaaa, blay! for internal",
                      "service_destination_port":6666,
                      "service_protocol":"tcp",
                      "service_in_docker":True,
                      "service_comment":"yahaaaa, blay!",
                      "source_address":"23.88.127.228",
                      "source_type":"group",
                      "source_comment":"serv-1"
                   },
                   {
                      "ip":"23.88.127.228",
                      "full_comment":"some_service yahaaaa, blay! for internal",
                      "service_destination_port":6666,
                      "service_protocol":"tcp",
                      "service_in_docker":True,
                      "service_comment":"yahaaaa, blay!",
                      "source_address":"78.47.84.140",
                      "source_type":"group",
                      "source_comment":"serv-2"
                   },
                   {
                      "ip":"23.88.127.228",
                      "full_comment":"some_service yahaaaa, blay! for internal",
                      "service_destination_port":7777,
                      "service_protocol":"tcp",
                      "service_in_docker":True,
                      "service_comment":"yahaaaa, blay!",
                      "source_address":"23.88.127.228",
                      "source_type":"group",
                      "source_comment":"serv-1"
                   },
                   {
                      "ip":"23.88.127.228",
                      "full_comment":"some_service yahaaaa, blay! for internal",
                      "service_destination_port":7777,
                      "service_protocol":"tcp",
                      "service_in_docker":True,
                      "service_comment":"yahaaaa, blay!",
                      "source_address":"78.47.84.140",
                      "source_type":"group",
                      "source_comment":"serv-2"
                   },
                   {
                      "ip":"23.88.127.228",
                      "full_comment":"some_service yahaaaa, blay! for internal",
                      "service_destination_port":8888,
                      "service_protocol":"tcp",
                      "service_in_docker":True,
                      "service_comment":"yahaaaa, blay!",
                      "source_address":"23.88.127.228",
                      "source_type":"group",
                      "source_comment":"serv-1"
                   },
                   {
                      "ip":"23.88.127.228",
                      "full_comment":"some_service yahaaaa, blay! for internal",
                      "service_destination_port":8888,
                      "service_protocol":"tcp",
                      "service_in_docker":True,
                      "service_comment":"yahaaaa, blay!",
                      "source_address":"78.47.84.140",
                      "source_type":"group",
                      "source_comment":"serv-2"
                   },
                   {
                      "ip":"23.88.127.228",
                      "full_comment":"ssh for all",
                      "service_destination_port":22,
                      "service_protocol":"tcp",
                      "source_type":"address",
                      "source_address":"0.0.0.0/0"
                   },
                   {
                      "ip":"23.88.127.228",
                      "full_comment":"some_service yahaaaa, blay! for all",
                      "service_destination_port":6666,
                      "service_protocol":"tcp",
                      "service_in_docker":True,
                      "service_comment":"yahaaaa, blay!",
                      "source_type":"address",
                      "source_address":"0.0.0.0/0"
                   },
                   {
                      "ip":"23.88.127.228",
                      "full_comment":"some_service yahaaaa, blay! for all",
                      "service_destination_port":7777,
                      "service_protocol":"tcp",
                      "service_in_docker":True,
                      "service_comment":"yahaaaa, blay!",
                      "source_type":"address",
                      "source_address":"0.0.0.0/0"
                   },
                   {
                      "ip":"23.88.127.228",
                      "full_comment":"some_service yahaaaa, blay! for all",
                      "service_destination_port":8888,
                      "service_protocol":"tcp",
                      "service_in_docker":True,
                      "service_comment":"yahaaaa, blay!",
                      "source_type":"address",
                      "source_address":"0.0.0.0/0"
                   }
                ]
            }
        }
        actual = self.core.generate_ansible_iptables_acls_array("serv-1")
        self.assertEqual(actual, expect)

if __name__ == "__main__":
  unittest.main()
