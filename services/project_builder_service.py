import logging
import subprocess
import tempfile
import time
import cxxd.service

class ProjectBuilder(cxxd.service.Service):
    def __init__(self, service_plugin):
        cxxd.service.Service.__init__(self, service_plugin)
        self.build_cmd_dir = ""
        self.build_cmd_output_file = ""

    def startup_callback(self, args):
        self.build_cmd_dir = args[0]
        self.build_cmd_output_file = tempfile.NamedTemporaryFile(prefix=args[1] + '_', delete=True)
        logging.info("Args = {0}, build_cmd_output_file = {1}.".format(args, self.build_cmd_output_file.name))

    def shutdown_callback(self, args):
        pass

    def __call__(self, arg):
        start = time.clock()
        build_cmd = arg[0]
        self.build_cmd_output_file.truncate()
        cmd = "cd " + self.build_cmd_dir + " && " + build_cmd
        ret = subprocess.call(cmd, shell=True, stdout=self.build_cmd_output_file, stderr=self.build_cmd_output_file)
        end = time.clock()
        logging.info("Cmd '{0}' took {1}".format(cmd, end-start))
        return ret, self.build_cmd_output_file.name
