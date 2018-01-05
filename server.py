import logging
from multiprocessing import Process, Queue
from services.clang_format_service import ClangFormat
from services.clang_tidy_service import ClangTidy
from services.project_builder_service import ProjectBuilder
from services.source_code_model_service import SourceCodeModel

class ServiceId():
    SOURCE_CODE_MODEL     = 0x0
    PROJECT_BUILDER       = 0x1
    CLANG_FORMAT          = 0x2
    CLANG_TIDY            = 0x3

class ServerRequestId():
    START_ALL_SERVICES    = 0xF0
    START_SERVICE         = 0xF1
    SEND_SERVICE          = 0xF2
    SHUTDOWN_ALL_SERVICES = 0xFD
    SHUTDOWN_SERVICE      = 0xFE
    SHUTDOWN_AND_EXIT     = 0xFF

class Server():
    class ServiceHandler():
        def __init__(self, service):
            self.service = service
            self.process = None

        def start_listening(self):
            from service import service_listener
            if self.is_started():
                logging.warning("Service process already started!")
            else:
                self.process = Process(target=service_listener, args=(self.service,), name=self.service.__class__.__name__)
                self.process.daemon = False
                self.process.start()

        def stop_listening(self):
            if self.is_started():
                self.process.join()
                self.process = None
            else:
                logging.warning("Service process already stopped!")

        def is_started(self):
            return self.process != None

        def startup_request(self, payload):
            if self.is_started():
                self.service.send_startup_request(payload)
            else:
                logging.warning("Service process must be started before issuing any kind of requests!")

        def shutdown_request(self, payload):
            if self.is_started():
                self.service.send_shutdown_request(payload)
            else:
                logging.warning("Service process must be started before issuing any kind of requests!")

        def request(self, payload):
            if self.is_started():
                self.service.send_request(payload)
            else:
                logging.warning("Service process must be started before issuing any kind of requests!")

    def __init__(self, handle, source_code_model_plugin, project_builder_plugin, clang_format_plugin, clang_tidy_plugin):
        self.handle = handle
        self.service = {
            ServiceId.SOURCE_CODE_MODEL : self.ServiceHandler(SourceCodeModel(source_code_model_plugin)),
            ServiceId.PROJECT_BUILDER   : self.ServiceHandler(ProjectBuilder(project_builder_plugin)),
            ServiceId.CLANG_FORMAT      : self.ServiceHandler(ClangFormat(clang_format_plugin)),
            ServiceId.CLANG_TIDY        : self.ServiceHandler(ClangTidy(clang_tidy_plugin)),
        }
        self.action = {
            ServerRequestId.START_ALL_SERVICES    : self.__start_all_services,
            ServerRequestId.START_SERVICE         : self.__start_service,
            ServerRequestId.SEND_SERVICE          : self.__send_service_request,
            ServerRequestId.SHUTDOWN_ALL_SERVICES : self.__shutdown_all_services,
            ServerRequestId.SHUTDOWN_SERVICE      : self.__shutdown_service,
            ServerRequestId.SHUTDOWN_AND_EXIT     : self.__shutdown_and_exit
            # TODO add runtime debugging switch action
        }
        self.started_up = True
        logging.info("Registered services: {0}".format(self.service))
        logging.info("Actions: {0}".format(self.action))

    def __start_all_services(self, dummyServiceId, dummyPayload):
        logging.info("Starting all registered services ... {0}".format(self.service))
        for serviceId, svc_handler in self.service.iteritems():
            svc_handler.start_listening()
            svc_handler.startup_request(dummyPayload)
            logging.info(
                "id={0}, service='{1}', payload={2}".format(serviceId, svc_handler.service.__class__.__name__, dummyPayload)
            )
        return self.started_up

    def __start_service(self, serviceId, payload):
        svc_handler = self.service.get(serviceId, None)
        if svc_handler is not None:
            logging.info(
                "id={0}, service='{1}', payload={2}".format(serviceId, svc_handler.service.__class__.__name__, payload)
            )
            svc_handler.start_listening()
            svc_handler.startup_request(payload)
        else:
            logging.error("Starting the service not possible. No service found under id={0}.".format(serviceId))
        return self.started_up

    def __shutdown_all_services(self, dummyServiceId, payload):
        logging.info("Shutting down all registered services ... {0}".format(self.service))
        for serviceId, svc_handler in self.service.iteritems():
            svc_handler.shutdown_request(payload)
            logging.info(
                "id={0}, service='{1}', payload={2}".format(serviceId, svc_handler.service.__class__.__name__, payload)
            )
        for svc_handler in self.service.itervalues():
            svc_handler.stop_listening()
        return self.started_up

    def __shutdown_service(self, serviceId, payload):
        svc_handler = self.service.get(serviceId, None)
        if svc_handler is not None:
            logging.info(
                "id={0}, service='{1}', payload={2}".format(serviceId, svc_handler.service.__class__.__name__, payload)
            )
            svc_handler.shutdown_request(payload)
            svc_handler.stop_listening()
        else:
            logging.error("Shutting down the service not possible. No service found under id={0}.".format(serviceId))
        return self.started_up

    def __shutdown_and_exit(self, dummyServiceId, payload):
        logging.info("Shutting down the server ...")
        self.__shutdown_all_services(dummyServiceId, payload)
        self.started_up = False
        return self.started_up

    def __send_service_request(self, serviceId, payload):
        svc_handler = self.service.get(serviceId, None)
        if svc_handler is not None:
            logging.info(
                "id={0}, service='{1}', Payload={2}".format(serviceId, svc_handler.service.__class__.__name__, payload)
            )
            svc_handler.request(payload)
        else:
            logging.error("Sending a request to the service not possible. No service found under id={0}.".format(serviceId))
        return self.started_up

    def __unknown_action(self, serviceId, payload):
        logging.error("Unknown action triggered! Valid actions are: {0}".format(self.action))
        return self.started_up

    def process_request(self):
        payload = self.handle.get()
        still_running = self.action.get(int(payload[0]), self.__unknown_action)(int(payload[1]), payload[2])
        return still_running

    def is_started_up(self):
        return self.started_up

def server_listener(server):
    keep_listening = True
    while keep_listening:
        keep_listening = server.process_request()
    logging.info("Server listener shut down ...")





def test__clang_indexer__run_on_directory():
    proj_root_dir = "/home/jbakamovic/development/projects/cppcheck"
    compiler_args = "-I./lib -I./externals/simplecpp -I./tinyxml"
    filename = "/home/jbakamovic/development/projects/cppcheck/lib/astutils.cpp"

    q = Queue()
    q.put([0xF1, 0, "dummy"])
    q.put([0xF2, 0, [0x0, 0x1, proj_root_dir, compiler_args]])   # run-on-directory
    server_run(q, 'GVIM')

def test__clang_indexer__find_all_references():
    proj_root_dir = "/home/jbakamovic/development/projects/cppcheck"
    compiler_args = "-I./lib -I./externals/simplecpp -I./tinyxml"
    filename = "/home/jbakamovic/development/projects/cppcheck/lib/astutils.cpp"
    line = 27
    col = 15

    q = Queue()
    q.put([0xF1, 0, "dummy"])
    q.put([0xF2, 0, [0x0, 0x1, proj_root_dir, compiler_args]])   # run-on-directory
    q.put([0xF2, 0, [0x0, 0x11, filename, line, col]])           # find-all-references
    server_run(q, 'GVIM')

def test__clang_syntax_highlighter():
    proj_root_dir = "/home/jbakamovic/development/projects/cppcheck"
    compiler_args = "-I./lib -I./externals/simplecpp -I./tinyxml"
    filename = "/home/jbakamovic/development/projects/cppcheck/lib/astutils.cpp"

    q = Queue()
    q.put([0xF1, 0, "dummy"])
    q.put([0xF2, 0, [0x1, proj_root_dir, filename, filename, compiler_args]]) # syntax-highlight
    server_run(q, 'GVIM')

def test__clang_diagnostics():
    proj_root_dir = "/home/jbakamovic/development/projects/cppcheck"
    compiler_args = "-I./lib -I./externals/simplecpp -I./tinyxml"
    filename = "/home/jbakamovic/development/projects/cppcheck/lib/astutils.cpp"

    q = Queue()
    q.put([0xF1, 0, "dummy"])
    q.put([0xF2, 0, [0x2, proj_root_dir, filename, filename, compiler_args]]) # diagnostics
    server_run(q, 'GVIM')

def test__clang_type_deduction():
    proj_root_dir = "/home/jbakamovic/development/projects/cppcheck"
    compiler_args = "-I./lib -I./externals/simplecpp -I./tinyxml"
    filename = "/home/jbakamovic/development/projects/cppcheck/lib/astutils.cpp"
    line = 27
    col = 15

    q = Queue()
    q.put([0xF1, 0, "dummy"])
    q.put([0xF2, 0, [0x3, proj_root_dir, filename, filename, compiler_args, line, col]]) # type-deduction
    server_run(q, 'GVIM')


def main():
    return test__clang_indexer__find_all_references()
    return test__clang_indexer__run_on_directory()
    return test__clang_type_deduction()
    return test__clang_diagnostics()
    return test__clang_syntax_highlighter()

if __name__ == "__main__":
    main()

