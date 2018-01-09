import os
import unittest

from services.source_code_model_service import SourceCodeModelSubServiceId

class SourceCodeModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.file_to_be_built = tempfile.NamedTemporaryFile(suffix='.cpp', bufsize=0)
        cls.file_to_be_built.write(' \
            #include <vector> \n\
            int main() {      \n\
                return 0;     \n\
            }                 \n\
        ')
        cls.json_compilation_database = tempfile.NamedTemporaryFile(suffix='.json', bufsize=0)
        cls.json_compilation_database.write(('                          \
            {{                                                      \n  \
                "directory": "/tmp",                                \n  \
                "command": "/usr/bin/c++ -o dummy.o -c dummy.cpp",  \n  \
                "file": "dummy.cpp"                                 \n  \
            }}                                                          \
        '))

    @classmethod
    def tearDownClass(cls):
        cls.json_compilation_database.close()

    def setUp(self):
        import cxxd_mocks
        from services.source_code_model_service import SourceCodeModel
        self.service = SourceCodeModel(cxxd_mocks.ServicePluginMock())
        self.unknown_subservice_id = 0xABABABA

    def test_if_startup_callback_instantiates_parser_and_services_for_valid_compilation_db_and_proj_root_root_dir(self):
        self.assertEqual(self.service.parser, None)
        self.assertEqual(self.service.service, None)
        self.service.startup_callback([os.path.dirname(self.json_compilation_database.name), self.json_compilation_database.name])
        self.assertNotEqual(self.service.parser, None)
        self.assertNotEqual(self.service.service, None)

    def test_if_startup_callback_does_not_instantiate_parser_and_services_for_inexisting_compilation_db_and_proj_root_root_dir(self):
        self.assertEqual(self.service.parser, None)
        self.assertEqual(self.service.service, None)
        self.service.startup_callback(['inexisting_directory', 'inexisting_compilation_db'])
        self.assertEqual(self.service.parser, None)
        self.assertEqual(self.service.service, None)

    def test_if_call_returns_false_and_none_when_triggered_with_unknown_sub_service_id(self):
        self.service.startup_callback([os.path.dirname(self.json_compilation_database.name), self.json_compilation_database.name])
        success, args = self.service([self.unknown_subservice_id])
        self.assertEqual(success, False)
        self.assertEqual(args, None)

    def test_if_call_returns_false_and_none_when_initialized_with_inexisting_compilation_db_and_proj_root_dir(self):
        self.service.startup_callback(['inexisting_directory', 'inexisting_compilation_db'])
        success, args = self.service([self.unknown_subservice_id])
        self.assertEqual(success, False)
        self.assertEqual(args, None)

if __name__ == '__main__':
    unittest.main()
