import mock
import os
import unittest

import parser.clang_parser
import parser.tunit_cache
from file_generator import FileGenerator
from services.source_code_model.indexer.clang_indexer import SourceCodeModelIndexerRequestId

class ClangIndexerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_file                = FileGenerator.gen_simple_cpp_file()
        cls.test_file_edited         = FileGenerator.gen_simple_cpp_file(edited=True)
        cls.txt_compilation_database = FileGenerator.gen_txt_compilation_database()

        cls.parser = parser.clang_parser.ClangParser(
            cls.txt_compilation_database.name,
            parser.tunit_cache.TranslationUnitCache(parser.tunit_cache.NoCache())
        )

    @classmethod
    def tearDownClass(cls):
        FileGenerator.close_gen_file(cls.test_file)
        FileGenerator.close_gen_file(cls.test_file_edited)
        FileGenerator.close_gen_file(cls.txt_compilation_database)

    def setUp(self):
        import cxxd_mocks
        from services.source_code_model.indexer.clang_indexer import ClangIndexer
        self.unsupported_request = 0xFF
        self.root_directory = os.path.dirname(self.test_file.name)
        self.service = ClangIndexer(self.parser, self.root_directory)

    def test_if_symbol_db_is_located_in_root_directory(self):
        self.assertEqual(self.service.symbol_db_path, os.path.join(self.root_directory, self.service.symbol_db_name))

    def test_if_call_returns_false_for_unsupported_request(self):
        success, args = self.service([self.unsupported_request])
        self.assertEqual(success, False)
        self.assertEqual(args, None)

    def test_if_run_on_single_file_skips_indexing_when_file_is_edited(self):
        with mock.patch('services.source_code_model.indexer.clang_indexer.index_single_file') as mock_index_single_file:
            success, args = self.service([SourceCodeModelIndexerRequestId.RUN_ON_SINGLE_FILE, self.test_file.name, self.test_file_edited.name])
        mock_index_single_file.assert_not_called()
        self.assertEqual(success, True)
        self.assertEqual(args, None)

    def test_if_run_on_single_file_deletes_an_entry_from_symbol_db_using_its_basename_and_then_successfully_indexes_the_file(self):
        manager = mock.MagicMock()
        with mock.patch.object(self.service.symbol_db, 'open') as mock_symbol_db_open:
            with mock.patch.object(self.service.symbol_db, 'delete') as mock_symbol_db_delete_entry:
                with mock.patch('services.source_code_model.indexer.clang_indexer.index_single_file', return_value=True) as mock_index_single_file:
                    manager.attach_mock(mock_symbol_db_open, 'mock_symbol_db_open')
                    manager.attach_mock(mock_symbol_db_delete_entry, 'mock_symbol_db_delete_entry')
                    manager.attach_mock(mock_index_single_file, 'mock_index_single_file')
                    success, args = self.service([SourceCodeModelIndexerRequestId.RUN_ON_SINGLE_FILE, self.test_file.name, self.test_file.name])
        manager.assert_has_calls(
            [
                mock.call.mock_symbol_db_open(self.service.symbol_db_path),
                mock.call.mock_symbol_db_delete_entry(os.path.basename(self.test_file.name)),
                mock.call.mock_index_single_file(self.service.parser, self.service.root_directory, self.test_file.name, self.test_file.name, self.service.symbol_db)
            ]
        )
        self.assertEqual(success, True)
        self.assertEqual(args, None)

    def test_if_run_on_single_file_deletes_an_entry_from_symbol_db_using_its_basename_and_then_failes_to_index_the_file(self):
        manager = mock.MagicMock()
        with mock.patch.object(self.service.symbol_db, 'open') as mock_symbol_db_open:
            with mock.patch.object(self.service.symbol_db, 'delete') as mock_symbol_db_delete_entry:
                with mock.patch('services.source_code_model.indexer.clang_indexer.index_single_file', return_value=False) as mock_index_single_file:
                    manager.attach_mock(mock_symbol_db_open, 'mock_symbol_db_open')
                    manager.attach_mock(mock_symbol_db_delete_entry, 'mock_symbol_db_delete_entry')
                    manager.attach_mock(mock_index_single_file, 'mock_index_single_file')
                    success, args = self.service([SourceCodeModelIndexerRequestId.RUN_ON_SINGLE_FILE, self.test_file.name, self.test_file.name])
        manager.assert_has_calls(
            [
                mock.call.mock_symbol_db_open(self.service.symbol_db_path),
                mock.call.mock_symbol_db_delete_entry(os.path.basename(self.test_file.name)),
                mock.call.mock_index_single_file(self.service.parser, self.service.root_directory, self.test_file.name, self.test_file.name, self.service.symbol_db)
            ]
        )
        self.assertEqual(success, False)
        self.assertEqual(args, None)

    def test_if_drop_single_file_deletes_an_entry_from_symbol_db(self):
        with mock.patch.object(self.service.symbol_db, 'delete') as mock_symbol_db_delete:
            success, args = self.service([SourceCodeModelIndexerRequestId.DROP_SINGLE_FILE, self.test_file.name])
        mock_symbol_db_delete.assert_called_once()
        self.assertEqual(success, True)
        self.assertEqual(args, None)

    def test_if_drop_all_deletes_all_entries_from_symbol_db_but_does_not_delete_the_db_from_disk(self):
        delete_from_disk = False
        with mock.patch.object(self.service.symbol_db, 'delete_all') as mock_symbol_db_delete_all:
            with mock.patch.object(self.service.symbol_db, 'close') as mock_symbol_db_close:
                with mock.patch('os.remove') as mock_os_remove:
                    success, args = self.service([SourceCodeModelIndexerRequestId.DROP_ALL, delete_from_disk])
        mock_symbol_db_delete_all.assert_called_once()
        mock_symbol_db_close.assert_not_called()
        mock_os_remove.assert_not_called()
        self.assertEqual(success, True)
        self.assertEqual(args, None)

    def test_if_drop_all_deletes_all_entries_from_symbol_db_and_deletes_the_db_from_disk(self):
        delete_from_disk = True
        with mock.patch.object(self.service.symbol_db, 'delete_all') as mock_symbol_db_delete_all:
            with mock.patch.object(self.service.symbol_db, 'close') as mock_symbol_db_close:
                with mock.patch('os.remove') as mock_os_remove:
                    success, args = self.service([SourceCodeModelIndexerRequestId.DROP_ALL, delete_from_disk])
        mock_symbol_db_delete_all.assert_called_once()
        mock_symbol_db_close.assert_called_once()
        mock_os_remove.assert_called_once_with(self.service.symbol_db.filename)
        self.assertEqual(success, True)
        self.assertEqual(args, None)

