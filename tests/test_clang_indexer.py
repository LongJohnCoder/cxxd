import mock
import os
import sqlite3
import unittest

import parser.ast_node_identifier
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
        self.unsupported_ast_node_ids = [
            parser.ast_node_identifier.ASTNodeId.getNamespaceId(),
            parser.ast_node_identifier.ASTNodeId.getTemplateTypeParameterId(),
            parser.ast_node_identifier.ASTNodeId.getTemplateNonTypeParameterId(),
            parser.ast_node_identifier.ASTNodeId.getTemplateTemplateParameterId(),
            parser.ast_node_identifier.ASTNodeId.getNamespaceAliasId(),
            parser.ast_node_identifier.ASTNodeId.getUsingDirectiveId(),
            parser.ast_node_identifier.ASTNodeId.getUnsupportedId(),
        ]
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

    def test_if_run_on_directory_skips_indexing_if_symbol_db_already_exists_in_root_directory(self):
        with mock.patch('os.path.exists', return_value=True) as mock_os_path_exists:
            with mock.patch.object(self.service.symbol_db, 'open') as mock_symbol_db_open:
                with mock.patch.object(self.service.symbol_db, 'create_data_model') as mock_symbol_db_create_data_model:
                    success, args = self.service([SourceCodeModelIndexerRequestId.RUN_ON_DIRECTORY])
        mock_symbol_db_open.assert_called_once()
        mock_symbol_db_create_data_model.assert_not_called()
        self.assertEqual(success, True)
        self.assertEqual(args, None)

    def not_test_if_run_on_directory_does_not_skip_indexing_if_symbol_db_does_not_exist_in_root_directory(self):
        # TODO redundant?
        with mock.patch('os.path.exists', return_value=False) as mock_os_path_exists:
            with mock.patch.object(self.service.symbol_db, 'open') as mock_symbol_db_open:
                with mock.patch.object(self.service.symbol_db, 'create_data_model') as mock_symbol_db_create_data_model:
                    success, args = self.service([SourceCodeModelIndexerRequestId.RUN_ON_DIRECTORY])
        mock_symbol_db_open.assert_called_once()
        mock_symbol_db_create_data_model.assert_called_once()
        self.assertEqual(success, True)
        self.assertEqual(args, None)

    def test_if_run_on_directory_handles_when_there_are_no_files_existing_in_root_directory(self):
        with mock.patch('os.path.exists', return_value=False) as mock_os_path_exists:
            with mock.patch.object(self.service.symbol_db, 'open') as mock_symbol_db_open:
                with mock.patch.object(self.service.symbol_db, 'create_data_model') as mock_symbol_db_create_data_model:
                    with mock.patch('services.source_code_model.indexer.clang_indexer.get_cpp_file_list', return_value=[]) as mock_get_cpp_file_list:
                        success, args = self.service([SourceCodeModelIndexerRequestId.RUN_ON_DIRECTORY])
        mock_symbol_db_open.assert_called_once()
        mock_symbol_db_create_data_model.assert_called_once()
        mock_get_cpp_file_list.assert_called_once_with(self.service.root_directory)
        self.assertEqual(success, True)
        self.assertEqual(args, None)

    def test_if_run_on_directory_handles_when_cpp_file_chunk_list_contains_none_items(self):
        import multiprocessing, logging, subprocess
        logging.getLoggerClass().root.handlers[0].baseFilename = 'something'
        dummy_cmd = 'cd'
        cpp_file_list = ['/tmp/a.cpp', '/tmp/b.cpp', '/tmp/c.cpp', '/tmp/d.cpp', '/tmp/e.cpp', '/tmp/f.cpp', '/tmp/g.cpp']
        cpp_file_list_chunks = [cpp_file_list[0:1], cpp_file_list[2:3], cpp_file_list[4:5], [cpp_file_list[6], None]]
        with mock.patch('os.path.exists', return_value=False) as mock_os_path_exists:
            with mock.patch.object(self.service.symbol_db, 'open') as mock_symbol_db_open:
                with mock.patch.object(self.service.symbol_db, 'create_data_model') as mock_symbol_db_create_data_model:
                    with mock.patch('services.source_code_model.indexer.clang_indexer.get_cpp_file_list', return_value=cpp_file_list) as mock_get_cpp_file_list:
                        with mock.patch('services.source_code_model.indexer.clang_indexer.slice_it', return_value=cpp_file_list_chunks) as mock_slice_it, \
                            mock.patch('services.source_code_model.indexer.clang_indexer.create_indexer_input_list_file', return_value=(None, 'indexer_input_list_file',)) as mock_create_indexer_input_list_file, \
                            mock.patch('services.source_code_model.indexer.clang_indexer.create_empty_symbol_db', return_value=(None, 'empty_symbol_db_filename',)) as mock_create_empty_symbol_db, \
                            mock.patch('services.source_code_model.indexer.clang_indexer.start_indexing_subprocess', return_value=subprocess.Popen(dummy_cmd)) as mock_start_indexing_subprocess, \
                            mock.patch('subprocess.Popen.wait') as mock_subprocess_wait, \
                            mock.patch('services.source_code_model.indexer.clang_indexer.SymbolDatabase.insert_from'), \
                            mock.patch('os.remove') as mock_os_remove:
                            success, args = self.service([SourceCodeModelIndexerRequestId.RUN_ON_DIRECTORY])
        mock_symbol_db_open.assert_called_once()
        mock_symbol_db_create_data_model.assert_called_once()
        mock_get_cpp_file_list.assert_called_once_with(self.service.root_directory)
        mock_slice_it.assert_called_once_with(cpp_file_list, len(cpp_file_list)/multiprocessing.cpu_count())
        mock_create_empty_symbol_db.assert_called_with(self.service.root_directory, self.service.symbol_db_name)
        self.assertEqual(mock_create_indexer_input_list_file.call_count, len(cpp_file_list_chunks))
        self.assertEqual(mock_create_empty_symbol_db.call_count, len(cpp_file_list_chunks))
        self.assertEqual(mock_start_indexing_subprocess.call_count, len(cpp_file_list_chunks))
        self.assertEqual(mock_os_remove.call_count, 2*len(cpp_file_list_chunks))
        self.assertEqual(mock_subprocess_wait.call_count, len(cpp_file_list_chunks))
        self.assertEqual(success, True)
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

    def test_if_find_all_references_returns_false_and_empty_references_list_for_invalid_translation_unit(self):
        with mock.patch.object(self.service.parser, 'parse', return_value=None) as mock_parser_parse:
            success, references = self.service([SourceCodeModelIndexerRequestId.FIND_ALL_REFERENCES, self.test_file.name, 1, 1])
        self.assertEqual(success, False)
        self.assertEqual(len(references), 0)

    def test_if_find_all_references_returns_true_and_empty_references_list_for_invalid_cursor(self):
        with mock.patch.object(self.service.parser, 'parse') as mock_parser_parse:
            with mock.patch.object(self.service.parser, 'get_cursor', return_value=None) as mock_parser_get_cursor:
                success, references = self.service([SourceCodeModelIndexerRequestId.FIND_ALL_REFERENCES, self.test_file.name, 1, 1])
        self.assertEqual(success, True)
        self.assertEqual(len(references), 0)

    def test_if_find_all_references_returns_true_and_empty_references_list_when_run_on_unsupported_ast_node_ids(self):
        with mock.patch.object(self.service.parser, 'parse') as mock_parser_parse:
            with mock.patch.object(self.service.parser, 'get_cursor') as mock_parser_get_cursor:
                for ast_node_identifier in self.unsupported_ast_node_ids:
                    with mock.patch.object(self.service.parser, 'get_ast_node_id', return_value=ast_node_identifier) as mock_parser_get_ast_node_id:
                        success, references = self.service([SourceCodeModelIndexerRequestId.FIND_ALL_REFERENCES, self.test_file.name, 1, 1])
        self.assertEqual(success, True)
        self.assertEqual(len(references), 0)

    def test_if_find_all_references_returns_true_and_empty_references_list_when_run_on_symbol_which_does_not_have_any_occurence_in_symbol_db(self):
        cursor = mock.MagicMock(sqlite3.Cursor)
        cursor.fetchall.return_value = []
        with mock.patch.object(self.service.parser, 'parse') as mock_parser_parse:
            with mock.patch.object(self.service.parser, 'get_cursor') as mock_parser_get_cursor:
                with mock.patch.object(self.service.parser, 'get_ast_node_id', return_value=self.service.supported_ast_node_ids[0]) as mock_parser_get_ast_node_id:
                    with mock.patch.object(self.service.symbol_db, 'get_by_id', return_value=cursor) as mock_symbol_db_get_by_id:
                        success, references = self.service([SourceCodeModelIndexerRequestId.FIND_ALL_REFERENCES, self.test_file.name, 1, 1])
        self.assertEqual(success, True)
        self.assertEqual(len(references), 0)

    def test_if_find_all_references_returns_true_and_non_empty_references_list_when_run_on_symbol_which_has_occurences_in_symbol_db(self):
        cursor = mock.MagicMock(sqlite3.Cursor)
        cursor.fetchall.return_value = [['main.cpp', '22', '5', 'main.cpp#l22#c5#foobar', '    void foobar() {']]
        with mock.patch.object(self.service.parser, 'parse') as mock_parser_parse:
            with mock.patch.object(self.service.parser, 'get_cursor') as mock_parser_get_cursor:
                with mock.patch.object(self.service.parser, 'get_ast_node_id', return_value=self.service.supported_ast_node_ids[0]) as mock_parser_get_ast_node_id:
                    with mock.patch.object(self.service.symbol_db, 'get_by_id', return_value=cursor) as mock_symbol_db_get_by_id:
                        success, references = self.service([SourceCodeModelIndexerRequestId.FIND_ALL_REFERENCES, self.test_file.name, 1, 1])
        self.assertEqual(success, True)
        self.assertNotEqual(len(references), 0)

    def test_if_find_all_references_returns_true_and_in_non_empty_references_filename_columns_are_prepended_with_root_directory(self):
        cursor = mock.MagicMock(sqlite3.Cursor)
        cursor.fetchall.return_value = [['main.cpp', '22', '5', 'main.cpp#l22#c5#foobar', '    void foobar() {']]
        with mock.patch.object(self.service.parser, 'parse') as mock_parser_parse:
            with mock.patch.object(self.service.parser, 'get_cursor') as mock_parser_get_cursor:
                with mock.patch.object(self.service.parser, 'get_ast_node_id', return_value=self.service.supported_ast_node_ids[0]) as mock_parser_get_ast_node_id:
                    with mock.patch.object(self.service.symbol_db, 'get_by_id', return_value=cursor) as mock_symbol_db_get_by_id:
                        success, references = self.service([SourceCodeModelIndexerRequestId.FIND_ALL_REFERENCES, self.test_file.name, 1, 1])
        self.assertEqual(success, True)
        self.assertNotEqual(len(references), 0)
        filename = references[0][0]
        self.assertEqual(filename.startswith(self.root_directory), True)

    def test_if_index_file_list_runs_indexer_for_given_set_of_args(self):
        from services.source_code_model.indexer.clang_indexer import index_file_list
        from parser.tunit_cache import NoCache
        root_directory = os.path.dirname(self.test_file.name)
        input_filename_list = ['/tmp/a.cpp', '/tmp/b.cpp', '/tmp/c.cpp', '/tmp/d.cpp', '/tmp/e.cpp', '/tmp/f.cpp', '/tmp/g.cpp']
        compiler_args_filename = 'compiler_args.json'
        output_db_filename = 'out.db'
        manager = mock.MagicMock()
        with mock.patch('services.source_code_model.indexer.clang_indexer.SymbolDatabase.__init__', return_value=None) as mock_symbol_db_creation, \
            mock.patch('services.source_code_model.indexer.clang_indexer.SymbolDatabase.__del__', return_value=None) as mock_symbol_db_deletion, \
            mock.patch('services.source_code_model.indexer.clang_indexer.SymbolDatabase.create_data_model') as mock_symbol_db_create_data_model, \
            mock.patch('services.source_code_model.indexer.clang_indexer.ClangParser.__init__', return_value=None) as mock_clang_parser_creation, \
            mock.patch('services.source_code_model.indexer.clang_indexer.TranslationUnitCache') as mock_translation_unit_cache, \
            mock.patch('services.source_code_model.indexer.clang_indexer.NoCache') as mock_translation_unit_no_cache_strategy, \
            mock.patch('services.source_code_model.indexer.clang_indexer.index_single_file') as mock_index_single_file, \
            mock.patch('__builtin__.open', mock.mock_open(read_data='\n'.join(input_filename_list)), create=True), \
            mock.patch('services.source_code_model.indexer.clang_indexer.SymbolDatabase.close') as mock_symbol_db_close:
                manager.attach_mock(mock_index_single_file, 'mock_index_single_file')
                index_file_list(root_directory, 'dummy_input_file', compiler_args_filename, output_db_filename)
        mock_symbol_db_creation.assert_called_once_with(output_db_filename)
        mock_symbol_db_create_data_model.assert_called_once()
        mock_clang_parser_creation.assert_called_once_with(compiler_args_filename, mock.ANY) #NoCache())
        mock_translation_unit_cache.assert_called_once()
        mock_translation_unit_no_cache_strategy.assert_called_once()
        self.assertEqual(mock_index_single_file.call_count, len(input_filename_list))
        manager.assert_has_calls(
            [
                mock.call.mock_index_single_file(
                    mock.ANY, root_directory,
                    input_filename_list[0], input_filename_list[0], mock.ANY
                ),
                mock.call.mock_index_single_file(
                    mock.ANY, root_directory,
                    input_filename_list[1], input_filename_list[1], mock.ANY
                ),
                mock.call.mock_index_single_file(
                    mock.ANY, root_directory,
                    input_filename_list[2], input_filename_list[2], mock.ANY
                ),
                mock.call.mock_index_single_file(
                    mock.ANY, root_directory,
                    input_filename_list[3], input_filename_list[3], mock.ANY
                ),
                mock.call.mock_index_single_file(
                    mock.ANY, root_directory,
                    input_filename_list[4], input_filename_list[4], mock.ANY
                ),
                mock.call.mock_index_single_file(
                    mock.ANY, root_directory,
                    input_filename_list[5], input_filename_list[5], mock.ANY
                ),
                mock.call.mock_index_single_file(
                    mock.ANY, root_directory,
                    input_filename_list[6], input_filename_list[6], mock.ANY
                )
            ]
        )
        mock_symbol_db_close.assert_called_once()

    def test_if_index_single_file_parses_traverses_and_flushes_the_symbol_db(self):
        from services.source_code_model.indexer.clang_indexer import index_single_file
        from services.source_code_model.indexer.clang_indexer import indexer_visitor
        from services.source_code_model.indexer.symbol_database import SymbolDatabase
        symbol_db = SymbolDatabase('tmp.db')
        with mock.patch.object(self.parser, 'parse') as mock_parser_parse:
            with mock.patch.object(self.parser, 'traverse') as mock_parser_traverse:
                with mock.patch('services.source_code_model.indexer.clang_indexer.SymbolDatabase.flush') as mock_symbol_db_flush:
                    index_single_file(self.parser, os.path.dirname(self.test_file.name), self.test_file.name, self.test_file.name, symbol_db)
        mock_parser_parse.assert_called_once_with(self.test_file.name, self.test_file.name)
        mock_parser_traverse.assert_called_once_with(mock.ANY, mock.ANY, indexer_visitor)
        mock_symbol_db_flush.assert_called_once()

    def test_if_get_clang_index_path_returns_a_valid_path(self):
        from services.source_code_model.indexer.clang_indexer import get_clang_index_path
        self.assertTrue(os.path.exists(get_clang_index_path()))
