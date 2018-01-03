from glob import glob
from os.path import join

from .call import ApiCall


class DocumentFormatter:

    def __init__(self, output_directory):
        self.output_directory = output_directory
        self.locations = {}

    @property
    def output_format(self):
        raise NotImplementedError()

    def load(self, directory):
        for filename in glob(join(directory, '*.yml')):
            with open(filename) as f:
                self.load_file(f)
        print(self.locations)

    def load_file(self, f):
        call = ApiCall.load(f)
        verbs = self.locations.setdefault(call.url, {})
        calls = verbs.setdefault(call.verb, [])
        calls.append(call)

    def dump(self):
        for location, verbs in self.locations.items():
            for verb, calls in verbs.items():
                self.write_file(self.get_filename(location, verb), calls)

    def get_filename(self, location, verb):
        url = location.strip('/').replace('/', '-')
        return f'{url}-{verb}.{self.output_format}'.replace(' ', '-')

    def write_file(self, filename, calls):
        with open(filename) as file:
            raise NotImplementedError()


class MarkdownFormatter(DocumentFormatter):
    pass
