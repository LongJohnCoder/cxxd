class GoToInclude():
    def __init__(self, parser):
        self.parser = parser

    def __call__(self, args):
        include_filename = None
        original_filename, contents_filename, line = args
        tunit = self.parser.parse(contents_filename, original_filename)
        for include in self.parser.get_top_level_includes(tunit):
            filename, l, col = include
            if l == line:
                include_filename = filename
                break
        return (tunit != None and include_filename != None), include_filename
