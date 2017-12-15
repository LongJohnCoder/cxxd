import logging
import sys

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

def __run_impl(get_server_instance, msg_queue, args, log_file):
    # Logger setup
    FORMAT = '[%(levelname)s] [%(filename)s:%(lineno)s] %(funcName)25s(): %(message)s'
    logging.basicConfig(filename=log_file, filemode='w', format=FORMAT, level=logging.INFO)
    logging.info('Starting a server ...')

    # Setup catching unhandled exceptions
    __catch_unhandled_exceptions()

    # Instantiate and run the server
    try:
        get_server_instance(msg_queue, args).listen()
    except:
        sys.excepthook(*sys.exc_info())

def run(get_server_instance, msg_queue, args, log_file):
    import multiprocessing
    server_process = multiprocessing.Process(
        target=__run_impl,
        args=(
            get_server_instance,
            msg_queue,
            args,
            log_file
        ),
        name="cxxd_server"
    )
    server_process.daemon = False
    server_process.start()
