import unittest

class ClangTidyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.file_to_perform_clang_tidy_on = tempfile.NamedTemporaryFile(suffix='.cpp')
        cls.file_to_perform_clang_tidy_on.write('   \
            #include <vector>\n                     \
            int main() {     \n                     \
                return 0;    \n                     \
            }                                       \
        ')
        cls.json_compilation_database = tempfile.NamedTemporaryFile(suffix='.json')
        cls.json_compilation_database.write(('                  \
            {{                                            \n    \
                "directory": "/tmp",                      \n    \
                "command": "/usr/bin/c++ -o {0}.o -c {1}",\n    \
                "file": "{2}"                             \n    \
            }}                                                  \
        ').format(cls.file_to_perform_clang_tidy_on.name, cls.file_to_perform_clang_tidy_on.name, cls.file_to_perform_clang_tidy_on.name))
        cls.txt_compile_flags = ['-D_GLIBCXX_DEBUG', '-Wabi', '-Wconversion', '-Winline']
        cls.txt_compilation_database = tempfile.NamedTemporaryFile(suffix='.txt', bufsize=0)
        cls.txt_compilation_database.write('\n'.join(cls.txt_compile_flags))

    @classmethod
    def tearDownClass(cls):
        cls.file_to_perform_clang_tidy_on.close()
        cls.json_compilation_database.close()
        cls.txt_compilation_database.close()

    def setUp(self):
        import cxxd_mocks
        from services.clang_tidy_service import ClangTidy
        self.service = ClangTidy(cxxd_mocks.ServicePluginMock())
        self.unsupported_compilation_database = 'compiler_flags.yaml'

    def test_if_compile_flags_are_set_to_none_by_default(self):
        self.assertEqual(self.service.clang_tidy_compile_flags, None)

    def test_if_clang_tidy_binary_is_available_on_the_system_path(self):
        self.assertNotEqual(self.service.clang_tidy_binary, None)

    def test_if_startup_callback_sets_compile_flags_accordingly_when_json_compilation_database_provided(self):
        self.assertEqual(self.service.clang_tidy_compile_flags, None)
        self.service.startup_callback([self.json_compilation_database.name])
        self.assertEqual(self.service.clang_tidy_compile_flags, '-p ' + self.json_compilation_database.name)

    def test_if_startup_callback_sets_compile_flags_accordingly_when_txt_compilation_database_provided(self):
        self.assertEqual(self.service.clang_tidy_compile_flags, None)
        self.service.startup_callback([self.txt_compilation_database.name])
        self.assertEqual(self.service.clang_tidy_compile_flags, '-- ' + ' '.join(self.txt_compile_flags))

    def test_if_startup_callback_sets_compile_flags_accordingly_when_unsupported_compilation_database_provided(self):
        self.assertEqual(self.service.clang_tidy_compile_flags, None)
        self.service.startup_callback([self.unsupported_compilation_database])
        self.assertEqual(self.service.clang_tidy_compile_flags, None)

    def test_if_startup_callback_sets_compile_flags_accordingly_when_compilation_database_file_provided_is_not_existing(self):
        self.assertEqual(self.service.clang_tidy_compile_flags, None)
        self.service.startup_callback(['some_totally_compilation_database_random_name'])
        self.assertEqual(self.service.clang_tidy_compile_flags, None)

    def test_if_startup_callback_sets_compile_flags_accordingly_when_clang_tidy_binary_is_not_available_on_the_system_path(self):
        self.service.clang_tidy_binary = None
        self.assertEqual(self.service.clang_tidy_compile_flags, None)
        self.service.startup_callback([self.json_compilation_database.name])
        self.assertEqual(self.service.clang_tidy_compile_flags, None)

    def test_if_call_returns_true_for_success_and_file_containing_clang_tidy_output_when_run_on_existing_file_without_applying_fixes(self):
        self.service.startup_callback([self.json_compilation_database.name])
        success, clang_tidy_output = self.service([self.file_to_perform_clang_tidy_on.name, False])
        self.assertEqual(success, True)
        self.assertNotEqual(clang_tidy_output, None)

    def test_if_call_returns_true_for_success_and_file_containing_clang_tidy_output_when_run_on_existing_file_with_applying_fixes(self):
        self.service.startup_callback([self.json_compilation_database.name])
        success, clang_tidy_output = self.service([self.file_to_perform_clang_tidy_on.name, True])
        self.assertEqual(success, True)
        self.assertNotEqual(clang_tidy_output, None)

    def test_if_call_returns_false_for_success_and_no_output_when_run_on_inexisting_file_without_applying_fixes(self):
        self.service.startup_callback([self.json_compilation_database.name])
        success, clang_tidy_output = self.service(['inexisting_filename', False])        
        self.assertEqual(success, False)
        self.assertEqual(clang_tidy_output, None)

    def test_if_call_returns_false_for_success_and_no_output_when_run_on_inexisting_file_with_applying_fixes(self):
        self.service.startup_callback([self.json_compilation_database.name])
        success, clang_tidy_output = self.service(['inexisting_filename', True])        
        self.assertEqual(success, False)
        self.assertEqual(clang_tidy_output, None)

    def test_if_call_returns_false_for_success_and_no_output_when_clang_tidy_binary_is_not_available_on_the_system_path(self):
        self.service.clang_tidy_binary = None
        self.service.startup_callback([self.json_compilation_database.name])
        success, clang_tidy_output = self.service([self.file_to_perform_clang_tidy_on.name, False])        
        self.assertEqual(success, False)
        self.assertEqual(clang_tidy_output, None)

    def test_if_call_returns_false_for_success_and_no_output_when_compile_flags_are_not_available(self):
        self.service.startup_callback([self.unsupported_compilation_database])
        success, clang_tidy_output = self.service([self.file_to_perform_clang_tidy_on.name, False])        
        self.assertEqual(success, False)
        self.assertEqual(clang_tidy_output, None)

if __name__ == '__main__':
    unittest.main()

