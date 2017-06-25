
import unittest
from os.path import dirname, abspath, join

from restfulpy.utils import import_python_module_by_filename, construct_class_by_name


HERE = abspath(dirname(__file__))
DATA_DIR = join(HERE, 'data')


class MyClassToConstructByName:
    def __init__(self, a):
        self.a = a


class UtilsTestCase(unittest.TestCase):

    def test_import_python_module_by_filename(self):
        filename = join(DATA_DIR, 'a.py')
        with open(filename, mode='w') as f:
            f.write('b = 123\n')

        module_ = import_python_module_by_filename('a', filename)
        self.assertEqual(module_.b, 123)

    def test_construct_class_by_name(self):
        obj = construct_class_by_name('restfulpy.tests.test_utils.MyClassToConstructByName', 1)
        self.assertEqual(obj.a, 1)
        self.assertIsNotNone(obj)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
