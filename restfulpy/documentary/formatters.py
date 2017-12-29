from glob import glob
from os.path import join

from .call import ApiCall


class DocumentFormatter:
    def __init__(self):
        self.locations = {}

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

    def dump(self, directory):
        raise NotImplementedError()


class MarkdownFormatter(DocumentFormatter):
    pass
