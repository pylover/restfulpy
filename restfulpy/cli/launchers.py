class Launcher:
    no_launch = False
    parser = None

    @classmethod
    def create_parser(cls, subparsers):
        raise NotImplementedError

    @classmethod
    def register(cls, subparsers):
        parser = cls.create_parser(subparsers)
        instance = cls()
        instance.parser = parser
        if not cls.no_launch:
            parser.set_defaults(func=instance)
        return instance

    def __call__(self, *args):
        self.args = args[0] if len(args) else None
        self.launch()

    def launch(self):
        if self.parser:
            self.parser.print_help()


class RequireSubCommand:
    no_launch = True
