import multiprocessing
import os
import shlex
import subprocess
import unittest

import cxxd.api
from cxxd.services.source_code_model_service import SourceCodeModelSubServiceId
import cxxd.server
import cxxd.tests.cxxd_mocks

wait_on_source_code_model_cb_semaphore = multiprocessing.Semaphore(0)

class SourceCodeModelServicePluginMock():
    def startup_callback(self, success, payload):
        pass

    def shutdown_callback(self, success, payload):
        pass

    def __call__(self, success, payload, args):
        source_code_model_service_id = int(payload[0])
        wait_on_source_code_model_cb_semaphore.release()

        # TODO let's assert if it doesn't happen what we expected

        #if source_code_model_service_id == SourceCodeModelSubServiceId.INDEXER:
        #elif source_code_model_service_id == SourceCodeModelSubServiceId.SEMANTIC_SYNTAX_HIGHLIGHT:
        #    self.semantic_syntax_higlight(success, payload, args)
        #elif source_code_model_service_id == SourceCodeModelSubServiceId.DIAGNOSTICS:
        #    self.diagnostics(success, payload, args)
        #elif source_code_model_service_id == SourceCodeModelSubServiceId.TYPE_DEDUCTION:
        #    self.type_deduction(success, payload, args)
        #elif source_code_model_service_id == SourceCodeModelSubServiceId.GO_TO_DEFINITION:
        #    self.go_to_definition(success, payload, args)
        #elif source_code_model_service_id == SourceCodeModelSubServiceId.GO_TO_INCLUDE:
        #    self.go_to_include(success, payload, args)
        #else:
        #    logging.error('Invalid source code model service id!')

class ClangFormatServicePluginMock():
    def startup_callback(self, success, payload):
        pass

    def shutdown_callback(self, success, payload):
        pass

    def __call__(self, success, payload, args):
        pass

class ClangTidyServicePluginMock():
    def startup_callback(self, success, payload):
        pass

    def shutdown_callback(self, success, payload):
        pass

    def __call__(self, success, payload, args):
        pass

class ProjectBuilderServicePluginMock():
    def startup_callback(self, success, payload):
        pass

    def shutdown_callback(self, success, payload):
        pass

    def __call__(self, success, payload, args):
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

    @classmethod
    def tearDownClass(cls):
        if CxxdIntegrationTest.DROP_SYMBOL_DB:
            cxxd.api.source_code_model_indexer_drop_all_request(cls.handle, remove_db_from_disk=True)
            wait_on_source_code_model_cb_semaphore.acquire()
        cxxd.api.server_stop(cls.handle)
        os.remove(cls.log_file)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_source_code_model_indexer_run_on_directory(self):
        cxxd.api.source_code_model_indexer_run_on_directory_request(self.handle)
        wait_on_source_code_model_cb_semaphore.acquire()

    def test_source_code_model_indexer_drop_single_file(self):
        fut = ext_dep['chaiscript']['path'] + os.sep + 'include' + os.sep + 'chaiscript' + os.sep + 'chaiscript.hpp'
        cxxd.api.source_code_model_indexer_drop_single_file_request(self.handle, fut)
        wait_on_source_code_model_cb_semaphore.acquire()

    def test_source_code_model_indexer_run_on_single_file(self):
        fut = ext_dep['chaiscript']['path'] + os.sep + 'include' + os.sep + 'chaiscript' + os.sep + 'chaiscript.hpp'
        cxxd.api.source_code_model_indexer_run_on_single_file_request(self.handle, fut, fut)
        wait_on_source_code_model_cb_semaphore.acquire()

    def test_source_code_model_indexer_find_all_references_request(self):
        fut = ext_dep['chaiscript']['path'] + os.sep + 'include' + os.sep + 'chaiscript' + os.sep + 'chaiscript.hpp'
        cxxd.api.source_code_model_indexer_find_all_references_request(self.handle, fut, 830, 9)
        wait_on_source_code_model_cb_semaphore.acquire()

    def test_source_code_model_go_to_definition_request(self):
        fut = ext_dep['chaiscript']['path'] + os.sep + 'include' + os.sep + 'chaiscript' + os.sep + 'chaiscript.hpp'
        cxxd.api.source_code_model_go_to_definition_request(self.handle, fut, fut, 830, 29)
        wait_on_source_code_model_cb_semaphore.acquire()

    def test_source_code_model_go_to_definition_on_fwd_declared_symbol_request(self):
        fut = ext_dep['chaiscript']['path'] + os.sep + 'include' + os.sep + 'chaiscript' + os.sep + 'dispatchkit' + os.sep + 'dispatchkit.hpp'
        cxxd.api.source_code_model_go_to_definition_request(self.handle, fut, fut, 49, 7)
        wait_on_source_code_model_cb_semaphore.acquire()

    def test_source_code_model_go_to_include_request(self):
        fut = ext_dep['chaiscript']['path'] + os.sep + 'include' + os.sep + 'chaiscript' + os.sep + 'chaiscript.hpp'
        cxxd.api.source_code_model_go_to_include_request(self.handle, fut, fut, 824)
        wait_on_source_code_model_cb_semaphore.acquire()

    def test_source_code_model_type_deduction_request(self):
        fut = ext_dep['chaiscript']['path'] + os.sep + 'include' + os.sep + 'chaiscript' + os.sep + 'chaiscript.hpp'
        cxxd.api.source_code_model_type_deduction_request(self.handle, fut, fut, 177, 42)
        wait_on_source_code_model_cb_semaphore.acquire()

    #def test_source_code_model_indexer_
    #def test_source_code_model_indexer_

if __name__ == "__main__":
    import argparse, sys
    parser = argparse.ArgumentParser()
    parser.add_argument('--do_not_drop_symbol_db', action='store_true',\
        help='Use if you want to instruct the CxxdIntegrationTest not to drop the symbol database after it has\
        run all of the tests. Dropping the database after each run will slow you down during the develop-test-debug cycle\
        as indexing operation takes a quite some time. Hence, this is the flag to override such behavior.'
    )
    parser.add_argument('unittest_args', nargs='*')

    args = parser.parse_args()

    # Forward unittest module arguments
    sys.argv[1:] = args.unittest_args

    CxxdIntegrationTest.DROP_SYMBOL_DB = not args.do_not_drop_symbol_db

    unittest.main()
