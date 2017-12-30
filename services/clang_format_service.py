import logging
import subprocess
import cxxd.service

class ClangFormat(cxxd.service.Service):
    def __init__(self, service_plugin):
        cxxd.service.Service.__init__(self, service_plugin)
        self.config_file = ""
        self.format_cmd = "clang-format -i -style=file -assume-filename="
        self.clang_format_success_code = 0

    def startup_callback(self, args):
        self.config_file = args[0]
        self.format_cmd += self.config_file
        logging.info("Config_file = {0}. Format_cmd = {1}".format(self.config_file, self.format_cmd))

    def shutdown_callback(self, args):
        pass

    def __call__(self, args):
        filename = args[0]
        cmd = self.format_cmd + " " + filename
        ret = subprocess.call(cmd, shell=True)
        logging.info("Filename = {0}. Cmd = {1}".format(filename, cmd))
        return ret == self.clang_format_success_code, None
