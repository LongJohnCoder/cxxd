import unittest

import parser.clang_parser
import parser.tunit_cache

class SourceCodeModelDiagnosticsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.test_file_with_no_diagnostics = tempfile.NamedTemporaryFile(suffix='.cpp', bufsize=0)
        cls.test_file_with_no_diagnostics.write(' \
            #include <vector> \n\
            int main() {      \n\
                return 0;     \n\
            }                 \n\
        ')

        cls.test_file_with_no_diagnostics_edited = tempfile.NamedTemporaryFile(suffix='.cpp', bufsize=0)
        cls.test_file_with_no_diagnostics_edited.write(' \
            #include <vector> \n\
                              \n\
            int main() {      \n\
                return 0;     \n\
            }                 \n\
        ')

        cls.test_file_with_compile_errors = tempfile.NamedTemporaryFile(suffix='.cpp', bufsize=0)
        cls.test_file_with_compile_errors.write(' \
            #include <vector> \n\
            compile error     \n\
            int main() {      \n\
                return 0;     \n\
            }                 \n\
        ')

        cls.test_file_with_compile_errors_edited = tempfile.NamedTemporaryFile(suffix='.cpp', bufsize=0)
        cls.test_file_with_compile_errors_edited.write(' \
            #include <vector> \n\
                              \n\
            compile error     \n\
                              \n\
            int main() {      \n\
                return 0;     \n\
            }                 \n\
        ')

        cls.txt_compile_flags = ['-D_GLIBCXX_DEBUG', '-Wabi', '-Wconversion', '-Winline']
        cls.txt_compilation_database = tempfile.NamedTemporaryFile(suffix='.txt', bufsize=0)
        cls.txt_compilation_database.write('\n'.join(cls.txt_compile_flags))

        cls.parser = parser.clang_parser.ClangParser(
            cls.txt_compilation_database.name,
            parser.tunit_cache.TranslationUnitCache(parser.tunit_cache.NoCache())
        )

    @classmethod
    def tearDownClass(cls):
        cls.test_file_with_no_diagnostics.close()
        cls.test_file_with_no_diagnostics_edited.close()
        cls.test_file_with_compile_errors.close()
        cls.test_file_with_compile_errors_edited.close()
        cls.txt_compilation_database.close()

    def setUp(self):
        import cxxd_mocks
        from services.source_code_model.diagnostics.diagnostics import Diagnostics
        self.service = Diagnostics(self.parser)

    def test_if_call_returns_true_and_empty_diagnostics_iterator_for_diagnostics_free_source_code(self):
        success, diagnostics_iter = self.service([self.test_file_with_no_diagnostics.name, self.test_file_with_no_diagnostics.name])
        self.assertEqual(success, True)
        self.assertEqual(len(diagnostics_iter), 0)

    def test_if_call_returns_true_and_empty_diagnostics_iterator_for_edited_diagnostics_free_source_code(self):
        success, diagnostics_iter = self.service([self.test_file_with_no_diagnostics.name, self.test_file_with_no_diagnostics_edited.name])
        self.assertEqual(success, True)
        self.assertEqual(len(diagnostics_iter), 0)

    def test_if_call_returns_true_and_empty_diagnostics_iterator_for_source_code_containing_compiling_error(self):
        success, diagnostics_iter = self.service([self.test_file_with_compile_errors.name, self.test_file_with_compile_errors.name])
        self.assertEqual(success, True)
        self.assertNotEqual(len(diagnostics_iter), 0)

    def test_if_call_returns_true_and_empty_diagnostics_iterator_for_edited_source_code_containing_compiling_error(self):
        success, diagnostics_iter = self.service([self.test_file_with_compile_errors.name, self.test_file_with_compile_errors_edited.name])
        self.assertEqual(success, True)
        self.assertNotEqual(len(diagnostics_iter), 0)

    def test_if_call_returns_false_and_none_as_diagnostics_iterator_for_inexisting_source_code(self):
        success, diagnostics_iter = self.service(['inexisting_source_code_filename', 'inexisting_source_code_filename'])
        self.assertEqual(success, False)
        self.assertEqual(diagnostics_iter, None)

if __name__ == '__main__':
    unittest.main()
