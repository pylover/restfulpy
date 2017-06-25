
import io
import unittest
from os.path import dirname, abspath, join
from datetime import datetime, timezone, timedelta, time

from restfulpy.utils import import_python_module_by_filename, construct_class_by_name, format_iso_datetime, \
    format_iso_time, random_password, copy_stream, md5sum


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

    def test_format_iso_datetime(self):
        result = format_iso_datetime(datetime(2012, 2, 22, 12, 52, 29, 300, tzinfo=timezone(timedelta(minutes=30))))
        self.assertEqual(result, '2012-02-22T12:52:29+00:30')

        result = format_iso_datetime(datetime(2012, 2, 22, 12, 52, 29, 300, tzinfo=timezone(timedelta(minutes=0))))
        self.assertEqual(result, '2012-02-22T12:52:29Z')

    def test_format_iso_time(self):
        result = format_iso_time(time(12, 52, 29, 300, tzinfo=timezone(timedelta(minutes=30))))
        self.assertEqual(result, '12:52:29+00:30')

        result = format_iso_time(time(12, 52, 29, 300, tzinfo=timezone(timedelta(minutes=0))))
        self.assertEqual(result, '12:52:29Z')

    def test_random_password(self):
        result = random_password(5)
        self.assertEqual(len(result), 5)

    def test_copy_stream(self):
        content = b'This is the initial source file'
        source = io.BytesIO(content)
        target = io.BytesIO()
        copy_stream(source, target)
        target.seek(0)
        self.assertEqual(target.read(), content)

    def test_md5sum(self):
        content = b'This is the initial source file'
        source = io.BytesIO(content)
        filename = join(DATA_DIR, 'a.txt')
        with open(filename, mode='wb') as f:
            f.write(content)

        self.assertEqual(md5sum(source), md5sum(filename))


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
