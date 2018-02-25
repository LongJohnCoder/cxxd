import ctypes
import multiprocessing

from cxxd.services.source_code_model_service import SourceCodeModelSubServiceId

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
        from cxxd.services.source_code_model.indexer.clang_indexer import SourceCodeModelIndexerRequestId
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

class SourceCodeModelCallbackResult():
    def __init__(self):
        self.type = {
            'type_deduction'     : TypeDeductionCallbackResult(),
            'go_to_definition'   : GoToDefinitionCallbackResult(),
            'go_to_include'      : GoToIncludeCallbackResult(),
            'semantic_syntax_hl' : SemanticSyntaxHighlightCallbackResult(),
            'diagnostics'        : DiagnosticsCallbackResult(),
            'indexer'            : IndexerCallbackResult()
        }
        self.wait_on_completion = multiprocessing.Semaphore(0)

    def wait_until_available(self):
        self.wait_on_completion.acquire()

    def set(self, success, payload, args):
        source_code_model_service_id = int(payload[0])
        if source_code_model_service_id == SourceCodeModelSubServiceId.INDEXER:
            self.type['indexer'].set(success, int(payload[1]), args)
        elif source_code_model_service_id == SourceCodeModelSubServiceId.SEMANTIC_SYNTAX_HIGHLIGHT:
            self.type['semantic_syntax_hl'].set(success, args)
        elif source_code_model_service_id == SourceCodeModelSubServiceId.DIAGNOSTICS:
            self.type['diagnostics'].set(success, args)
        elif source_code_model_service_id == SourceCodeModelSubServiceId.TYPE_DEDUCTION:
            self.type['type_deduction'].set(success, args)
        elif source_code_model_service_id == SourceCodeModelSubServiceId.GO_TO_DEFINITION:
            self.type['go_to_definition'].set(success, args)
        elif source_code_model_service_id == SourceCodeModelSubServiceId.GO_TO_INCLUDE:
            self.type['go_to_include'].set(success, args)
        else:
            logging.error('Invalid source code model service id!')
        self.wait_on_completion.release()

    def reset(self):
        for key, callback_result in self.type.iteritems():
            callback_result.reset()

    def __getitem__(self, key):
        return self.type.get(key, None)

# TODO implement similar callback handling classes for the rest of services (clang-tidy, clang-format, project-builder)


