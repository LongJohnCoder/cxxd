class ServiceMock():
    def send_startup_request(self, payload):
        pass

    def send_shutdown_request(self, payload):
        pass

    def send_request(self, payload):
        pass

class ServicePluginMock():
    def startup_callback(self, success, payload):
        pass

    def shutdown_callback(self, success, payload):
        pass

    def __call__(self, success, payload, args):
        pass
