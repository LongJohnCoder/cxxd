from server import ServiceId
from server import ServerRequestId
from services.source_code_model_service import SourceCodeModelSubServiceId
from services.source_code_model.indexer.clang_indexer import SourceCodeModelIndexerRequestId

#
# Server API
#
def start_server(get_server_instance, get_server_instance_args, log_file):
    import logging
    import multiprocessing
    import sys

    def __run_impl(handle, get_server_instance, args, log_file):
        def __handle_exception(exc_type, exc_value, exc_traceback):
            logging.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

        def __catch_unhandled_exceptions():
            # This is what usually should be enough
            sys.excepthook = __handle_exception

            # But sys.excepthook does not work anymore within multi-threaded/multi-process environment (see https://bugs.python.org/issue1230540)
            # So what we can do is to override the Service.listen() implementation so it includes try-catch block with exceptions
            # being forwarded to the sys.excepthook function.
            from service import Service
            run_original = Service.listen
            def listen(self):
                try:
                    run_original(self)
                except:
                    sys.excepthook(*sys.exc_info())
            Service.listen = listen

        # Logger setup
        FORMAT = '[%(levelname)s] [%(filename)s:%(lineno)s] %(funcName)25s(): %(message)s'
        logging.basicConfig(filename=log_file, filemode='w', format=FORMAT, level=logging.INFO)
        logging.info('Starting a server ...')

        # Setup catching unhandled exceptions
        __catch_unhandled_exceptions()

        # Instantiate and run the server
        try:
            get_server_instance(handle, args).listen()
        except:
            sys.excepthook(*sys.exc_info())

    server_queue = multiprocessing.Queue()
    server_process = multiprocessing.Process(
        target=__run_impl,
        args=(
            server_queue,
            get_server_instance,
            get_server_instance_args,
            log_file
        ),
        name="cxxd_server"
    )
    server_process.daemon = False
    server_process.start()
    return server_queue

def stop_server(handle, *payload):
    handle.put([ServerRequestId.SHUTDOWN_AND_EXIT, 0x0, list(payload)])

def start_all_services(handle, *payload):
    handle.put([ServerRequestId.START_ALL_SERVICES, 0x0, list(payload)])

def stop_all_services(handle, *payload):
    handle.put([ServerRequestId.SHUTDOWN_ALL_SERVICES, 0x0, list(payload)])

def start_service(handle, id, *payload):
    handle.put([ServerRequestId.START_SERVICE, id, list(payload)])

def stop_service(handle, id, *payload):
    handle.put([ServerRequestId.SHUTDOWN_SERVICE, id, list(payload)])

def request_service(handle, id, *payload):
    handle.put([ServerRequestId.SEND_SERVICE, id, list(payload)])

#
# Source code model API
#
def source_code_model_start(handle, project_root_directory, compiler_args):
    start_service(handle, ServiceId.SOURCE_CODE_MODEL, project_root_directory, compiler_args)

def source_code_model_stop(handle, subscribe_for_callback):
    stop_service(handle, ServiceId.SOURCE_CODE_MODEL, subscribe_for_callback)

def source_code_model_request(handle, source_code_model_service_id, *source_code_model_service_args):
    request_service(handle, ServiceId.SOURCE_CODE_MODEL, source_code_model_service_id, *source_code_model_service_args)

#
# Source code model services API
#
def indexer_request(handle, indexer_action_id, *args):
    source_code_model_request(handle, SourceCodeModelSubServiceId.INDEXER, indexer_action_id, *args)

def semantic_syntax_highlight_request(handle, filename, contents):
    source_code_model_request(handle, SourceCodeModelSubServiceId.SEMANTIC_SYNTAX_HIGHLIGHT, filename, contents)

def diagnostics_request(handle, filename, contents):
    source_code_model_request(handle, SourceCodeModelSubServiceId.DIAGNOSTICS, filename, contents)

def type_deduction_request(handle, filename, contents, line, col):
    source_code_model_request(handle, SourceCodeModelSubServiceId.TYPE_DEDUCTION, filename, contents, line, col)

def go_to_definition_request(handle, filename, contents, line, col):
    source_code_model_request(handle, SourceCodeModelSubServiceId.GO_TO_DEFINITION, filename, contents, line, col)

def go_to_include_request(handle, filename, contents, line):
    source_code_model_request(handle, SourceCodeModelSubServiceId.GO_TO_INCLUDE, filename, contents, line)

def indexer_run_on_single_file_request(handle, filename, contents):
    indexer_request(handle, SourceCodeModelIndexerRequestId.RUN_ON_SINGLE_FILE, filename, contents)

def indexer_run_on_directory_request(handle):
    indexer_request(handle, SourceCodeModelIndexerRequestId.RUN_ON_DIRECTORY)

def indexer_drop_single_file_request(handle, filename):
    indexer_request(handle, SourceCodeModelIndexerRequestId.DROP_SINGLE_FILE, filename)

def indexer_drop_all_request(handle, remove_db_from_disk):
    indexer_request(handle, SourceCodeModelIndexerRequestId.DROP_ALL, remove_db_from_disk)

def indexer_drop_all_and_run_on_directory_request(handle):
    indexer_drop_all_request(handle, True)
    indexer_run_on_directory_request(handle)

def indexer_find_all_references_request(handle, filename, line, col):
    indexer_request(handle, SourceCodeModelIndexerRequestId.FIND_ALL_REFERENCES, filename, line, col)



#
# Project builder service API
#
def project_builder_start(handle, project_root_directory):
    start_service(handle, ServiceId.PROJECT_BUILDER, project_root_directory)

def project_builder_stop(handle, subscribe_for_callback):
    stop_service(handle, ServiceId.PROJECT_BUILDER, subscribe_for_callback)

def project_builder_request(handle, build_command):
    request_service(handle, ServiceId.PROJECT_BUILDER, build_command)

#
# Clang-format service API
#
def clang_format_start(handle, config_file):
    start_service(handle, ServiceId.CLANG_FORMAT, config_file)

def clang_format_stop(handle, subscribe_for_callback):
    stop_service(handle, ServiceId.CLANG_FORMAT, subscribe_for_callback)

def clang_format_request(handle, filename):
    request_service(handle, ServiceId.CLANG_FORMAT, filename)

#
# Clang-tidy service API
#
def clang_tidy_start(handle, config_file, json_compilation_database):
    start_service(handle, ServiceId.CLANG_TIDY, config_file, json_compilation_database)

def clang_tidy_stop(handle, subscribe_for_callback):
    stop_service(handle, ServiceId.CLANG_TIDY, subscribe_for_callback)

def clang_tidy_request(handle, filename, apply_fixes):
    request_service(handle, ServiceId.CLANG_TIDY, filename, apply_fixes)

