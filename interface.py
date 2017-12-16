import logging
import sys

def start_server(get_server_instance, get_server_instance_args, log_file):
    import multiprocessing
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

def stop_server(handle, subscribe_for_callback):
    handle.put([0xFF, 0x0, subscribe_for_callback])

def start_all_services(handle, payload):
    handle.put([0xF0, 0x0, 0x0])

def stop_all_services(handle, subscribe_for_callback):
    handle.put([0xFD, 0x0, subscribe_for_callback])

def start_service(handle, id, payload):
    handle.put([0xF1, id, payload])

def stop_service(handle, id, subscribe_for_callback):
    handle.put([0xFE, id, subscribe_for_callback])

def request_service(handle, id, payload):
    handle.put([0xF2, id, payload])


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

def __run_impl(handle, get_server_instance, args, log_file):
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

