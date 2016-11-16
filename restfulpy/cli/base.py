
from restfulpy.configuration import configure
from restfulpy.orm import init_model, create_engine


class Launcher(object):
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
        if len(args):
            self.args = args[0]
        else:
            self.args = None
        self.launch()

    def launch(self):
        if self.parser:
            self.parser.print_help()


# noinspection PyAbstractClass
class ConfiguredLauncher(Launcher):

    def configure(self):
        configure(directories=self.args.config_dir)

    def __call__(self, *args):
        if len(args):
            self.args = args[0]
        else:
            self.args = None
        self.configure()
        self.launch()


# noinspection PyAbstractClass
class DatabaseLauncher(ConfiguredLauncher):

    def configure(self):
        super(DatabaseLauncher, self).configure()
        init_model(create_engine())


class RequireSubCommand(object):
    no_launch = True
