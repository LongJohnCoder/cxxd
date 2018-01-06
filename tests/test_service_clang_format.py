import unittest

class ClangFormatTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.file_to_perform_clang_format_on = tempfile.NamedTemporaryFile()
        cls.file_to_perform_clang_format_on.write(' \
            #include <vector> \
            int main() {      \
                return 0;     \
            }                 \
        ')

        cls.clang_format_config_file = tempfile.NamedTemporaryFile()
        cls.clang_format_config_file.write('        \
            BasedOnStyle: LLVM                      \
            AccessModifierOffset: -4                \
            AlwaysBreakTemplateDeclarations: true   \
            ColumnLimit: 100                        \
            Cpp11BracedListStyle: true              \
            IndentWidth: 4                          \
            MaxEmptyLinesToKeep: 2                  \
            PointerBindsToType: true                \
            Standard: Cpp11                         \
            TabWidth: 4                             \
        ')

    @classmethod
    def tearDownClass(cls):
        cls.file_to_perform_clang_format_on.close()
        cls.clang_format_config_file.close()

    def setUp(self):
        import cxxd_mocks
        from services.clang_format_service import ClangFormat
        self.service = ClangFormat(cxxd_mocks.ServicePluginMock())

    def test_if_startup_callback_appends_clang_format_config_file_correctly(self):
        clang_format_cmd_pre_startup_callback = self.service.format_cmd
        self.service.startup_callback([self.clang_format_config_file.name])
        self.assertEqual(self.service.format_cmd, clang_format_cmd_pre_startup_callback + self.clang_format_config_file.name)

    def test_if_call_returns_true_for_success_and_none_for_args_when_run_on_existing_file(self):
        filename = self.file_to_perform_clang_format_on.name
        self.service.startup_callback([self.clang_format_config_file.name])
        success, args = self.service([filename])
        self.assertEqual(success, True)
        self.assertEqual(args, None)

    def test_if_call_returns_false_for_success_and_none_for_args_when_run_on_inexisting_file(self):
        filename = 'inexisting_filename'
        self.service.startup_callback([self.clang_format_config_file.name])
        success, args = self.service([filename])
        self.assertEqual(success, False)
        self.assertEqual(args, None)

if __name__ == '__main__':
    unittest.main()
