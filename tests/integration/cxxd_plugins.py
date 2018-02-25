class SourceCodeModelServicePluginMock():
    def __init__(self, callback_result):
        self.callback_result = callback_result

    def startup_callback(self, success, payload):
        pass

    def shutdown_callback(self, success, payload):
        pass

    def __call__(self, success, payload, args):
        self.callback_result.set(success, payload, args)

class ClangFormatServicePluginMock():
    def startup_callback(self, success, payload):
        pass

    def shutdown_callback(self, success, payload):
        pass

    def __call__(self, success, payload, args):
        # TODO store result
        pass

class ClangTidyServicePluginMock():
    def startup_callback(self, success, payload):
        pass

    def shutdown_callback(self, success, payload):
        pass

    def __call__(self, success, payload, args):
        # TODO store result
        pass

class ProjectBuilderServicePluginMock():
    def startup_callback(self, success, payload):
        pass

    def shutdown_callback(self, success, payload):
        pass

    def __call__(self, success, payload, args):
        # TODO store result
        pass

