import unittest

import parser.ast_node_identifier
import parser.clang_parser
import parser.tunit_cache
from file_generator import FileGenerator

class SemanticSyntaxHighlightTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_file                    = FileGenerator.gen_simple_cpp_file()
        cls.test_file_with_includes_only = FileGenerator.gen_header_file_containing_includes_only()
        cls.txt_compilation_database     = FileGenerator.gen_txt_compilation_database()

        cls.parser = parser.clang_parser.ClangParser(
            cls.txt_compilation_database.name,
            parser.tunit_cache.TranslationUnitCache(parser.tunit_cache.NoCache())
        )

    @classmethod
    def tearDownClass(cls):
        FileGenerator.close_gen_file(cls.test_file)
        FileGenerator.close_gen_file(cls.test_file_with_includes_only)
        FileGenerator.close_gen_file(cls.txt_compilation_database)

    def setUp(self):
        import cxxd_mocks
        from services.source_code_model.semantic_syntax_highlight.semantic_syntax_highlight import SemanticSyntaxHighlight
        self.service = SemanticSyntaxHighlight(self.parser)

    def test_if_call_returns_true_and_ast_tree_traversal_callback_does_not_take_place_for_unsupported_ast_nodes(self):
        success, [tunit, ast_traversal_fun] = self.service([self.test_file.name, self.test_file.name])
        self.assertEqual(success, True)
        self.assertNotEqual(tunit, None)
        self.assertNotEqual(ast_traversal_fun, None)
        
        def ast_node_callback(id, name, line, column, data):
            self.assertNotEqual(id, parser.ast_node_identifier.ASTNodeId.getUnsupportedId())
        ast_traversal_fun(tunit, ast_node_callback, data=None)

    def test_if_call_returns_true_and_ast_tree_traversal_callback_does_not_take_place_for_symbols_from_included_files(self):
        success, [tunit, ast_traversal_fun] = self.service([self.test_file_with_includes_only.name, self.test_file_with_includes_only.name])
        self.assertEqual(success, True)
        self.assertNotEqual(tunit, None)
        self.assertNotEqual(ast_traversal_fun, None)

        nodes = []
        def ast_node_callback(id, name, line, column, data):
            data.append(id)
        ast_traversal_fun(tunit, ast_node_callback, data=nodes)
        self.assertEqual(len(nodes), 0)

if __name__ == '__main__':
    unittest.main()
