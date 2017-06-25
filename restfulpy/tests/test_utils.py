
import unittest
from os.path import dirname, abspath, join

from restfulpy.utils import import_python_module_by_filename


HERE = abspath(dirname(__file__))
DATA_DIR = join(HERE, 'data')


class UtilsTestCase(unittest.TestCase):

    def test_import_python_module_by_filename(self):
        filepath = join(DATA_DIR, 'a.py')
        with open(filepath, mode='w') as f:
            f.write('b = 123\n')

        module = import_python_module_by_filename('a', filepath)
        self.assertEqual(module.b, 123)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
