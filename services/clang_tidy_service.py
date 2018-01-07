import distutils.spawn
import logging
import os
import subprocess
import tempfile
import time
import cxxd.service

class ClangTidy(cxxd.service.Service):
    def __init__(self, service_plugin):
        cxxd.service.Service.__init__(self, service_plugin)
        self.clang_tidy_compile_flags = None
        self.clang_tidy_binary = distutils.spawn.find_executable('clang-tidy')
        self.clang_tidy_success_code = 0
        self.clang_tidy_output = None

    def startup_callback(self, args):
        if self.clang_tidy_binary:
            compilation_database = args[0]
            if os.path.isfile(compilation_database):
                self.clang_tidy_output = tempfile.NamedTemporaryFile(suffix='_clang_tidy_output')
                root, ext = os.path.splitext(compilation_database)
                if ext == '.json':
                    self.clang_tidy_compile_flags = '-p ' + compilation_database            # In case we have a JSON compilation database we simply use one
                    logging.info('clang-tidy will extract compiler flags from existing JSON database.')
                elif ext == '.txt':
                    with open(compilation_database) as f:
                        self.clang_tidy_compile_flags = '-- ' + f.read().replace('\n', ' ') # Otherwise we provide compilation flags inline
                    logging.info('clang-tidy will use compiler flags given inline: \'{0}\'.'.format(self.clang_tidy_compile_flags))
                else:
                    logging.error('clang-tidy requires compiler flags to be provided either inline or via JSON compilation database.')
            else:
                logging.error('Provided compilation database, \'{0}\', does not exist. Please check if correct path is given.'.format(compilation_database))
        else:
            logging.error('clang-tidy executable not found on your system path!')

    def shutdown_callback(self, args):
        pass

    def __call__(self, args):
        filename, apply_fixes = args
        if self.clang_tidy_binary and self.clang_tidy_compile_flags and os.path.isfile(filename):
            clang_tidy_binary = self.clang_tidy_binary + ' ' + filename + ' ' + str('-fix' if apply_fixes else '') + ' ' + self.clang_tidy_compile_flags
            logging.info("Triggering clang-tidy over '{0}' with '{1}'".format(filename, clang_tidy_binary))
            with open(self.clang_tidy_output.name, 'w') as f:
                start = time.clock()
                ret = subprocess.call(clang_tidy_binary, shell=True, stdout=f)
                end = time.clock()
            logging.info("clang-tidy over '{0}' completed in {1}s.".format(filename, end-start))
            return ret == self.clang_tidy_success_code, self.clang_tidy_output.name
        return False, None
