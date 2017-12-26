class Diagnostics():
    def __init__(self, parser):
        self.parser = parser

    def __call__(self, args):
        original_filename = str(args[0])
        contents_filename = str(args[1])

        diag_iter = self.parser.get_diagnostics(
            self.parser.parse(contents_filename, original_filename)
        )
        return diag_iter != None, diag_iter
