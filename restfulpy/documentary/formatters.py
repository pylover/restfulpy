from glob import glob
from os.path import join

import yaml


class DocumentFormatter:

    def load(self, directory):
        for filename in glob(join(directory, '*.yml')):
            with open(filename) as f:
                self.load_file(f)

    def load_file(self, f):
        spec = yaml.load(f)
        print(spec)

    def dump(self, directory):
        raise NotImplementedError()


class MarkdownFormatter(DocumentFormatter):
    pass
