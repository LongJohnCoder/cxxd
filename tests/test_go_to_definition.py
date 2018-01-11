import mock
import os
import sqlite3
import unittest

import parser.clang_parser
import parser.tunit_cache

class SourceCodeModelGoToDefinitionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.test_file = tempfile.NamedTemporaryFile(suffix='.cpp', bufsize=0)
        cls.test_file.write('\
#include <vector>       \n\
                        \n\
int foobar() {          \n\
    return 0;           \n\
}                       \n\
                        \n\
int main() {            \n\
    std::vector<int> v; \n\
    return foobar();    \n\
}                       \n\
                        \n\
int fun() {             \n\
    return bar();       \n\
}                       \n\
        ')

        cls.test_file_edited = tempfile.NamedTemporaryFile(suffix='.cpp', bufsize=0)
        cls.test_file_edited.write('\
#include <vector>           \n\
                            \n\
                            \n\
int foobar() {              \n\
    return 0;               \n\
}                           \n\
                            \n\
int main() {                \n\
    std::vector<int> v;     \n\
    int result = foobar();  \n\
    return result;          \n\
}                           \n\
                            \n\
int fun() {                 \n\
    return bar();           \n\
}                           \n\
        ')

        cls.txt_compile_flags = ['-D_GLIBCXX_DEBUG', '-Wabi', '-Wconversion', '-Winline']
        cls.txt_compilation_database = open('compile_flags.txt', 'w') # tempfile.NamedTemporaryFile(suffix='.txt', bufsize=0) # TODO handle this somehow differently. apply to other unit tests as well (make a common utility class)
        cls.txt_compilation_database.write('\n'.join(cls.txt_compile_flags))

        cls.parser = parser.clang_parser.ClangParser(
            cls.txt_compilation_database.name,
            parser.tunit_cache.TranslationUnitCache(parser.tunit_cache.NoCache())
        )

    @classmethod
    def tearDownClass(cls):
        cls.test_file.close()
        cls.test_file_edited.close()
        cls.txt_compilation_database.close()

    def setUp(self):
        import cxxd_mocks
        from services.source_code_model.go_to_definition.go_to_definition import GoToDefinition
        self.project_root_directory = os.path.dirname(self.test_file.name)
        self.service = GoToDefinition(self.parser, cxxd_mocks.SymbolDatabaseMock(), self.project_root_directory)

    def test_if_call_returns_true_and_definition_is_found_for_local_symbol(self):
        success, definition = self.service(
            [self.test_file.name, self.test_file.name, 9, 12]
        )
        filename, line, column = definition
        self.assertEqual(success, True)
        self.assertEqual(filename, self.test_file.name)
        self.assertEqual(line, 3)
        self.assertEqual(column, 5)

    def test_if_call_returns_true_and_definition_is_found_for_local_symbol_with_current_tunit_being_modified(self):
        success, definition = self.service(
            [self.test_file.name, self.test_file_edited.name, 10, 18]
        )
        filename, line, column = definition
        self.assertEqual(success, True)
        self.assertEqual(filename, self.test_file.name) # still returns an original filename and not the edited (temporary) one
        self.assertEqual(line, 4)
        self.assertEqual(column, 5)

    def test_if_call_returns_true_and_definition_is_found_for_non_local_symbol_included_via_header(self):
        success, definition = self.service(
            [self.test_file.name, self.test_file.name, 8, 10]
        )
        filename, line, column = definition
        self.assertEqual(success, True)
        self.assertNotEqual(filename, self.test_file.name)
        self.assertGreaterEqual(line, 0)
        self.assertGreaterEqual(column, 0)

    def test_if_call_returns_true_and_definition_is_found_for_non_local_symbol_included_via_header_with_current_tunit_being_modified(self):
        success, definition = self.service(
            [self.test_file.name, self.test_file_edited.name, 9, 10]
        )
        filename, line, column = definition
        self.assertEqual(success, True)
        self.assertNotEqual(filename, self.test_file.name)
        self.assertGreaterEqual(line, 0)
        self.assertGreaterEqual(column, 0)

    def test_if_call_returns_false_and_definition_is_not_found_for_non_local_symbol_not_included_via_header_and_not_found_in_symbol_db(self):
        cursor = mock.MagicMock(sqlite3.Cursor)
        cursor.fetchall.return_value = None
        with mock.patch.object(self.service.symbol_db, 'get_definition', return_value=cursor) as mock_symbol_db_get_definition:
            success, definition = self.service(
                [self.test_file.name, self.test_file.name, 13, 12]
            )
        filename, line, column = definition
        self.assertEqual(success, False)
        self.assertEqual(filename, '')
        self.assertEqual(line, 0)
        self.assertEqual(column, 0)

    def test_if_call_returns_false_and_definition_is_not_found_for_non_local_symbol_not_included_via_header_and_not_found_in_symbol_db_with_current_tunit_being_modified(self):
        cursor = mock.MagicMock(sqlite3.Cursor)
        cursor.fetchall.return_value = None
        with mock.patch.object(self.service.symbol_db, 'get_definition', return_value=cursor) as mock_symbol_db_get_definition:
            success, definition = self.service(
                [self.test_file.name, self.test_file_edited.name, 15, 12]
            )
        filename, line, column = definition
        self.assertEqual(success, False)
        self.assertEqual(filename, '')
        self.assertEqual(line, 0)
        self.assertEqual(column, 0)

    def test_if_call_returns_true_and_definition_is_found_for_non_local_symbol_not_included_via_header_but_found_in_symbol_db(self):
        cursor = mock.MagicMock(sqlite3.Cursor)
        cursor.fetchall.return_value = [('name_of_some_other_translation_unit_extracted_from_symbol_db', 124, 5)] # some random unimportant value
        with mock.patch.object(self.service.symbol_db, 'get_definition', return_value=cursor) as mock_symbol_db_get_definition:
            success, definition = self.service(
                [self.test_file.name, self.test_file.name, 13, 12]
            )
        filename, line, column = definition
        self.assertEqual(success, True)
        self.assertNotEqual(filename, self.test_file.name)
        self.assertGreaterEqual(filename.find(self.project_root_directory), 0)
        self.assertGreaterEqual(line, 0)
        self.assertGreaterEqual(column, 0)

    def test_if_call_returns_true_and_definition_is_found_for_non_local_symbol_not_included_via_header_but_found_in_symbol_db_with_current_tunit_being_modified(self):
        cursor = mock.MagicMock(sqlite3.Cursor)
        cursor.fetchall.return_value = [('name_of_some_other_translation_unit_extracted_from_symbol_db', 124, 5)] # some random unimportant value
        with mock.patch.object(self.service.symbol_db, 'get_definition', return_value=cursor) as mock_symbol_db_get_definition:
            success, definition = self.service(
                [self.test_file.name, self.test_file_edited.name, 15, 12]
            )
        filename, line, column = definition
        self.assertEqual(success, True)
        self.assertNotEqual(filename, self.test_file.name)
        self.assertGreaterEqual(filename.find(self.project_root_directory), 0)
        self.assertGreaterEqual(line, 0)
        self.assertGreaterEqual(column, 0)

    # TODO test for non-parseable translation units (compile errors?)

if __name__ == '__main__':
    unittest.main()

