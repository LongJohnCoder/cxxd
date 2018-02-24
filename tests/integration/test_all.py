import multiprocessing
import os
import shlex
import subprocess
import unittest

import cxxd.api
from cxxd.services.source_code_model.indexer.clang_indexer import SourceCodeModelIndexerRequestId
from cxxd.services.source_code_model_service import SourceCodeModelSubServiceId
import cxxd.server
import cxxd.tests.cxxd_mocks

wait_on_source_code_model_cb_semaphore = multiprocessing.Semaphore(0)

import ctypes
class TypeDeductionCallbackResult():
    TYPE_DEDUCTION_SPELLING_LENGTH_MAX = 50

    def __init__(self):
        self.type_deduction_status   = multiprocessing.Value(ctypes.c_bool, False)
        self.type_deduction_spelling = multiprocessing.Array(ctypes.c_char, TypeDeductionCallbackResult.TYPE_DEDUCTION_SPELLING_LENGTH_MAX)

    def set(self, success, args):
        self.type_deduction_status.value = success
        self.type_deduction_spelling.value = args[0:TypeDeductionCallbackResult.TYPE_DEDUCTION_SPELLING_LENGTH_MAX]

    def reset(self):
        self.set(False, '')

    @property
    def status(self):
        return self.type_deduction_status.value

    @property
    def spelling(self):
        return self.type_deduction_spelling.value


class GoToDefinitionCallbackResult():
    DEFINITION_FILENAME_LENGTH_MAX = 150

    def __init__(self):
        self.go_to_definition_status   = multiprocessing.Value(ctypes.c_bool, False)
        self.go_to_definition_filename = multiprocessing.Array(ctypes.c_char, GoToDefinitionCallbackResult.DEFINITION_FILENAME_LENGTH_MAX)
        self.go_to_definition_line     = multiprocessing.Value(ctypes.c_int, 0)
        self.go_to_definition_column   = multiprocessing.Value(ctypes.c_int, 0)

    def set(self, success, args):
        filename, line, column = args
        self.go_to_definition_status.value = success
        self.go_to_definition_filename.value = filename[0:GoToDefinitionCallbackResult.DEFINITION_FILENAME_LENGTH_MAX]
        self.go_to_definition_line.value = line
        self.go_to_definition_column.value = column

    def reset(self):
        self.set(False, ('', 0, 0,))

    @property
    def status(self):
        return self.go_to_definition_status.value

    @property
    def filename(self):
        return self.go_to_definition_filename.value

    @property
    def line(self):
        return self.go_to_definition_line.value

    @property
    def column(self):
        return self.go_to_definition_column.value

class GoToIncludeCallbackResult():
    INCLUDE_FILENAME_LENGTH_MAX = 150

    def __init__(self):
        self.go_to_include_status   = multiprocessing.Value(ctypes.c_bool, False)
        self.go_to_include_filename = multiprocessing.Array(ctypes.c_char, GoToIncludeCallbackResult.INCLUDE_FILENAME_LENGTH_MAX)

    def set(self, success, args):
        self.go_to_include_status.value = success
        self.go_to_include_filename.value = args[0:GoToIncludeCallbackResult.INCLUDE_FILENAME_LENGTH_MAX]

    def reset(self):
        self.set(False, '')

    @property
    def status(self):
        return self.go_to_include_status.value

    @property
    def filename(self):
        return self.go_to_include_filename.value

class SemanticSyntaxHighlightCallbackResult():
    TUNIT_FILENAME_LENGTH_MAX = 150

    def __init__(self):
        self.semantic_syntax_highlight_status           = multiprocessing.Value(ctypes.c_bool, False)
        self.semantic_syntax_highlight_tunit_spelling   = multiprocessing.Array(ctypes.c_char, SemanticSyntaxHighlightCallbackResult.TUNIT_FILENAME_LENGTH_MAX)
        self.semantic_syntax_highlight_num_of_ast_nodes = multiprocessing.Value(ctypes.c_int, 0)

    def set(self, success, args):
        def callback(ast_node_id, ast_node_name, ast_node_line, ast_node_column, ast_node_id_list):
            ast_node_id_list.append(ast_node_id)

        ast_node_id_list = []
        tunit, traverse = args
        traverse(tunit, callback, ast_node_id_list)
        self.semantic_syntax_highlight_status.value = success
        self.semantic_syntax_highlight_tunit_spelling.value = tunit.spelling[0:SemanticSyntaxHighlightCallbackResult.TUNIT_FILENAME_LENGTH_MAX]
        self.semantic_syntax_highlight_num_of_ast_nodes.value = len(ast_node_id_list)

    def reset(self):
        self.semantic_syntax_highlight_status.value = False
        self.semantic_syntax_highlight_tunit_spelling.value = ''
        self.semantic_syntax_highlight_num_of_ast_nodes.value = 0

    @property
    def status(self):
        return self.semantic_syntax_highlight_status.value

    @property
    def tunit_spelling(self):
        return self.semantic_syntax_highlight_tunit_spelling.value

    @property
    def num_of_ast_nodes(self):
        return self.semantic_syntax_highlight_num_of_ast_nodes.value

class DiagnosticsCallbackResult():
    def __init__(self):
        self.diagnostics_status = multiprocessing.Value(ctypes.c_bool, False)

    def set(self, success, args):
        self.diagnostics_status.value = success

    def reset(self):
        self.set(False, None)

    @property
    def status(self):
        return self.diagnostics_status.value

class IndexerCallbackResult():
    def __init__(self):
        self.indexer_status = multiprocessing.Value(ctypes.c_bool, False)
        self.indexer_num_of_references = multiprocessing.Value(ctypes.c_int, 0)

    def set(self, success, indexer_action_id, args):
        self.indexer_status.value = success
        if indexer_action_id == SourceCodeModelIndexerRequestId.RUN_ON_SINGLE_FILE:
            pass # Nothing to be checked upon
        elif indexer_action_id == SourceCodeModelIndexerRequestId.RUN_ON_DIRECTORY:
            pass # Nothing to be checked upon
        elif indexer_action_id == SourceCodeModelIndexerRequestId.DROP_SINGLE_FILE:
            pass # Nothing to be checked upon
        elif indexer_action_id == SourceCodeModelIndexerRequestId.DROP_ALL:
            pass # Nothing to be checked upon
        elif indexer_action_id == SourceCodeModelIndexerRequestId.FIND_ALL_REFERENCES:
            self.indexer_num_of_references.value = len(args)

    def reset(self):
        self.indexer_status.value = False
        self.indexer_num_of_references.value = 0

    @property
    def status(self):
        return self.indexer_status.value

    @property
    def num_of_references(self):
        return self.indexer_num_of_references.value

type_deduction_cb_result     = TypeDeductionCallbackResult()
go_to_definition_cb_result   = GoToDefinitionCallbackResult()
go_to_include_cb_result      = GoToIncludeCallbackResult()
semantic_syntax_hl_cb_result = SemanticSyntaxHighlightCallbackResult()
diagnostics_cb_result        = DiagnosticsCallbackResult()
indexer_cb_result            = IndexerCallbackResult()

class SourceCodeModelServicePluginMock():
    def startup_callback(self, success, payload):
        pass

    def shutdown_callback(self, success, payload):
        pass

    def __call__(self, success, payload, args):
        source_code_model_service_id = int(payload[0])
        if source_code_model_service_id == SourceCodeModelSubServiceId.INDEXER:
            indexer_cb_result.set(success, int(payload[1]), args)
        elif source_code_model_service_id == SourceCodeModelSubServiceId.SEMANTIC_SYNTAX_HIGHLIGHT:
            semantic_syntax_hl_cb_result.set(success, args)
        elif source_code_model_service_id == SourceCodeModelSubServiceId.DIAGNOSTICS:
            diagnostics_cb_result.set(success, args)
        elif source_code_model_service_id == SourceCodeModelSubServiceId.TYPE_DEDUCTION:
            type_deduction_cb_result.set(success, args)
        elif source_code_model_service_id == SourceCodeModelSubServiceId.GO_TO_DEFINITION:
            go_to_definition_cb_result.set(success, args)
        elif source_code_model_service_id == SourceCodeModelSubServiceId.GO_TO_INCLUDE:
            go_to_include_cb_result.set(success, args)
        else:
            logging.error('Invalid source code model service id!')
        wait_on_source_code_model_cb_semaphore.release()

class ClangFormatServicePluginMock():
    def startup_callback(self, success, payload):
        pass

    def shutdown_callback(self, success, payload):
        pass

    def __call__(self, success, payload, args):
        # TODO store result
        pass

class ClangTidyServicePluginMock():
    def startup_callback(self, success, payload):
        pass

    def shutdown_callback(self, success, payload):
        pass

    def __call__(self, success, payload, args):
        # TODO store result
        pass

class ProjectBuilderServicePluginMock():
    def startup_callback(self, success, payload):
        pass

    def shutdown_callback(self, success, payload):
        pass

    def __call__(self, success, payload, args):
        # TODO store result
        pass

def get_server_instance(handle, args):
    return cxxd.server.Server(
        handle,
        SourceCodeModelServicePluginMock(),
        ClangFormatServicePluginMock(),
        ClangTidyServicePluginMock(),
        ProjectBuilderServicePluginMock()
    )

current_dir = os.path.dirname(os.path.realpath(__file__))
ext_dep = {
    'chaiscript' : {
        'path' : current_dir + os.sep + 'external' + os.sep + 'ChaiScript',
    }
}

def gen_compile_commands_json(project_root_directory):
    cmd = 'cmake . -DCMAKE_EXPORT_COMPILE_COMMANDS=ON'
    return subprocess.call(shlex.split(cmd), cwd=project_root_directory)

class CxxdIntegrationTest(unittest.TestCase):
    DROP_SYMBOL_DB = True

    @classmethod
    def setUpClass(cls):
        # Setup some paths
        cls.proj_root_dir = ext_dep['chaiscript']['path']
        cls.compiler_args = cls.proj_root_dir + os.sep + 'compile_commands.json'
        cls.clang_format_config = cls.proj_root_dir + os.sep + 'clang-format'
        cls.log_file = current_dir + os.sep + 'cxxd.log'

        # Generate compile_commands.json
        gen_compile_commands_json(cls.proj_root_dir)

        # Trigger the cxxd server ...
        cls.handle = cxxd.api.server_start(get_server_instance, None, cls.log_file)
        cxxd.api.source_code_model_start(cls.handle, cls.proj_root_dir, cls.compiler_args)
        cxxd.api.project_builder_start(cls.handle, cls.proj_root_dir)
        cxxd.api.clang_format_start(cls.handle, cls.clang_format_config)
        cxxd.api.clang_tidy_start(cls.handle, cls.compiler_args)

        # Run the indexer ... Wait until it completes.
        cxxd.api.source_code_model_indexer_run_on_directory_request(cls.handle)
        wait_on_source_code_model_cb_semaphore.acquire()
        assert indexer_cb_result.status == True # can't use unittest asserts here ...

    @classmethod
    def tearDownClass(cls):
        if CxxdIntegrationTest.DROP_SYMBOL_DB:
            cxxd.api.source_code_model_indexer_drop_all_request(cls.handle, remove_db_from_disk=True)
            wait_on_source_code_model_cb_semaphore.acquire()
            assert indexer_cb_result.status == True # can't use unittest asserts here ...
        cxxd.api.server_stop(cls.handle)
        os.remove(cls.log_file)

    def setUp(self):
        type_deduction_cb_result.reset()
        go_to_include_cb_result.reset()
        go_to_definition_cb_result.reset()
        semantic_syntax_hl_cb_result.reset()
        diagnostics_cb_result.reset()
        indexer_cb_result.reset()

    def tearDown(self):
        pass

    def test_source_code_model_indexer_run_on_directory(self):
        cxxd.api.source_code_model_indexer_run_on_directory_request(self.handle)
        wait_on_source_code_model_cb_semaphore.acquire()
        self.assertTrue(indexer_cb_result.status)

    def test_source_code_model_indexer_drop_single_file(self):
        fut = ext_dep['chaiscript']['path'] + os.sep + 'include' + os.sep + 'chaiscript' + os.sep + 'chaiscript.hpp'
        cxxd.api.source_code_model_indexer_drop_single_file_request(self.handle, fut)
        wait_on_source_code_model_cb_semaphore.acquire()
        self.assertTrue(indexer_cb_result.status)

    def test_source_code_model_indexer_run_on_single_file(self):
        fut = ext_dep['chaiscript']['path'] + os.sep + 'include' + os.sep + 'chaiscript' + os.sep + 'chaiscript.hpp'
        cxxd.api.source_code_model_indexer_run_on_single_file_request(self.handle, fut, fut)
        wait_on_source_code_model_cb_semaphore.acquire()
        self.assertTrue(indexer_cb_result.status)

    def test_source_code_model_indexer_find_all_references_request(self):
        fut = ext_dep['chaiscript']['path'] + os.sep + 'include' + os.sep + 'chaiscript' + os.sep + 'chaiscript.hpp'
        cxxd.api.source_code_model_indexer_find_all_references_request(self.handle, fut, 830, 9)
        wait_on_source_code_model_cb_semaphore.acquire()
        self.assertTrue(indexer_cb_result.status)
        self.assertNotEqual(indexer_cb_result.num_of_references, 0)

    def test_source_code_model_go_to_definition_request(self):
        fut = ext_dep['chaiscript']['path'] + os.sep + 'include' + os.sep + 'chaiscript' + os.sep + 'chaiscript.hpp'
        cxxd.api.source_code_model_go_to_definition_request(self.handle, fut, fut, 830, 29)
        wait_on_source_code_model_cb_semaphore.acquire()
        self.assertTrue(go_to_definition_cb_result.status)
        self.assertNotEqual(go_to_definition_cb_result.filename, '')
        self.assertNotEqual(go_to_definition_cb_result.line, 0)
        self.assertNotEqual(go_to_definition_cb_result.column, 0)

    def test_source_code_model_go_to_definition_on_fwd_declared_symbol_request(self):
        fut = ext_dep['chaiscript']['path'] + os.sep + 'include' + os.sep + 'chaiscript' + os.sep + 'dispatchkit' + os.sep + 'dispatchkit.hpp'
        cxxd.api.source_code_model_go_to_definition_request(self.handle, fut, fut, 49, 7)
        wait_on_source_code_model_cb_semaphore.acquire()
        self.assertTrue(go_to_definition_cb_result.status)
        self.assertNotEqual(go_to_definition_cb_result.filename, '')
        self.assertNotEqual(go_to_definition_cb_result.line, 0)
        self.assertNotEqual(go_to_definition_cb_result.column, 0)

    def test_source_code_model_go_to_include_request(self):
        fut = ext_dep['chaiscript']['path'] + os.sep + 'include' + os.sep + 'chaiscript' + os.sep + 'chaiscript.hpp'
        cxxd.api.source_code_model_go_to_include_request(self.handle, fut, fut, 824)
        wait_on_source_code_model_cb_semaphore.acquire()
        self.assertTrue(go_to_include_cb_result.status)
        self.assertNotEqual(go_to_include_cb_result.filename, '')

    def test_source_code_model_type_deduction_request(self):
        fut = ext_dep['chaiscript']['path'] + os.sep + 'include' + os.sep + 'chaiscript' + os.sep + 'chaiscript.hpp'
        cxxd.api.source_code_model_type_deduction_request(self.handle, fut, fut, 838, 67)
        wait_on_source_code_model_cb_semaphore.acquire()
        self.assertTrue(type_deduction_cb_result.status)
        self.assertNotEqual(type_deduction_cb_result.spelling, '')

    def test_source_code_model_semantic_syntax_highlight_request(self):
        fut = ext_dep['chaiscript']['path'] + os.sep + 'include' + os.sep + 'chaiscript' + os.sep + 'chaiscript.hpp'
        cxxd.api.source_code_model_semantic_syntax_highlight_request(self.handle, fut, fut)
        wait_on_source_code_model_cb_semaphore.acquire()
        self.assertTrue(semantic_syntax_hl_cb_result.status)
        self.assertNotEqual(semantic_syntax_hl_cb_result.tunit_spelling, '')
        self.assertNotEqual(semantic_syntax_hl_cb_result.num_of_ast_nodes, 0)

    def test_source_code_model_diagnostics_request(self):
        fut = ext_dep['chaiscript']['path'] + os.sep + 'include' + os.sep + 'chaiscript' + os.sep + 'chaiscript.hpp'
        cxxd.api.source_code_model_diagnostics_request(self.handle, fut, fut)
        wait_on_source_code_model_cb_semaphore.acquire()
        self.assertTrue(diagnostics_cb_result.status)

if __name__ == "__main__":
    import argparse, sys
    parser = argparse.ArgumentParser()
    parser.add_argument('--do_not_drop_symbol_db', action='store_true',\
        help='Use if you want to instruct the CxxdIntegrationTest not to drop the symbol database after it has\
        run all of the tests. Dropping the database after each run will slow down the develop-test-debug cycle\
        as indexing operation takes a quite some time. Hence, this flag''s purpose is to override such behavior.'
    )
    parser.add_argument('unittest_args', nargs='*')

    args = parser.parse_args()

    # Forward unittest module arguments
    sys.argv[1:] = args.unittest_args

    CxxdIntegrationTest.DROP_SYMBOL_DB = not args.do_not_drop_symbol_db

    unittest.main()
