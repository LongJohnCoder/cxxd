import os
import tempfile

class FileGenerator():
    @staticmethod
    def gen_simple_cpp_file(edited=False):
        fd = tempfile.NamedTemporaryFile(suffix='.cpp', bufsize=0)
        if edited:
            fd.write('\
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
        else:
            fd.write('\
#include <vector>           \n\
                            \n\
int foobar() {              \n\
    return 0;               \n\
}                           \n\
                            \n\
int main() {                \n\
    std::vector<int> v;     \n\
    return foobar();        \n\
}                           \n\
                            \n\
int fun() {                 \n\
    return bar();           \n\
}                           \n\
            ')
        return fd

    @staticmethod
    def gen_broken_cpp_file(edited=False):
        fd = tempfile.NamedTemporaryFile(suffix='.cpp', bufsize=0)
        if edited:
            fd.write('\
#include <vector>           \n\
                            \n\
trigger compile error       \n\
                            \n\
int foobar() {              \n\
    return 0;               \n\
}                           \n\
                            \n\
int main() {                \n\
    std::vector<int> v;     \n\
    return foobar();        \n\
}                           \n\
                            \n\
int fun() {                 \n\
    return bar();           \n\
}                           \n\
            ')
        else:
            fd.write('\
#include <vector>           \n\
                            \n\
                            \n\
trigger compile error       \n\
                            \n\
int foobar() {              \n\
    return 0;               \n\
}                           \n\
                            \n\
int main() {                \n\
    std::vector<int> v;     \n\
    return foobar();        \n\
}                           \n\
                            \n\
int fun() {                 \n\
    return bar();           \n\
}                           \n\
            ')
        return fd

    @staticmethod
    def gen_txt_compilation_database():
        txt_compile_flags = [
            '-D_GLIBCXX_DEBUG',
            '-Wabi',
            '-Wconversion',
            '-Winline',
        ]
        fd = open('compile_flags.txt', 'w') # tempfile.NamedTemporaryFile(suffix='.txt', bufsize=0)
        fd.write('\n'.join(txt_compile_flags))
        return fd

    @staticmethod
    def gen_json_compilation_database():
        fd = open('compile_commands.json', 'w') #tempfile.NamedTemporaryFile(suffix='.json', bufsize=0)
        fd.write(('                  \
            {{                                            \n    \
                "directory": "/tmp",                      \n    \
                "command": "/usr/bin/c++ -o {0}.o -c {1}",\n    \
                "file": "{2}"                             \n    \
            }}                                                  \
        ').format(cls.file_to_perform_clang_tidy_on.name, cls.file_to_perform_clang_tidy_on.name, cls.file_to_perform_clang_tidy_on.name))
        return fd

    @staticmethod
    def gen_clang_format_config_file():
        fd = tempfile.NamedTemporaryFile(suffix='.clang-format', bufsize=0)
        fd.write('        \
            BasedOnStyle: LLVM                      \n\
            AccessModifierOffset: -4                \n\
            AlwaysBreakTemplateDeclarations: true   \n\
            ColumnLimit: 100                        \n\
            Cpp11BracedListStyle: true              \n\
            IndentWidth: 4                          \n\
            MaxEmptyLinesToKeep: 2                  \n\
            PointerBindsToType: true                \n\
            Standard: Cpp11                         \n\
            TabWidth: 4                             \n\
        ')
        return fd

    @staticmethod
    def close_gen_file(fd):
        os.remove(fd.name)
