import logging
import os
import subprocess
import tempfile
import time
import cxxd.service

class ClangTidy(cxxd.service.Service):
    def __init__(self, service_plugin):
        cxxd.service.Service.__init__(self, service_plugin)
        self.config_file = ''
        self.compiler_options = ''
        self.cmd = 'clang-tidy'
        self.clang_tidy_success_code = 0

    def startup_callback(self, args):
        self.config_file = args[0]
        compilation_database = args[1]
        self.output_file = tempfile.NamedTemporaryFile(suffix='_clang_tidy_output', delete=True)
        root, ext = os.path.splitext(compilation_database)
        if ext == '.json':  # In case we have a JSON compilation database we simply use one
            self.compiler_options = '-p ' + compilation_database
            logging.info("clang-tidy will extract compiler flags from existing JSON database.")
        else:               # Otherwise we provide compilation flags inline
            with open(compilation_database) as f:
                self.compiler_options = '-- ' + f.read().replace('\n', ' ')
            logging.info("clang-tidy will use compiler flags given inline: '{0}'.".format(self.compiler_options))

    def shutdown_callback(self, args):
        pass

    def __call__(self, args):
        filename, apply_fixes = args
        cmd = self.cmd + ' ' + filename + ' ' + str('-fix' if apply_fixes else '') + ' ' + self.compiler_options
        logging.info("Triggering clang-tidy over '{0}' with '{1}'".format(filename, cmd))
        with open(self.output_file.name, 'w') as f:
            start = time.clock()
            ret = subprocess.call(cmd, shell=True, stdout=f)
            end = time.clock()
        logging.info("Clang-Tidy over '{0}' completed in {1}s.".format(filename, end-start))
        return ret == self.clang_tidy_success_code, self.output_file.name
