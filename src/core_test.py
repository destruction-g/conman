import unittest

from core import Core

class TestCore(unittest.TestCase):
    def setUp(self):
        self.core = Core("test_data/", "test_data/configuration_items/", "", "test_data/files/keys/") 


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
                    "serv-1": "23.88.127.191", "serv-2": "23.88.127.228", "serv-3": "23.88.126.90",
                    "serv-1.service": "23.88.127.191", "serv-1.test": "23.88.127.191"
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
